#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""TV Plus Turkey EPG Scraper"""

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
BASE_URL = "https://tvplus.com.tr/canli-tv/yayin-akisi"
BUILD_ID_CACHE = None


def normalize_slug(name: str) -> str:
    """
    Normalize channel name to slug format.
    Removes Turkish characters and special chars.
    """
    slug = name.strip()
    # Remove Turkish characters
    slug = slug.replace("ü", "u").replace("ö", "o").replace("ş", "s")
    slug = slug.replace("ç", "c").replace("ğ", "g").replace("ı", "i")
    slug = slug.replace("İ", "i").replace("Ş", "s").replace("Ç", "c")
    slug = slug.replace("Ğ", "g").replace("Ü", "u").replace("Ö", "o")
    # Convert to lowercase and replace spaces with hyphens
    slug = slug.lower().replace(" ", "-")
    # Remove special characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    return slug


def fetch_build_id(retry_count: int = 3) -> Optional[str]:
    """Fetch the Next.js buildId from the main page"""
    global BUILD_ID_CACHE
    
    if BUILD_ID_CACHE:
        return BUILD_ID_CACHE
    
    headers = {
        "User-Agent": config.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    for attempt in range(retry_count):
        try:
            logger.debug(f"TV Plus: Fetching buildId (attempt {attempt + 1}/{retry_count})")
            response = requests.get(BASE_URL, headers=headers, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            html = response.text
            
            # Find __NEXT_DATA__ script tag
            match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            if match:
                try:
                    next_data = json.loads(match.group(1))
                    build_id = next_data.get("buildId")
                    if build_id:
                        BUILD_ID_CACHE = build_id
                        logger.info(f"TV Plus: Got buildId: {build_id}")
                        return build_id
                except json.JSONDecodeError as e:
                    logger.warning(f"TV Plus: Failed to parse __NEXT_DATA__: {e}")
            
            logger.debug("TV Plus: Could not find buildId in page")
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)
                continue
            return None
            
        except requests.Timeout:
            logger.warning(f"TV Plus: Timeout fetching buildId (attempt {attempt + 1}/{retry_count})")
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)
                continue
        except requests.HTTPError as e:
            logger.error(f"TV Plus: HTTP error fetching buildId (status {e.response.status_code})")
            if attempt < retry_count - 1 and e.response.status_code >= 500:
                time.sleep(2 ** attempt)
                continue
            return None
        except Exception as e:
            logger.error(f"TV Plus: Unexpected error fetching buildId: {e}", exc_info=True)
            return None
    
    logger.error("TV Plus: Failed to fetch buildId after all attempts")
    return None


def fetch_channels(build_id: str, retry_count: int = 3) -> List[Dict[str, Any]]:
    """Fetch channel list from TV Plus API"""
    url = f"https://tvplus.com.tr/_next/data/{build_id}/tr/canli-tv/yayin-akisi.json"
    
    headers = {
        "User-Agent": config.USER_AGENT,
        "Accept": "application/json",
    }
    
    for attempt in range(retry_count):
        try:
            logger.debug(f"TV Plus: Fetching channels (attempt {attempt + 1}/{retry_count})")
            response = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Try different possible paths for channel data
            channels_json = (
                data.get("pageProps", {}).get("pageData", {}).get("channelData") or
                data.get("pageProps", {}).get("channelListSsr") or
                []
            )
            
            if not isinstance(channels_json, list):
                logger.error(f"TV Plus: Expected list of channels, got {type(channels_json)}")
                return []
            
            logger.info(f"TV Plus: Fetched {len(channels_json)} channels")
            return channels_json
            
        except requests.Timeout:
            logger.warning(f"TV Plus: Timeout fetching channels (attempt {attempt + 1}/{retry_count})")
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)
                continue
        except requests.HTTPError as e:
            logger.error(f"TV Plus: HTTP error fetching channels (status {e.response.status_code})")
            if attempt < retry_count - 1 and e.response.status_code >= 500:
                time.sleep(2 ** attempt)
                continue
            return []
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"TV Plus: Failed to parse channels JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"TV Plus: Unexpected error fetching channels: {e}", exc_info=True)
            return []
    
    logger.error("TV Plus: Failed to fetch channels after all attempts")
    return []


def fetch_channel_epg(build_id: str, channel_slug: str, channel_id: str, retry_count: int = 3) -> List[Dict[str, Any]]:
    """Fetch EPG data for a specific channel"""
    # Convert slug format: "kanal-d--123" for URL
    channel_param = channel_slug.replace("/", "--")
    url = f"https://tvplus.com.tr/_next/data/{build_id}/tr/canli-tv/yayin-akisi/{channel_param}.json?title={channel_param}"
    
    headers = {
        "User-Agent": config.USER_AGENT,
        "Accept": "application/json",
    }
    
    for attempt in range(retry_count):
        try:
            logger.debug(f"TV Plus: Fetching EPG for {channel_slug} (attempt {attempt + 1}/{retry_count})")
            response = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Try different possible paths for playbill data
            playbills = (
                data.get("pageProps", {}).get("pageData", {}).get("playbills") or
                data.get("pageProps", {}).get("allPlaybillList") or
                []
            )
            
            # Flatten if it's an array of arrays
            if isinstance(playbills, list) and len(playbills) > 0 and isinstance(playbills[0], list):
                playbills = [item for sublist in playbills for item in sublist]
            
            if not isinstance(playbills, list):
                logger.debug(f"TV Plus: No playbills for {channel_slug}")
                return []
            
            logger.debug(f"TV Plus: Fetched {len(playbills)} programmes for {channel_slug}")
            return playbills
            
        except requests.Timeout:
            logger.debug(f"TV Plus: Timeout fetching EPG for {channel_slug} (attempt {attempt + 1}/{retry_count})")
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)
                continue
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.debug(f"TV Plus: No EPG data available for {channel_slug} (404)")
                return []
            logger.debug(f"TV Plus: HTTP error fetching EPG for {channel_slug} (status {e.response.status_code})")
            if attempt < retry_count - 1 and e.response.status_code >= 500:
                time.sleep(2 ** attempt)
                continue
            return []
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"TV Plus: Failed to parse EPG JSON for {channel_slug}: {e}")
            return []
        except Exception as e:
            logger.error(f"TV Plus: Unexpected error fetching EPG for {channel_slug}: {e}", exc_info=True)
            return []
    
    logger.debug(f"TV Plus: Failed to fetch EPG for {channel_slug} after all attempts")
    return []


