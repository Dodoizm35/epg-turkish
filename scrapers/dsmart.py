#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""D-Smart EPG Scraper"""

import requests
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

import config

logger = logging.getLogger(__name__)

# Constants
DEFAULT_PROGRAMME_DURATION_MINUTES = 60

# Channel logo mappings (popular channels)
CHANNEL_LOGOS = {
    "kanal d": "https://i.imgur.com/VLwzfXl.png",
    "show tv": "https://i.imgur.com/M4F2xLv.png",
    "star": "https://i.imgur.com/Qq1jjVn.png",
    "atv": "https://i.imgur.com/dCljS6D.png",
    "trt 1": "https://i.imgur.com/sxNPH7E.png",
    "kanal 7": "https://i.imgur.com/FoKRxWt.png",
    "tv8": "https://i.imgur.com/zTVYQ4L.png",
    "fox": "https://i.imgur.com/qpPRlOE.png",
    "now": "https://i.imgur.com/OxnVZnP.png",
    "cnn türk": "https://i.imgur.com/n6evhXW.png",
    "ntv": "https://i.imgur.com/H7sCQvs.png",
    "trt haber": "https://i.imgur.com/JxBVWdW.png",
    "haber türk": "https://i.imgur.com/dSKZZgr.png",
    "a haber": "https://i.imgur.com/5wAuJHg.png",
    "haber global": "https://i.imgur.com/FzmYP2l.png",
    "bloomberg ht": "https://i.imgur.com/Qx5wLHJ.png",
    "bbc earth": "https://i.imgur.com/0d3rO0V.png",
    "discovery": "https://i.imgur.com/RkJGLnS.png",
    "national geographic": "https://i.imgur.com/VhEMz8a.png",
    "history channel": "https://i.imgur.com/cKF6M3k.png",
    "trt belgesel": "https://i.imgur.com/7XsJZKl.png",
    "cartoon network": "https://i.imgur.com/Xj3O3WY.png",
    "disney channel": "https://i.imgur.com/9G6wBLm.png",
    "trt çocuk": "https://i.imgur.com/hZpL9Qn.png",
    "minika go": "https://i.imgur.com/qWLMzLr.png",
    "minika çocuk": "https://i.imgur.com/m6HN7Ky.png",
    "eurosport": "https://i.imgur.com/9SMszSC.png",
    "eurosport 2": "https://i.imgur.com/vpXvPmB.png",
    "spor smart": "https://i.imgur.com/hLHJFHm.png",
    "a spor": "https://i.imgur.com/QTkhKjI.png",
    "trt spor": "https://i.imgur.com/U27aKnE.png",
    "nba tv": "https://i.imgur.com/aSxJykS.png",
    "fx": "https://i.imgur.com/LqwxQjN.png",
    "dmax": "https://i.imgur.com/7MnQxpR.png",
    "tlc": "https://i.imgur.com/PnspnHV.png",
    "teve2": "https://i.imgur.com/FrSqFDr.png",
}


def get_channel_logo(channel_name: str) -> str:
    """Get logo URL for a channel"""
    name_lower = channel_name.lower().strip()
    return CHANNEL_LOGOS.get(name_lower, "")


def make_channel_id(channel_name: str, ch_no: int) -> str:
    """Generate a unique channel ID"""
    slug = channel_name.lower()
    slug = slug.replace(" ", "").replace("-", "").replace("ü", "u").replace("ö", "o")
    slug = slug.replace("ş", "s").replace("ç", "c").replace("ğ", "g").replace("ı", "i")
    return f"{slug}.dsmart.tr"


