#!/bin/bash
# lance la compilation en parallele sur N coeurs via xargs
NPAR=${1:-$(nproc)}
echo "Compilation parallele sur $NPAR coeurs..."
xargs -d '\n' -P $NPAR -I {} bash -c '{}' < /workspace/compile_cmds.txt > /workspace/compile.log 2>&1
NB=$(find /workspace/data/binaries -type f -executable 2>/dev/null | wc -l | tr -d ' ')
NO=$(grep -c '^OK ' /workspace/compile.log 2>/dev/null | tr -d ' ')
NF=$(grep -c '^FAIL ' /workspace/compile.log 2>/dev/null | tr -d ' ')
echo "Termine: ${NB} executables, ${NO:-0} ok, ${NF:-0} echecs"
touch /workspace/compile.done