def fetch_all(days: int = None) -> Dict[str, Any]:
    """
    Fetch EPG data for all TV Plus channels
    
    Returns:
        {
            "channels": [{"id": "...", "name": "...", "logo": "..."}],
            "programmes": [{"channel": "...", "start": datetime, "stop": datetime, "title": "...", "desc": "..."}]
        }
    """
    if days is None:
        days = config.DAYS_TO_FETCH
    
    logger.info("TV Plus: Starting EPG fetch")
    
    # Step 1: Get buildId
    build_id = fetch_build_id()
    if not build_id:
        logger.error("TV Plus: Cannot proceed without buildId")
        return {"channels": [], "programmes": []}
    
    # Step 2: Get channel list
    channels_json = fetch_channels(build_id)
    if not channels_json:
        logger.warning("TV Plus: No channels found")
        return {"channels": [], "programmes": []}
    
    # Step 3: Process channels and fetch EPG
    all_channels = {}
    all_programmes = []
    
    # Get today's date range for filtering
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=days)
    
    for ch in channels_json:
        ch_name = ch.get("name", "").strip()
        ch_id_num = ch.get("id")
        ch_logo = ch.get("channelLogo", "")
        
        if not ch_name or not ch_id_num:
            logger.debug(f"TV Plus: Skipping channel with missing data: {ch}")
            continue
        
        # Create simple channel ID (just the normalized name)
        ch_id = normalize_slug(ch_name)
        
        # Create site_id for API (name-slug/id)
        site_id_slug = normalize_slug(ch_name)
        site_id = f"{site_id_slug}/{ch_id_num}"
        
        # Add channel
        all_channels[ch_id] = {
            "id": ch_id,
            "name": ch_name,
            "logo": ch_logo,
        }
        
        # Fetch EPG for this channel
        playbills = fetch_channel_epg(build_id, site_id, ch_id)
        
        for prog in playbills:
            if not isinstance(prog, dict):
                continue
            
            title = prog.get("name", "").strip()
            description = prog.get("introduce", "").strip()
            genres = prog.get("genres")
            
            # Parse timestamps (Unix timestamp in milliseconds or seconds)
            start_time = prog.get("starttime")
            end_time = prog.get("endtime")
            
            if not title or start_time is None:
                continue
            
            try:
                # Convert timestamp to datetime
                # TV Plus uses Unix timestamps (could be in seconds or milliseconds)
                if isinstance(start_time, (int, float)):
                    # If timestamp is too large, it's in milliseconds
                    if start_time > 10000000000:
                        start_dt = datetime.utcfromtimestamp(start_time / 1000)
                    else:
                        start_dt = datetime.utcfromtimestamp(start_time)
                else:
                    logger.debug(f"TV Plus: Invalid start_time type for '{title}': {type(start_time)}")
                    continue
                
                if end_time is not None and isinstance(end_time, (int, float)):
                    if end_time > 10000000000:
                        stop_dt = datetime.utcfromtimestamp(end_time / 1000)
                    else:
                        stop_dt = datetime.utcfromtimestamp(end_time)
                else:
                    # Default duration if no end time
                    stop_dt = start_dt + timedelta(hours=1)
                
                # Filter to only include today's programmes
                if not (today <= start_dt < tomorrow):
                    continue
                
                # Validate times
                if stop_dt <= start_dt:
                    stop_dt = start_dt + timedelta(hours=1)
                
                # Format category
                category = ""
                if genres:
                    if isinstance(genres, list):
                        category = ", ".join(str(g) for g in genres if g)
                    else:
                        category = str(genres)
                
                all_programmes.append({
                    "channel": ch_id,
                    "start": start_dt,
                    "stop": stop_dt,
                    "title": title,
                    "desc": description,
                    "category": category,
                    "tz": config.TZ_UTC,  # All times in UTC
                })
            
            except (ValueError, TypeError, OSError) as e:
                logger.debug(f"TV Plus: Could not parse times for '{title}': {e}")
                continue
            except Exception as e:
                logger.error(f"TV Plus: Unexpected error parsing programme '{title}': {e}", exc_info=True)
                continue
    
    logger.info(f"TV Plus: Total {len(all_channels)} channels, {len(all_programmes)} programmes")
    
    return {
        "channels": list(all_channels.values()),
        "programmes": all_programmes,
    }