def fetch_day(date: datetime, retry_count: int = 3) -> List[Dict[str, Any]]:
    """Fetch EPG data for a specific day with retry logic"""
    date_str = date.strftime("%Y-%m-%d")

    headers = {
        "User-Agent": config.USER_AGENT,
        "Accept": "application/json",
    }

    params = {
        "day": date_str,
        "page": 1,
        "limit": config.DSMART_CHANNELS_PER_PAGE,
    }

    for attempt in range(retry_count):
        try:
            logger.debug(f"D-Smart: Fetching data for {date_str} (attempt {attempt + 1}/{retry_count})")
            response = requests.get(
                config.DSMART_API_URL,
                headers=headers,
                params=params,
                timeout=config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            # Validate response is JSON
            try:
                data = response.json()
            except ValueError as json_err:
                logger.error(f"D-Smart: Invalid JSON response for {date_str}: {json_err}")
                logger.debug(f"D-Smart: Response content: {response.text[:500]}")
                if attempt < retry_count - 1:
                    continue
                return []

            # Validate response structure
            if not isinstance(data, dict):
                logger.error(f"D-Smart: Expected dict response for {date_str}, got {type(data)}")
                if attempt < retry_count - 1:
                    continue
                return []

            channels = data.get("data", {}).get("channels", [])
            
            if not isinstance(channels, list):
                logger.error(f"D-Smart: Expected list of channels for {date_str}, got {type(channels)}")
                return []
            
            logger.info(f"D-Smart: Successfully fetched {len(channels)} channels for {date_str}")
            return channels

        except requests.Timeout as e:
            logger.warning(f"D-Smart: Timeout for {date_str} (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
        except requests.HTTPError as e:
            logger.error(f"D-Smart: HTTP error for {date_str} (status {e.response.status_code}): {e}")
            if attempt < retry_count - 1 and e.response.status_code >= 500:
                time.sleep(2 ** attempt)
                continue
            return []
        except requests.RequestException as e:
            logger.error(f"D-Smart: Request error for {date_str} (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)
                continue
        except Exception as e:
            logger.error(f"D-Smart: Unexpected error for {date_str}: {e}", exc_info=True)
            return []

    logger.error(f"D-Smart: Failed to fetch data for {date_str} after {retry_count} attempts")
    return []


def fetch_all(days: int = None) -> Dict[str, Any]:
    """
    Fetch EPG data for multiple days

    Returns:
        {
            "channels": [{"id": "...", "name": "...", "logo": "..."}],
            "programmes": [{"channel": "...", "start": datetime, "stop": datetime, "title": "...", "desc": "..."}]
        }
    """
    if days is None:
        days = config.DAYS_TO_FETCH

    all_channels = {}
    all_programmes = []

    today = datetime.now()

    for day_offset in range(days):
        date = today + timedelta(days=day_offset)
        channels = fetch_day(date)

        for ch in channels:
            ch_name = ch.get("channel_name", "").strip()
            ch_no = ch.get("ch_no", 0)

            if not ch_name:
                continue

            # Skip SD duplicates and test channels
            if ch_name.endswith(" SD") or "Test" in ch_name or "Çoklu Ekran" in ch_name:
                continue

            ch_id = make_channel_id(ch_name, ch_no)

            # Add channel if not already added
            if ch_id not in all_channels:
                all_channels[ch_id] = {
                    "id": ch_id,
                    "name": ch_name,
                    "logo": get_channel_logo(ch_name),
                }

            # Parse programmes
            schedule = ch.get("schedule", [])
            
            if not isinstance(schedule, list):
                logger.warning(f"D-Smart: Invalid schedule format for channel {ch_name}")
                continue
            
            for prog in schedule:
                if not isinstance(prog, dict):
                    logger.debug(f"D-Smart: Invalid programme entry for channel {ch_name}")
                    continue
                
                prog_name = prog.get("program_name", "").strip()
                start_str = prog.get("start_date")
                end_str = prog.get("end_date")
                description = prog.get("description", "").strip()
                genre = prog.get("genre", "").strip()

                if not prog_name or not start_str:
                    logger.debug(f"D-Smart: Missing programme name or start time for channel {ch_name}")
                    continue

                try:
                    # Parse ISO format: 2026-01-10T08:00:00.000Z
                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))

                    if end_str:
                        stop_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                    else:
                        # Default duration if no end time
                        duration = prog.get("duration", DEFAULT_PROGRAMME_DURATION_MINUTES)
                        if not isinstance(duration, (int, float)) or duration <= 0:
                            duration = DEFAULT_PROGRAMME_DURATION_MINUTES
                        stop_dt = start_dt + timedelta(minutes=duration)

                    # Keep as UTC - XMLTV will handle timezone display
                    # Remove timezone info for naive datetime
                    start_dt = start_dt.replace(tzinfo=None)
                    stop_dt = stop_dt.replace(tzinfo=None)
                    
                    # Validate times - try to fix invalid times instead of skipping
                    if stop_dt <= start_dt:
                        # Fix invalid stop time by adding default duration
                        duration = prog.get("duration", DEFAULT_PROGRAMME_DURATION_MINUTES)
                        if not isinstance(duration, (int, float)) or duration <= 0:
                            duration = DEFAULT_PROGRAMME_DURATION_MINUTES
                        stop_dt = start_dt + timedelta(minutes=duration)
                        logger.debug(f"D-Smart: Fixed invalid stop time for '{prog_name}' on {ch_name}")

                    all_programmes.append({
                        "channel": ch_id,
                        "start": start_dt,
                        "stop": stop_dt,
                        "title": prog_name,
                        "desc": description,
                        "category": genre,
                        "tz": config.TZ_UTC,  # D-Smart API returns UTC
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"D-Smart: Could not parse programme time for '{prog_name}' on {ch_name}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"D-Smart: Unexpected error parsing programme on {ch_name}: {e}", exc_info=True)
                    continue

    logger.info(f"D-Smart: Total {len(all_channels)} channels, {len(all_programmes)} programmes")

    return {
        "channels": list(all_channels.values()),
        "programmes": all_programmes,
    }
