"""Genere les metadata pour data/sample"""

import json
from pathlib import Path
from datetime import datetime


def generate_sample_metadata(sample_dir="data/sample"):
    """Parcourt les sources et ecrit les metadata"""

    base = Path(sample_dir)
    if not base.exists():
        return

    for src_dir in sorted(base.iterdir()):
        if not src_dir.is_dir():
            continue

        tasks = [d for d in src_dir.iterdir() if d.is_dir()]
        if not tasks:
            continue

        impl_counts = {"C": 0, "Cpp": 0, "Rust": 0, "Go": 0}
        
        for task_dir in tasks:
            for lang in impl_counts:
                lang_dir = task_dir / lang
                if lang_dir.is_dir():
                    impl_counts[lang] += sum(1 for f in lang_dir.iterdir() if f.is_file())

        metadata = {
            "source": src_dir.name,
            "scrape_date": datetime.now().isoformat(),
            "total_tasks": len(tasks),
            "implementations": impl_counts,
            "structure": f"<output_dir>/{src_dir.name}/<task>/<C|Cpp|Rust|Go>/impl_XX.<ext>"
        }

        out_path = base / f"{src_dir.name}_metadata.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"Fichier genere : {out_path}")


if __name__ == "__main__":
    generate_sample_metadata()