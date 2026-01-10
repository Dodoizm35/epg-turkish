#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""beIN Sports Turkey EPG Scraper"""

import requests
import re
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

import config

logger = logging.getLogger(__name__)


def fetch_channel(channel_id: int, url: str) -> List[Dict[str, Any]]:
    """Fetch EPG data for a single beIN Sports channel"""
    headers = {
        "User-Agent": config.USER_AGENT,
    }

    try:
        response = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        html = response.text

        match = re.search(
            r'"listTvGuides"\s*:\s*(\[[^\]]+\])',
            html,
            re.DOTALL
        )

        if not match:
            logger.warning(f"beIN Sports: listTvGuides not found for channel {channel_id}")
            return []

        guides = json.loads(match.group(1))
        logger.info(f"beIN Sports: Fetched {len(guides)} programmes for channel {channel_id}")
        return guides

    except requests.RequestException as e:
        logger.error(f"beIN Sports request error for channel {channel_id}: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"beIN Sports JSON parse error for channel {channel_id}: {e}")
        return []


def fetch_all() -> Dict[str, Any]:
    """
    Fetch EPG data for all beIN Sports channels

    Returns:
        {
            "channels": [{"id": "...", "name": "...", "logo": "..."}],
            "programmes": [{"channel": "...", "start": datetime, "stop": datetime, "title": "..."}]
        }
    """
    channels = []
    programmes_by_channel = {}

    # Add channel definitions
    for ch_id, (xml_id, name, logo) in config.BEINSPORTS_CHANNELS.items():
        channels.append({
            "id": xml_id,
            "name": name,
            "logo": logo,
        })
        programmes_by_channel[ch_id] = []

    # Fetch programmes for each channel
    for ch_id, url in config.BEINSPORTS_URLS.items():
        guides = fetch_channel(ch_id, url)

        for g in guides:
            ch = g.get("channel_id")
            if ch not in config.BEINSPORTS_CHANNELS:
                continue

            time_str = g.get("event_time")
            title = g.get("name")
            date_str = g.get("event_date")  # Format: 1/2/2026 12:00:00 AM

            if not time_str or not title or not date_str:
                continue

            try:
                # Parse event date
                event_date = datetime.strptime(date_str.split(" ")[0], "%m/%d/%Y")

                # Parse event time
                h, m, s = time_str.split(":")
                start_dt = event_date.replace(
                    hour=int(h), minute=int(m), second=int(s)
                )

                programmes_by_channel[ch].append({
                    "start": start_dt,
                    "title": title,
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"beIN Sports: Could not parse time: {e}")
                continue

    # Convert to final format with stop times
    all_programmes = []

    for ch_id, items in programmes_by_channel.items():
        if not items:
            continue

        xml_id = config.BEINSPORTS_CHANNELS[ch_id][0]
        items.sort(key=lambda x: x["start"])

        for i, item in enumerate(items):
            start = item["start"]

            if i + 1 < len(items):
                # End 1 minute before next programme
                stop = items[i + 1]["start"] - timedelta(minutes=1)
            else:
                # Default 2 hours for last programme
                stop = start + timedelta(hours=2)

            all_programmes.append({
                "channel": xml_id,
                "start": start,
                "stop": stop,
                "title": item["title"],
                "desc": "",
                "category": "Sports",
                "tz": config.TZ_TURKEY,  # beIN Sports returns Turkey time
            })

    logger.info(f"beIN Sports: Total {len(channels)} channels, {len(all_programmes)} programmes")

    return {
        "channels": channels,
        "programmes": all_programmes,
    }
