#!/usr/bin/env bash

# avant faire chmod +x scripts/download_sample.sh

# Script qui permet de download un sample depuis GCP (bscd-database)
# Usage : ./scripts/download_sample.sh <SOURCE> [N_TASKS]

set -e # Permeet d'arreter le script à la moindre erreur et eviter des effets de bord inattendus

BUCKET="gs://bscd-database/dataset_raw"
SOURCE="${1:-}"
N_TASKS="${2:-20}"
DEST_DIR="data/sample"


if [[ -z "$SOURCE" ]]; then # -z pour zero length

  echo "Erreur: SOURCE manquant"
  echo ""
  echo "Usage: $0 <SOURCE> [N_TASKS]"
  echo ""
  echo "Sources disponibles:"
  echo "  - leetcode"
  echo "  - rosetta_code"
  echo "  - the_algorithms"
  echo "  - AtCoder"
  echo "  - all (les 4 sources)"

  exit 1

fi


if ! command -v gsutil &> /dev/null; then 

  echo "Erreur: gsutil non trouvé. Il faut d'abord installer Google Cloud SDK : (https://cloud.google.com/sdk/docs/install)"
  exit 1

fi

# La fonction pour sampler une source
sample_source() {
  local SRC=$1
  local DEST="$DEST_DIR/$SRC"
  mkdir -p "$DEST"

  echo ""
  echo "Sampling $N_TASKS tasks depuis $BUCKET/$SRC/"
  
  TASKS=$(gsutil ls "$BUCKET/$SRC/" | head -n "$N_TASKS") 
  
  for TASK in $TASKS; do
    echo "Téléchargement de $TASK"
    gsutil -m cp -r "$TASK" "$DEST/" # parfois ca peut bugger sur MacOS le multithreading remplacer alors par: gsutil -o "GSUtil:parallel_process_count=1" -m cp -r "$TASK" "$DEST/"
  done
  
  echo "$SRC : $N_TASKS tasks dans $DEST"
}

# Toutes les sources  
if [[ "$SOURCE" == "all" ]]; then
  for SRC in leetcode rosetta_code the_algorithms AtCoder; do

    sample_source "$SRC"
  done

else

  if [[ ! "$SOURCE" =~ ^(leetcode|rosetta_code|the_algorithms|AtCoder)$ ]]; then
    echo "Erreur: SOURCE invalide '$SOURCE'"
    exit 1
  fi
  
  sample_source "$SOURCE"
fi

echo ""
echo "Sample disponible dans : $DEST_DIR/"