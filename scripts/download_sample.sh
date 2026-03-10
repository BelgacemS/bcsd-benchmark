#!/usr/bin/env bash

# avant faire chmod +x scripts/download_sample.sh

# Script qui permet de download un sample depuis GCP (bscd-database)
# Usage : ./scripts/download_sample.sh <SOURCE> [N_TASKS]

set -eo pipefail # Arrete le script a la moindre erreur

BUCKET="gs://bscd-database/sources"
SOURCE="${1:-}"
N_TASKS="${2:-20}"
DEST_DIR="data/sample"


if [[ -z "$SOURCE" ]]; then 

  echo "Erreur: SOURCE manquant"
  echo ""
  echo "Usage: $0 <SOURCE> [N_TASKS]"
  echo ""
  echo "Sources disponibles:"
  echo "  - leetcode"
  echo "  - rosetta_code"
  echo "  - atcoder"
  echo "  - all (les 3 sources)"

  exit 1

fi


if ! command -v gsutil &> /dev/null; then 

  echo "Erreur : gsutil non trouvé. Il faut d'abord installer Google Cloud SDK : (https://cloud.google.com/sdk/docs/install)"
  exit 1

fi

# La fonction pour sampler une source
sample_source() {
  local SRC=$1
  local DEST="$DEST_DIR/$SRC"
  mkdir -p "$DEST"


  echo "Sampling $N_TASKS tasks depuis $BUCKET/$SRC/"
  
  TASKS=$(gsutil ls "$BUCKET/$SRC/" 2>/dev/null | head -n "$N_TASKS" || true)
  
  # Telecharge toutes les tasks (sans multiprocessing pour eviter le bug macOS)

  gsutil -o "GSUtil:parallel_process_count=1" -m cp -r $TASKS "$DEST/"

  # Telecharge le metadata de la source
  gsutil cp "$BUCKET/${SRC}_metadata.json" "$DEST_DIR/" 2>/dev/null || true

  echo "$SRC : $N_TASKS tasks dans $DEST"
}

# Toutes les sources  
if [[ "$SOURCE" == "all" ]]; then
  for SRC in leetcode rosetta_code atcoder; do

    sample_source "$SRC"
  done

else

  if [[ ! "$SOURCE" =~ ^(leetcode|rosetta_code|atcoder)$ ]]; then
    echo "Erreur: SOURCE invalide '$SOURCE'"
    exit 1
  fi
  
  sample_source "$SOURCE"
fi

echo "Sample disponible dans : $DEST_DIR/"