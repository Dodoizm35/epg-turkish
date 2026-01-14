#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Turkey EPG Generator
Generates XMLTV format EPG for Turkish TV channels.

Sources:
- TV Plus: Turkish TV channels (general TV)
- beIN Sports: 5 channels (sports) - optional
"""

import os
import sys
import logging
from datetime import datetime
from html import escape
from typing import Dict, Any, List

import config
from scrapers import tvplus, beinsports

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Constants
EMPTY_EPG_DATA = {"channels": [], "programmes": []}


def xml_time(dt: datetime, tz: str) -> str:
    """Format datetime for XMLTV with timezone"""
    if not isinstance(dt, datetime):
        raise ValueError(f"Expected datetime object, got {type(dt)}")
    if not tz:
        raise ValueError("Timezone cannot be empty")
    return dt.strftime("%Y%m%d%H%M%S") + f" {tz}"


def escape_xml(text: str) -> str:
    """Escape special characters for XML"""
    if not text:
        return ""
    return escape(text)


def generate_xml(channels: List[Dict], programmes: List[Dict]) -> str:
    """Generate XMLTV format XML with proper formatting and single channel IDs"""
    if not isinstance(channels, list):
        raise ValueError(f"channels must be a list, got {type(channels)}")
    if not isinstance(programmes, list):
        raise ValueError(f"programmes must be a list, got {type(programmes)}")
    
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE tv SYSTEM "xmltv.dtd">',
        '<tv generator-info-name="Turkey EPG">',
    ]

    # Channel definitions - one ID per channel
    for ch in channels:
        if not isinstance(ch, dict):
            logger.warning(f"Skipping invalid channel entry: {ch}")
            continue
        
        ch_id = ch.get("id")
        ch_name = ch.get("name", "")
        
        if not ch_id:
            logger.warning(f"Skipping channel with missing id: {ch}")
            continue
        
        ch_name = escape_xml(ch_name)
        logo = ch.get("logo", "")

        # Format with proper indentation
        lines.append(f'  <channel id="{escape_xml(ch_id)}">')
        lines.append(f'    <display-name>{ch_name}</display-name>')
        if logo:
            lines.append(f'    <icon src="{escape_xml(logo)}" />')
        lines.append('  </channel>')
        lines.append('')  # Empty line for readability

    # Programme entries - one entry per programme
    for prog in programmes:
        if not isinstance(prog, dict):
            logger.warning(f"Skipping invalid programme entry: {prog}")
            continue
        
        ch_id = prog.get("channel")
        if not ch_id:
            logger.warning(f"Skipping programme with missing channel: {prog}")
            continue
        
        tz = prog.get("tz", config.TZ_UTC)
        start_dt = prog.get("start")
        stop_dt = prog.get("stop")
        title = prog.get("title", "")
        
        if not start_dt or not stop_dt:
            logger.warning(f"Skipping programme with missing times: {prog}")
            continue
        
        if not title:
            logger.debug(f"Programme with empty title on channel {ch_id}")
            title = "Unknown"
        
        try:
            start = xml_time(start_dt, tz)
            stop = xml_time(stop_dt, tz)
        except (ValueError, AttributeError) as e:
            logger.warning(f"Skipping programme with invalid datetime: {e}")
            continue
        
        title = escape_xml(title)

        # Format with proper indentation
        lines.append(f'  <programme start="{start}" stop="{stop}" channel="{escape_xml(ch_id)}">')
        lines.append(f'    <title lang="tr">{title}</title>')

        if prog.get("desc"):
            lines.append(f'    <desc lang="tr">{escape_xml(prog["desc"])}</desc>')

        if prog.get("category"):
            lines.append(f'    <category lang="tr">{escape_xml(prog["category"])}</category>')

        lines.append('  </programme>')

    lines.append('</tv>')

    return '\n'.join(lines)


def merge_data(*sources: Dict[str, Any]) -> Dict[str, Any]:
    """Merge data from multiple sources"""
    all_channels = {}
    all_programmes = []

    for source in sources:
        if not isinstance(source, dict):
            logger.warning(f"Skipping invalid source: {type(source)}")
            continue
        
        for ch in source.get("channels", []):
            if not isinstance(ch, dict):
                logger.warning(f"Skipping invalid channel: {ch}")
                continue
            
            ch_id = ch.get("id")
            if not ch_id:
                logger.warning(f"Skipping channel with missing id: {ch}")
                continue
            
            if ch_id not in all_channels:
                all_channels[ch_id] = ch

        programmes = source.get("programmes", [])
        if isinstance(programmes, list):
            all_programmes.extend(programmes)
        else:
            logger.warning(f"Invalid programmes list in source: {type(programmes)}")

    # Sort programmes by start time
    try:
        all_programmes.sort(key=lambda x: (x.get("channel", ""), x.get("start", datetime.min)))
    except (TypeError, AttributeError) as e:
        logger.warning(f"Error sorting programmes: {e}")

    return {
        "channels": list(all_channels.values()),
        "programmes": all_programmes,
    }


def main():
    """Main entry point"""
    try:
        logger.info("Starting EPG generation...")

        # Fetch from all sources
        logger.info("Fetching TV Plus EPG...")
        try:
            tvplus_data = tvplus.fetch_all()
        except Exception as e:
            logger.error(f"Failed to fetch TV Plus data: {e}", exc_info=True)
            tvplus_data = EMPTY_EPG_DATA

        logger.info("Fetching beIN Sports EPG...")
        try:
            beinsports_data = beinsports.fetch_all()
        except Exception as e:
            logger.error(f"Failed to fetch beIN Sports data: {e}", exc_info=True)
            beinsports_data = EMPTY_EPG_DATA

        # Merge all sources
        merged = merge_data(tvplus_data, beinsports_data)

        logger.info(f"Total: {len(merged['channels'])} channels, {len(merged['programmes'])} programmes")

        if len(merged['channels']) == 0:
            logger.warning("No channels found! Generated EPG will be empty.")

        # Generate XML with single IDs (no aliases)
        try:
            xml_content = generate_xml(merged["channels"], merged["programmes"])
        except Exception as e:
            logger.error(f"Failed to generate XML: {e}", exc_info=True)
            return 1

        # Ensure output directory exists
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)

        # Write output
        try:
            with open(config.OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(xml_content)
            logger.info(f"EPG written to {config.OUTPUT_FILE}")
        except IOError as e:
            logger.error(f"Failed to write output file: {e}", exc_info=True)
            return 1

        # Print summary
        print(f"\n{'='*50}")
        print(f"EPG Generation Complete!")
        print(f"{'='*50}")
        print(f"Channels: {len(merged['channels'])}")
        print(f"Programmes: {len(merged['programmes'])}")
        print(f"Output: {config.OUTPUT_FILE}")
        print(f"{'='*50}\n")

        return 0
    
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
