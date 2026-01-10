#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""EPG Configuration"""

import os
from datetime import datetime

# Output settings
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "epg")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.xml")

# Timezone for XMLTV output
# D-Smart API returns UTC, beIN Sports returns Turkey time
TZ_UTC = "+0000"
TZ_TURKEY = "+0300"

# Days to fetch (today + N days)
DAYS_TO_FETCH = 7

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# API settings
REQUEST_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# D-Smart API
DSMART_API_URL = "https://www.dsmart.com.tr/api/v1/public/epg/schedules"
DSMART_CHANNELS_PER_PAGE = 250

# beIN Sports
BEINSPORTS_CHANNELS = {
    1: ("beinsports1.tr", "beIN Sports 1", "https://i.imgur.com/kM9zBTT.png"),
    2: ("beinsports2.tr", "beIN Sports 2", "https://i.imgur.com/BmJOHDc.png"),
    3: ("beinsports3.tr", "beIN Sports 3", "https://i.imgur.com/i7vjTkE.png"),
    4: ("beinsports4.tr", "beIN Sports 4", "https://i.imgur.com/mMDwBQ4.png"),
    13: ("beinsportshaber.tr", "beIN Sports Haber", "https://i.imgur.com/yShRjeb.png"),
}

BEINSPORTS_URLS = {
    1: "https://beinsports.com.tr/yayin-akisi/beinsports-1",
    2: "https://beinsports.com.tr/yayin-akisi/beinsports-2",
    3: "https://beinsports.com.tr/yayin-akisi/beinsports-3",
    4: "https://beinsports.com.tr/yayin-akisi/beinsports-4",
    13: "https://beinsports.com.tr/yayin-akisi/beinsports-haber",
}
