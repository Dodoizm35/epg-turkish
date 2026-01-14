#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
D-Smart EPG Scraper

DEPRECATED: This scraper is no longer used in favor of TV Plus.
Kept for reference purposes only.
"""

import requests
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

import config

logger = logging.getLogger(__name__)

# Constants
DEFAULT_PROGRAMME_DURATION_MINUTES = 60

# Channel logo mappings (official D-Smart CDN)
# Using D-Smart's official CDN instead of Imgur for better reliability
CHANNEL_LOGOS = {
    "kanal d": "https://dsmart-static-v2.ercdn.net/content/-/EU/11785/Thumbnail.png",
    "show tv": "https://dsmart-static-v2.ercdn.net/content/E/aM/11889/Thumbnail.png",
    "star": "https://dsmart-static-v2.ercdn.net/content/E/oG/11875/Thumbnail.png",
    "atv": "https://dsmart-static-v2.ercdn.net/content/Q/Eq/13351/Thumbnail.png",
    "trt 1": "https://dsmart-static-v2.ercdn.net/content/Q/ou/11887/Thumbnail.png",
    "kanal 7": "https://dsmart-static-v2.ercdn.net/content/E/7Y/11821/Thumbnail.png",
    "tv8": "https://dsmart-static-v2.ercdn.net/content/Q/EJ/11868/Thumbnail.png",
    "fox": "https://dsmart-static-v2.ercdn.net/content/Q/AK/11882/Thumbnail.png",
    "now": "https://dsmart-static-v2.ercdn.net/content/Q/AK/11882/Thumbnail.png",  # NOW is former FOX
    "teve2": "https://dsmart-static-v2.ercdn.net/content/Q/AL/11888/Thumbnail.png",
    "beyaz tv": "https://dsmart-static-v2.ercdn.net/content/E/ZY/11886/Thumbnail.png",
    "cnn türk": "https://dsmart-static-v2.ercdn.net/content/E/JA/11897/Thumbnail.png",
    "ntv": "https://dsmart-static-v2.ercdn.net/content/Q/oN/11852/Thumbnail.png",
    "trt haber": "https://dsmart-static-v2.ercdn.net/content/E/Kq/11881/Thumbnail.png",
    "habertürk": "https://dsmart-static-v2.ercdn.net/content/Q/o5/11851/Thumbnail.png",
    "haber türk": "https://dsmart-static-v2.ercdn.net/content/Q/o5/11851/Thumbnail.png",
    "a haber": "https://dsmart-static-v2.ercdn.net/content/Q/ou/11886/Thumbnail.png",
    "haber global": "https://dsmart-static-v2.ercdn.net/content/Q/EG/11849/Thumbnail.png",
    "bloomberg ht": "https://dsmart-static-v2.ercdn.net/content/Q/ou/11847/Thumbnail.png",
    "trt spor": "https://dsmart-static-v2.ercdn.net/content/E/aO/11880/Thumbnail.png",
    "a spor": "https://dsmart-static-v2.ercdn.net/content/Q/E8/11848/Thumbnail.png",
    "trt belgesel": "https://dsmart-static-v2.ercdn.net/content/E/7I/11879/Thumbnail.png",
    "trt çocuk": "https://dsmart-static-v2.ercdn.net/content/Q/Es/11878/Thumbnail.png",
    "cartoon network": "https://dsmart-static-v2.ercdn.net/content/Q/o4/11853/Thumbnail.png",
    "disney channel": "https://dsmart-static-v2.ercdn.net/content/E/Jw/11855/Thumbnail.png",
    "minika go": "https://dsmart-static-v2.ercdn.net/content/Q/Em/11856/Thumbnail.png",
    "minika çocuk": "https://dsmart-static-v2.ercdn.net/content/Q/o2/11857/Thumbnail.png",
    "national geographic": "https://dsmart-static-v2.ercdn.net/content/Q/o6/11858/Thumbnail.png",
    "discovery": "https://dsmart-static-v2.ercdn.net/content/Q/Em/11859/Thumbnail.png",
    "bbc earth": "https://dsmart-static-v2.ercdn.net/content/Q/o3/11860/Thumbnail.png",
    "eurosport": "https://dsmart-static-v2.ercdn.net/content/E/ae/11861/Thumbnail.png",
    "eurosport 2": "https://dsmart-static-v2.ercdn.net/content/E/J2/11862/Thumbnail.png",
    "spor smart": "https://dsmart-static-v2.ercdn.net/content/Q/EF/11863/Thumbnail.png",
    "nba tv": "https://dsmart-static-v2.ercdn.net/content/Q/ou/11864/Thumbnail.png",
    "fx": "https://dsmart-static-v2.ercdn.net/content/E/7G/11865/Thumbnail.png",
    "dmax": "https://dsmart-static-v2.ercdn.net/content/Q/o7/11866/Thumbnail.png",
    "tlc": "https://dsmart-static-v2.ercdn.net/content/Q/oM/11867/Thumbnail.png",
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

                    # Convert UTC to Turkey time (+3 hours)
                    # D-Smart API returns UTC, but we need to display in Turkey time
                    start_dt = start_dt + timedelta(hours=3)
                    stop_dt = stop_dt + timedelta(hours=3)
                    
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
                        "tz": config.TZ_TURKEY,  # Display in Turkey time
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
