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


def fetch_channel(channel_id: int, url: str, retry_count: int = 3) -> List[Dict[str, Any]]:
    """Fetch EPG data for a single beIN Sports channel with retry logic"""
    headers = {
        "User-Agent": config.USER_AGENT,
    }

    for attempt in range(retry_count):
        try:
            logger.debug(f"beIN Sports: Fetching channel {channel_id} (attempt {attempt + 1}/{retry_count})")
            response = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            html = response.text
            
            if not html or len(html) < 100:
                logger.warning(f"beIN Sports: Empty or too short response for channel {channel_id}")
                if attempt < retry_count - 1:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                return []

            match = re.search(
                r'"listTvGuides"\s*:\s*(\[[^\]]+\])',
                html,
                re.DOTALL
            )

            if not match:
                logger.warning(f"beIN Sports: listTvGuides not found for channel {channel_id}")
                logger.debug(f"beIN Sports: HTML snippet: {html[:500]}")
                if attempt < retry_count - 1:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                return []

            try:
                guides = json.loads(match.group(1))
            except json.JSONDecodeError as e:
                logger.error(f"beIN Sports: JSON parse error for channel {channel_id}: {e}")
                logger.debug(f"beIN Sports: Matched content: {match.group(1)[:500]}")
                if attempt < retry_count - 1:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                return []
            
            if not isinstance(guides, list):
                logger.error(f"beIN Sports: Expected list of guides for channel {channel_id}, got {type(guides)}")
                return []
            
            logger.info(f"beIN Sports: Successfully fetched {len(guides)} programmes for channel {channel_id}")
            return guides

        except requests.Timeout as e:
            logger.warning(f"beIN Sports: Timeout for channel {channel_id} (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                import time
                time.sleep(2 ** attempt)
                continue
        except requests.HTTPError as e:
            logger.error(f"beIN Sports: HTTP error for channel {channel_id} (status {e.response.status_code}): {e}")
            if attempt < retry_count - 1 and e.response.status_code >= 500:
                import time
                time.sleep(2 ** attempt)
                continue
            return []
        except requests.RequestException as e:
            logger.error(f"beIN Sports: Request error for channel {channel_id} (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                import time
                time.sleep(2 ** attempt)
                continue
        except Exception as e:
            logger.error(f"beIN Sports: Unexpected error for channel {channel_id}: {e}", exc_info=True)
            return []
    
    logger.error(f"beIN Sports: Failed to fetch channel {channel_id} after {retry_count} attempts")
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
            if not isinstance(g, dict):
                logger.debug(f"beIN Sports: Invalid guide entry for channel {ch_id}")
                continue
            
            ch = g.get("channel_id")
            if ch not in config.BEINSPORTS_CHANNELS:
                logger.debug(f"beIN Sports: Unknown channel_id {ch} in guide data")
                continue

            time_str = g.get("event_time")
            title = g.get("name", "").strip()
            date_str = g.get("event_date")  # Format: 1/2/2026 12:00:00 AM

            if not time_str or not title or not date_str:
                logger.debug(f"beIN Sports: Missing required fields for channel {ch}: time={time_str}, title={title}, date={date_str}")
                continue

            try:
                # Parse event date (format: "M/D/YYYY H:M:S AM/PM")
                date_parts = date_str.split(" ")
                if len(date_parts) < 1:
                    logger.warning(f"beIN Sports: Invalid date format for '{title}': {date_str}")
                    continue
                
                event_date = datetime.strptime(date_parts[0], "%m/%d/%Y")

                # Parse event time (format: "H:M:S")
                time_parts = time_str.split(":")
                if len(time_parts) != 3:
                    logger.warning(f"beIN Sports: Invalid time format for '{title}': {time_str}")
                    continue
                
                h, m, s = time_parts
                start_dt = event_date.replace(
                    hour=int(h), minute=int(m), second=int(s)
                )

                programmes_by_channel[ch].append({
                    "start": start_dt,
                    "title": title,
                })
            except ValueError as e:
                logger.warning(f"beIN Sports: Could not parse time for '{title}': {e} (date: {date_str}, time: {time_str})")
                continue
            except (TypeError, AttributeError) as e:
                logger.warning(f"beIN Sports: Type error parsing time for '{title}': {e}")
                continue
            except Exception as e:
                logger.error(f"beIN Sports: Unexpected error parsing programme '{title}': {e}", exc_info=True)
                continue

    # Convert to final format with stop times
    all_programmes = []

    for ch_id, items in programmes_by_channel.items():
        if not items:
            logger.debug(f"beIN Sports: No programmes for channel {ch_id}")
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
            
            # Validate times
            if stop <= start:
                logger.warning(f"beIN Sports: Invalid programme times for '{item['title']}': stop <= start")
                stop = start + timedelta(hours=1)  # Fallback to 1 hour

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
