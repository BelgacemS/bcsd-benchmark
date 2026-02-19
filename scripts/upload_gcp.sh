#!/usr/bin/env bash

# rendre compatible avec les autres scrappers apres 

set -e 

BUCKET="gs://bscd-database/dataset_raw"
TMP_DIR="/tmp/bcsd_rosetta_full"

echo "Démarrage du pipeline d'upload vers GCP"

rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"


echo "Lancement du scraping"

python3 src/scrapers/rosetta_scraper.py -o "$TMP_DIR"


echo "Envoi des données vers $BUCKET"
gsutil -m cp -r "$TMP_DIR/rosetta_code" "$BUCKET/"

# Envoi du fichier de métadonnées à la racine de dataset_raw parce que sinon c'est dans le dossier rosetta_code long a le retrouver dans GCP
gsutil cp "$TMP_DIR/rosetta_metadata.json" "$BUCKET/"

echo "Nettoyage des fichiers temporaires locaux"
rm -rf "$TMP_DIR"

echo "Terminé. Toute la base est uploadée sur GCP."