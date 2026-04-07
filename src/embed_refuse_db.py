#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import List, Sequence, Tuple


def _import_numpy():
    try:
        import numpy as np
    except ImportError as e:
        raise RuntimeError(
            "numpy is required for embed_refuse_db.py. Install dependencies from requirements.txt"
        ) from e
    return np


def _import_refuse_modules(repo_root: Path):
    refuse_eval_dir = repo_root / "model-evaluation" / "refuse"
    if not refuse_eval_dir.exists():
        raise FileNotFoundError(
            f"Could not find REFuSe eval directory at: {refuse_eval_dir}"
        )

    sys.path.insert(0, str(refuse_eval_dir))

    import jax
    from jax import numpy as jnp
    import optax
    from flax.training.train_state import TrainState
    from flax.training import checkpoints
    from utils.net_modules import REFUSE

    return jax, jnp, optax, TrainState, checkpoints, REFUSE


def _load_refuse_state(
    repo_root: Path,
    checkpoint_file: Path,
    trim_length: int,
    embedding_dim: int,
):
    jax, jnp, optax, TrainState, checkpoints, REFUSE = _import_refuse_modules(repo_root)

    net = REFUSE(
        channels=embedding_dim,
        window_size=8,
        stride=8,
        embd_size=8,
        log_stride=None,
    )

    init_rngs = {"params": jax.random.PRNGKey(0)}
    init_x = jnp.zeros((1, trim_length), dtype=jnp.int16)
    init_params = net.init(init_rngs, init_x)

    optimizer = optax.chain(optax.clip(max_delta=1.0), optax.adam(learning_rate=0.005))
    state = TrainState.create(apply_fn=net.apply, params=init_params, tx=optimizer)

    state = checkpoints.restore_checkpoint(
        ckpt_dir=str(checkpoint_file.parent),
        target=state,
        prefix=checkpoint_file.name,
        step=None,
    )

    return net, state, jnp


def _init_embeddings_table(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS embeddings (
            function_id INTEGER PRIMARY KEY,
            embedding BLOB NOT NULL,
            embedding_dim INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            checkpoint_path TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(function_id) REFERENCES functions(id)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model_name)")
    conn.commit()


def _fetch_batch(conn: sqlite3.Connection, batch_size: int) -> List[Tuple[int, bytes]]:
    rows = conn.execute(
        """
        SELECT f.id, f.raw_bytes
        FROM functions f
        LEFT JOIN embeddings e ON e.function_id = f.id
        WHERE e.function_id IS NULL
        ORDER BY f.id
        LIMIT ?
        """,
        (batch_size,),
    ).fetchall()
    return [(int(r[0]), bytes(r[1])) for r in rows]


def _prepare_batch(raw_batch: Sequence[bytes], trim_length: int) -> np.ndarray:
    np = _import_numpy()
    out = np.full((len(raw_batch), trim_length), 256, dtype=np.int16)
    for i, raw in enumerate(raw_batch):
        arr = np.frombuffer(raw, dtype=np.uint8).astype(np.int16)
        if arr.size == 0:
            continue
        n = min(arr.size, trim_length)
        out[i, :n] = arr[:n]
    return out


def _store_embeddings(
    conn: sqlite3.Connection,
    function_ids: Sequence[int],
    embeddings: np.ndarray,
    model_name: str,
    checkpoint_path: str,
) -> None:
    np = _import_numpy()
    payload = []
    for fn_id, vec in zip(function_ids, embeddings):
        vec32 = vec.astype(np.float32, copy=False)
        payload.append(
            (
                int(fn_id),
                sqlite3.Binary(vec32.tobytes()),
                int(vec32.shape[0]),
                model_name,
                checkpoint_path,
            )
        )

    conn.executemany(
        """
        INSERT OR REPLACE INTO embeddings(
            function_id, embedding, embedding_dim, model_name, checkpoint_path
        ) VALUES (?, ?, ?, ?, ?)
        """,
        payload,
    )
    conn.commit()


def export_embeddings_matrix(conn: sqlite3.Connection, out_npy: Path) -> None:
    np = _import_numpy()
    rows = conn.execute(
        """
        SELECT function_id, embedding, embedding_dim
        FROM embeddings
        ORDER BY function_id
        """
    ).fetchall()
    if not rows:
        print("[embed_refuse_db] no embeddings to export")
        return

    fn_ids = np.array([int(r[0]) for r in rows], dtype=np.int64)
    vectors = []
    for _, blob, dim in rows:
        vectors.append(np.frombuffer(blob, dtype=np.float32, count=int(dim)))

    matrix = np.stack(vectors, axis=0).astype(np.float32)
    out_npy.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_npy, matrix)
    np.save(out_npy.with_suffix(".ids.npy"), fn_ids)
    print(f"[embed_refuse_db] exported matrix: {out_npy}")
    print(f"[embed_refuse_db] exported ids: {out_npy.with_suffix('.ids.npy')}")


