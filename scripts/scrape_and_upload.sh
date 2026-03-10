#!/usr/bin/env bash
# Scrape toutes les sources et upload sur GCP

set -eo pipefail

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

BUCKET="gs://bscd-database/sources"
OUTPUT_DIR="/tmp/bcsd_scrape"

echo "Pipeline pour scraper + upload GCP"
echo "Bucket : $BUCKET"
echo ""

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# RosettaCode

echo "RosettaCode"
python3 src/scrapers/rosetta_scraper.py -o "$OUTPUT_DIR" -v

echo "Upload rosetta_code"
gsutil -m cp -r "$OUTPUT_DIR/rosetta_code" "$BUCKET/"
[ -f "$OUTPUT_DIR/rosetta_code_metadata.json" ] && gsutil cp "$OUTPUT_DIR/rosetta_code_metadata.json" "$BUCKET/"
echo "OK"


# LeetCode
echo "LeetCode"
python3 src/scrapers/leetcode_scraper.py -o "$OUTPUT_DIR" -v

echo "Upload leetcode"
gsutil -m cp -r "$OUTPUT_DIR/leetcode" "$BUCKET/"
[ -f "$OUTPUT_DIR/leetcode_metadata.json" ] && gsutil cp "$OUTPUT_DIR/leetcode_metadata.json" "$BUCKET/"
echo "OK"

# AtCoder

if [ -f ".env" ] || [ -n "$REVEL_SESSION" ]; then

    echo "AtCoder"
    python3 src/scrapers/atcoder_scraper.py -o "$OUTPUT_DIR"

    echo "Upload atcoder"
    gsutil -m cp -r "$OUTPUT_DIR/atcoder" "$BUCKET/"
    [ -f "$OUTPUT_DIR/atcoder_metadata.json" ] && gsutil cp "$OUTPUT_DIR/atcoder_metadata.json" "$BUCKET/"
    echo "OK"
else
    echo ""
    echo "AtCoder ignore car pas de REVEL_SESSION dans le env"
fi


# nettoyage
echo ""
rm -rf "$OUTPUT_DIR"
echo "Scraping et upload terminé"
