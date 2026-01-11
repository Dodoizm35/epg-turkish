#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")/.."

# Regenerate the full channel list (Digiturk & TV+)
node ./custom/generate-digiturk-channels.mjs

# Regenerate guide.xml (+ guide.xml.gz)
npm run grab --- \
  --channels=./custom/tr.channels.xml \
  --output=./custom/public/guide.xml \
  --days=2 \
  --maxConnections=10 \
  --timeout=30000 \
  --gzip
