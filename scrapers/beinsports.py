#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""beIN Sports Turkey EPG Scraper"""

import requests
import re
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import config

logger = logging.getLogger(__name__)

# Constants
DEFAULT_LAST_PROGRAMME_DURATION_HOURS = 2
DEFAULT_FALLBACK_PROGRAMME_DURATION_HOURS = 1
TURKEY_UTC_OFFSET_HOURS = 3  # Turkey is UTC+3

# Channels that are known to not have EPG data available
# These will be skipped without warnings to keep logs clean
SKIP_CHANNELS = {1, 13}  # beIN Sports 1 and beIN Sports Haber


def extract_tv_guides(html: str) -> Optional[List[Dict]]:
    """
    Extract TV guide data from beIN Sports HTML page.
    Tries multiple methods to find the data.
    """
    # Method 1: Try to find listTvGuides in __NEXT_DATA__ script tag
    next_data_match = re.search(
        r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html,
        re.DOTALL
    )
    if next_data_match:
        try:
            next_data = json.loads(next_data_match.group(1))
            # Navigate through Next.js data structure
            props = next_data.get("props", {})
            page_props = props.get("pageProps", {})
            
            # Try different possible paths
            if "listTvGuides" in page_props:
                return page_props["listTvGuides"]
            if "tvGuides" in page_props:
                return page_props["tvGuides"]
            if "data" in page_props and isinstance(page_props["data"], dict):
                if "listTvGuides" in page_props["data"]:
                    return page_props["data"]["listTvGuides"]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # Method 2: Try original regex pattern (simple arrays)
    match = re.search(
        r'"listTvGuides"\s*:\s*(\[[^\]]*\])',
        html,
        re.DOTALL
    )
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Method 3: Try more flexible regex for nested JSON
    match = re.search(
        r'"listTvGuides"\s*:\s*(\[(?:[^\[\]]|\[(?:[^\[\]]|\[[^\[\]]*\])*\])*\])',
        html,
        re.DOTALL
    )
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Method 4: Find any JSON array after listTvGuides using bracket matching
    start_match = re.search(r'"listTvGuides"\s*:\s*\[', html)
    if start_match:
        start_idx = start_match.end() - 1  # Position of opening bracket
        bracket_count = 0
        end_idx = start_idx
        
        for i, char in enumerate(html[start_idx:], start=start_idx):
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end_idx = i + 1
                    break
        
        if end_idx > start_idx:
            try:
                return json.loads(html[start_idx:end_idx])
            except json.JSONDecodeError:
                pass

    return None


def fetch_channel(channel_id: int, url: str, retry_count: int = 3) -> List[Dict[str, Any]]:
    """Fetch EPG data for a single beIN Sports channel with retry logic"""
    
    # Skip channels that are known to not have data
    if channel_id in SKIP_CHANNELS:
        logger.debug(f"beIN Sports: Skipping channel {channel_id} (no EPG data available)")
        return []
    
    headers = {
        "User-Agent": config.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    for attempt in range(retry_count):
        try:
            logger.debug(f"beIN Sports: Fetching channel {channel_id} (attempt {attempt + 1}/{retry_count})")
            response = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            html = response.text
            
            if not html or len(html) < 100:
                logger.debug(f"beIN Sports: Empty or too short response for channel {channel_id}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                    continue
                return []

            guides = extract_tv_guides(html)
            
            if guides is None:
                logger.debug(f"beIN Sports: No TV guide data found for channel {channel_id}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                    continue
                return []
            
            if not isinstance(guides, list):
                logger.debug(f"beIN Sports: Expected list of guides for channel {channel_id}, got {type(guides)}")
                return []
            
            if len(guides) > 0:
                logger.info(f"beIN Sports: Successfully fetched {len(guides)} programmes for channel {channel_id}")
            return guides

        except requests.Timeout as e:
            logger.debug(f"beIN Sports: Timeout for channel {channel_id} (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)
                continue
        except requests.HTTPError as e:
            logger.debug(f"beIN Sports: HTTP error for channel {channel_id} (status {e.response.status_code}): {e}")
            if attempt < retry_count - 1 and e.response.status_code >= 500:
                time.sleep(2 ** attempt)
                continue
            return []
        except requests.RequestException as e:
            logger.debug(f"beIN Sports: Request error for channel {channel_id} (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)
                continue
        except Exception as e:
            logger.error(f"beIN Sports: Unexpected error for channel {channel_id}: {e}", exc_info=True)
            return []
    
    logger.debug(f"beIN Sports: Could not fetch channel {channel_id} after {retry_count} attempts")
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

    # Add channel definitions (only channels that have data)
    for ch_id, (xml_id, name, logo) in config.BEINSPORTS_CHANNELS.items():
        if ch_id not in SKIP_CHANNELS:
            channels.append({
                "id": xml_id,
                "name": name,
                "logo": logo,
            })
        programmes_by_channel[ch_id] = []

    # Fetch programmes for each channel
    for ch_id, url in config.BEINSPORTS_URLS.items():
        if ch_id in SKIP_CHANNELS:
            continue
            
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
                    logger.debug(f"beIN Sports: Invalid date format for '{title}': {date_str}")
                    continue
                
                event_date = datetime.strptime(date_parts[0], "%m/%d/%Y")

                # Parse event time (format: "H:M:S")
                time_parts = time_str.split(":")
                if len(time_parts) != 3:
                    logger.debug(f"beIN Sports: Invalid time format for '{title}': {time_str}")
                    continue
                
                h, m, s = time_parts
                start_dt = event_date.replace(
                    hour=int(h), minute=int(m), second=int(s)
                )
                
                # beIN Sports returns Turkey time (UTC+3), convert to UTC
                start_dt = start_dt - timedelta(hours=TURKEY_UTC_OFFSET_HOURS)

                programmes_by_channel[ch].append({
                    "start": start_dt,
                    "title": title,
                })
            except ValueError as e:
                logger.debug(f"beIN Sports: Could not parse time for '{title}': {e} (date: {date_str}, time: {time_str})")
                continue
            except (TypeError, AttributeError) as e:
                logger.debug(f"beIN Sports: Type error parsing time for '{title}': {e}")
                continue
            except Exception as e:
                logger.error(f"beIN Sports: Unexpected error parsing programme '{title}': {e}", exc_info=True)
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
                # Default duration for last programme
                stop = start + timedelta(hours=DEFAULT_LAST_PROGRAMME_DURATION_HOURS)
            
            # Validate times
            if stop <= start:
                stop = start + timedelta(hours=DEFAULT_FALLBACK_PROGRAMME_DURATION_HOURS)

            all_programmes.append({
                "channel": xml_id,
                "start": start,
                "stop": stop,
                "title": item["title"],
                "desc": "",
                "category": "Sports",
                "tz": config.TZ_UTC,  # All times in UTC
            })

    logger.info(f"beIN Sports: Total {len(channels)} channels, {len(all_programmes)} programmes")

    return {
        "channels": channels,
        "programmes": all_programmes,
    }