def generate_embeddings(
    db_path: Path,
    repo_root: Path,
    checkpoint_file: Path,
    batch_size: int,
    trim_length: int,
    embedding_dim: int,
    export_npy_path: Path,
) -> None:
    np = _import_numpy()
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    if not checkpoint_file.exists():
        raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_file}")

    net, state, jnp = _load_refuse_state(
        repo_root=repo_root,
        checkpoint_file=checkpoint_file,
        trim_length=trim_length,
        embedding_dim=embedding_dim,
    )

    conn = sqlite3.connect(str(db_path))
    _init_embeddings_table(conn)

    total_functions = conn.execute("SELECT COUNT(*) FROM functions").fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    print(f"[embed_refuse_db] functions total: {total_functions}")
    print(f"[embed_refuse_db] already embedded: {done}")

    model_name = "REFuSe"
    ckpt = str(checkpoint_file.resolve())
    processed = 0

    while True:
        batch = _fetch_batch(conn, batch_size)
        if not batch:
            break

        function_ids = [item[0] for item in batch]
        raw_bytes = [item[1] for item in batch]
        model_in = _prepare_batch(raw_bytes, trim_length)

        emb = net.apply(state.params, jnp.array(model_in))
        emb_np = np.array(emb, dtype=np.float32)

        _store_embeddings(conn, function_ids, emb_np, model_name, ckpt)
        processed += len(function_ids)

        now_done = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        print(f"[embed_refuse_db] embedded batch={len(function_ids)} total_done={now_done}")

    print(f"[embed_refuse_db] finished. newly processed: {processed}")

    if export_npy_path:
        export_embeddings_matrix(conn, export_npy_path)

    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate REFuSe embeddings from refuse_benchmark.db")
    parser.add_argument("--db-path", default="refuse_benchmark.db", help="Path to SQLite DB")
    parser.add_argument(
        "--refuse-repo-root",
        default=".cache/refuse_repo",
        help="Path to official Reverse-Engineering-Function-Search repo",
    )
    parser.add_argument(
        "--checkpoint-file",
        default=".cache/refuse_repo/model-training/checkpoints/refuse_checkpoint_1/checkpoint",
        help="Path to official REFuSe checkpoint file",
    )
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--trim-length", type=int, default=250)
    parser.add_argument("--embedding-dim", type=int, default=128)
    parser.add_argument(
        "--export-npy",
        default="",
        help="Optional output .npy path for aligned embedding matrix (writes IDs to <path>.ids.npy)",
    )
    args = parser.parse_args()

    generate_embeddings(
        db_path=Path(args.db_path),
        repo_root=Path(args.refuse_repo_root),
        checkpoint_file=Path(args.checkpoint_file),
        batch_size=args.batch_size,
        trim_length=args.trim_length,
        embedding_dim=args.embedding_dim,
        export_npy_path=Path(args.export_npy) if args.export_npy else None,
    )


if __name__ == "__main__":
    main()
