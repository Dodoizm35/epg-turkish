# Custom EPG (TR)

This folder contains a custom Digiturk-based channel list and a ready-to-run setup for generating/serving XMLTV for apps like **TiviMate** and **IPTVX**.

## 1) Generate the full Digiturk channel list

This will generate `custom/tr.channels.xml` from `sites/digiturk.com.tr/digiturk.com.tr.channels.xml`.

```sh
cd epg
node ./custom/generate-digiturk-channels.mjs
```

Notes:
- We prefix display names with `TR: ` to better match playlist naming conventions.
- If a channel has no `xmltv_id` in the upstream file, we assign a stable id like `digiturk_<site_id>`.

## 2) Generate XMLTV (manual)

```sh
cd epg
npm run grab --- --channels=./custom/tr.channels.xml --output=./custom/guide.xml --days=2 --maxConnections=10 --timeout=30000
```

You can then serve it locally:

```sh
cd epg
npx serve -l 3000 custom
```

## 3) Automatic refresh every 12 hours (recommended): Docker Compose

From `epg/custom/`:

```sh
# one-time: generate tr.channels.xml
cd ..
node ./custom/generate-digiturk-channels.mjs

# start the scheduled EPG service
cd custom
docker compose up -d
```

The container will:
- refresh the guide at **00:00** and **12:00**, and
- serve it at:
  - `http://<server-ip>:3001/guide.xml`

If `GZIP=true` is enabled, it will also produce `guide.xml.gz` in `custom/public/`.
