#!/bin/bash
# lance le desassemblage en parallele : split les jobs en chunks, un worker par chunk
NPAR=${1:-$(nproc)}
TOTAL=$(wc -l < /workspace/disasm_jobs.txt | tr -d ' ')
echo "Desassemblage: $TOTAL jobs sur $NPAR workers..."

if [ "$TOTAL" -eq 0 ]; then
    echo "Rien a desassembler"
    touch /workspace/disasm.done
    exit 0
fi

mkdir -p /workspace/logs
cd /workspace

if [ "$TOTAL" -lt "$NPAR" ]; then
    NPAR=$TOTAL
fi

# on split le fichier de jobs en chunks et on lance un worker par chunk
split -n l/$NPAR disasm_jobs.txt disasm_chunk_
for f in disasm_chunk_*; do
    python3 /workspace/disasm.py --mode batch --jobs-file "$f" --config /workspace/config.yaml > "/workspace/logs/$(basename $f).log" 2>&1 &
done
wait

NB=$(find /workspace/data/disasm -name '*.json' 2>/dev/null | wc -l | tr -d ' ')
echo "Termine: $NB JSON produits"
touch /workspace/disasm.done
