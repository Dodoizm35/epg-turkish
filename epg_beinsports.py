#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import json
from datetime import datetime, timedelta

OUTPUT = "beinsports_tr.xml"
TZ = "+0300"

CHANNEL_MAP = {
    1: ("bein.sports.1.tr", "beIN Sports 1"),
    2: ("bein.sports.2.tr", "beIN Sports 2"),
    3: ("bein.sports.3.tr", "beIN Sports 3"),
    4: ("bein.sports.4.tr", "beIN Sports 4"),
    13: ("bein.sports.haber.tr", "beIN Sports Haber"),
}

CHANNEL_URLS = {
    1: "https://beinsports.com.tr/yayin-akisi/beinsports-1",
    2: "https://beinsports.com.tr/yayin-akisi/beinsports-2",
    3: "https://beinsports.com.tr/yayin-akisi/beinsports-3",
    4: "https://beinsports.com.tr/yayin-akisi/beinsports-4",
    13: "https://beinsports.com.tr/yayin-akisi/beinsports-haber",
}

headers = {
    "User-Agent": "Mozilla/5.0",
}

all_guides = []

for _, url in CHANNEL_URLS.items():
    html = requests.get(url, headers=headers, timeout=15).text

    match = re.search(
        r'"listTvGuides"\s*:\s*(\[[^\]]+\])',
        html,
        re.DOTALL
    )

    if not match:
        continue

    guides = json.loads(match.group(1))
    all_guides.extend(guides)

if not all_guides:
    raise SystemExit("listTvGuides bulunamadi. Sayfa yapisi degismis.")

def xml_time(dt):
    return dt.strftime("%Y%m%d%H%M%S") + f" {TZ}"

xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv>']

# channel definitions
for _, (cid, name) in CHANNEL_MAP.items():
    xml.append(f'<channel id="{cid}"><display-name>{name}</display-name></channel>')

by_channel = {}

for g in all_guides:
    ch = g.get("channel_id")
    if ch not in CHANNEL_MAP:
        continue

    time_str = g.get("event_time")
    title = g.get("name")
    date_str = g.get("event_date")  # 1/2/2026 12:00:00 AM

    if not time_str or not title or not date_str:
        continue

    # GERÇEK YAYIN GÜNÜ
    event_date = datetime.strptime(
        date_str.split(" ")[0], "%m/%d/%Y"
    )

    h, m, s = time_str.split(":")
    start_dt = event_date.replace(
        hour=int(h), minute=int(m), second=int(s)
    )

    by_channel.setdefault(ch, []).append({
        "start": start_dt,
        "title": title
    })

for ch, items in by_channel.items():
    items.sort(key=lambda x: x["start"])
    xml_ch = CHANNEL_MAP[ch][0]

    for i, item in enumerate(items):
        start = item["start"]

        if i + 1 < len(items):
            # KRİTİK DÜZELTME: 1 DAKİKA BUFFER
            stop = items[i + 1]["start"] - timedelta(minutes=1)
        else:
            # Son program için güvenli varsayım
            stop = start + timedelta(hours=2)

        xml.append(
            f'<programme start="{xml_time(start)}" stop="{xml_time(stop)}" channel="{xml_ch}">'
            f'<title>{item["title"]}</title>'
            f'</programme>'
        )

xml.append("</tv>")

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(xml))

print(f"OK → {OUTPUT} olusturuldu ({len(all_guides)} program)")
