#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Channel ID Mapping for Universal IPTV Compatibility

This module generates multiple channel IDs for each channel to ensure
compatibility with various IPTV providers and applications.

Common IPTV provider formats:
- Provider format: "ChannelName.tr" (CamelCase)
- D-Smart format: "channelname.dsmart.tr" (lowercase)
- Simple format: "channelname.tr" (lowercase)
- Generic format: "ChannelName" (no suffix)
"""

import re
from typing import List, Dict, Tuple

# Manual mappings for channels with non-obvious name variations
# Format: "dsmart_slug" -> ["alias1", "alias2", ...]
MANUAL_ALIASES = {
    # News channels
    "cnnturk": ["CNNTurk", "cnn-turk", "CNN_Turk"],
    "ahaber": ["AHaber", "a-haber", "A_Haber"],
    "haberturk": ["Haberturk", "haber-turk", "HaberTurk"],
    "habertürk": ["Haberturk", "haber-turk", "HaberTurk"],
    "ntv": ["NTV"],
    "trt1": ["TRT1", "trt-1", "TRT_1"],
    "trthaber": ["TRTHaber", "trt-haber", "TRT_Haber"],
    "habrglobal": ["HaberGlobal", "haber-global"],
    "haberglobal": ["HaberGlobal", "haber-global"],
    "tv100": ["TV100", "tv-100"],
    "24": ["24", "Kanal24", "kanal-24"],
    "bloomberght": ["BloombergHT", "bloomberg-ht"],

    # Main channels
    "kanald": ["KanalD", "kanal-d", "Kanal_D"],
    "showtv": ["ShowTV", "show-tv", "Show_TV"],
    "startv": ["StarTV", "star-tv", "Star_TV"],
    "star": ["StarTV", "star-tv", "Star_TV"],
    "atv": ["ATV", "atv"],
    "kanal7": ["Kanal7", "kanal-7", "Kanal_7"],
    "tv8": ["TV8", "tv-8"],
    "fox": ["Fox", "FOX", "FoxTV", "NOW", "NowTV"],
    "now": ["NOW", "NowTV", "Fox", "FOX", "FoxTV"],
    "teve2": ["Teve2", "teve-2", "TV2"],
    "tv8int": ["TV8INT", "tv8-int"],
    "tv85": ["tv85", "TV8.5"],
    "a2": ["a2tv", "A2", "a2"],

    # TRT channels
    "trtspor": ["TRTSpor", "trt-spor", "TRT_Spor"],
    "trtsporstar": ["TrtSporYildiz", "TRTSporStar", "trt-spor-star"],
    "trtsporyildiz": ["TrtSporYildiz", "TRTSporYildiz", "trt-spor-yildiz"],
    "trtbelgesel": ["TRTBelgesel", "trt-belgesel", "TRT_Belgesel"],
    "trtcocuk": ["TRTCocuk", "trt-cocuk", "TRT_Cocuk"],
    "trtmuzik": ["TRTMuzik", "trt-muzik", "TRT_Muzik"],
    "trtturk": ["TRTTurk", "trt-turk", "TRT_Turk"],
    "trtworld": ["TRTWorld", "trt-world", "TRT_World"],
    "trtkurdi": ["TRTKurdi", "trt-kurdi", "TRT_Kurdi"],
    "trtavaz": ["TRTAvaz", "trt-avaz"],
    "trt3": ["TRT3SporTBMMTV", "TRT3", "trt-3"],
    "trtarabic": ["TRTAlArabiya", "trt-arabic"],
    "trtalarbiya": ["TRTAlArabiya", "trt-alarabiya"],

    # Sports channels
    "aspor": ["ASpor", "a-spor", "A_Spor"],
    "sporsmart": ["SportsTV", "spor-smart", "SportSmart"],
    "sportstv": ["SportsTV", "sports-tv"],
    "eurosport": ["Eurosport1", "euro-sport", "EuroSport"],
    "eurosport2": ["Eurosport2", "euro-sport-2", "EuroSport2"],
    "nbatv": ["NBATV", "nba-tv"],
    "fbtv": ["FBTV", "fb-tv", "FenerbahceTV"],
    "gstv": ["GSTV", "gs-tv", "GalatasarayTV"],
    "bjktv": ["BJKTV", "bjk-tv", "BesiktasTV"],
    "tstv": ["TSTV", "ts-tv", "TrabzonsporTV"],

    # Kids channels
    "cartoonnetwork": ["CartoonNetwork", "cartoon-network", "CN", "CartoonNetworkTR"],
    "disneychannel": ["DisneyChannel", "disney-channel", "Disney"],
    "disneyjunior": ["DisneyJunior", "disney-junior"],
    "minikago": ["minikaGO", "minika-go", "MinikaGO"],
    "minikacocuk": ["minikaCocuk", "minika-cocuk", "MinikaCocuk"],
    "cartoonito": ["Cartoonito", "cartoonito"],
    "babytv": ["BabyTV", "baby-tv"],
    "nickelodeon": ["Nickelodeon", "nick"],
    "nickjr": ["NickJr", "nick-jr"],
    "davincilearning": ["DaVinciLearning", "davinci"],

    # Documentary channels
    "discovery": ["DiscoveryChannel", "discovery-channel", "Discovery"],
    "discoveryid": ["DiscoveryIDXtra", "discovery-id", "DiscoveryID"],
    "discoveryscience": ["DiscoveryScience", "discovery-science"],
    "nationalgeographic": ["NatGeo", "national-geographic", "NationalGeographic", "NatGeoHD"],
    "natgeowild": ["NatGeoWild", "nat-geo-wild", "NationalGeographicWild"],
    "bbcearth": ["BBCEarth", "bbc-earth", "BBC_Earth"],
    "animalplanet": ["AnimalPlanet", "animal-planet"],
    "historychannel": ["ViasatHistoryNature", "history-channel", "History"],
    "viasathistory": ["ViasatHistoryNature", "viasat-history"],
    "dmax": ["DMAX", "d-max"],
    "tlc": ["TLC", "tlc"],

    # Movie/Series channels
    "fx": ["FX", "FxTV"],
    "foxcrime": ["FoxCrime", "fox-crime", "FOXCrime"],
    "foxlife": ["FoxLife", "fox-life", "FOXLife"],
    "sinematv": ["SinemaTV", "sinema-tv"],
    "sinemaaile": ["SinemaTVAile", "sinema-aile"],
    "sinematurk": ["SinemaTVTurk", "sinema-turk"],
    "sinemaaksiyon": ["SinemaTVAksiyon", "sinema-aksiyon"],
    "sinemakomedi": ["SinemaTVComedy", "sinema-komedi"],
    "filmbox": ["FilmBox", "film-box"],
    "filmboxextra": ["FilmBoxExtra", "filmbox-extra"],
    "filmboxarthouse": ["FilmBoxArthouse", "filmbox-arthouse"],
    "filmboxaction": ["FilmBoxAction", "filmbox-action"],
    "filmboxfamily": ["FilmBoxFamily", "filmbox-family"],

    # beIN channels
    "beinsports1": ["beINSports1", "bein-sports-1", "beIN_Sports_1", "beIN1"],
    "beinsports2": ["beINSports2", "bein-sports-2", "beIN_Sports_2", "beIN2"],
    "beinsports3": ["beINSports3", "bein-sports-3", "beIN_Sports_3", "beIN3"],
    "beinsports4": ["beINSports4", "bein-sports-4", "beIN_Sports_4", "beIN4"],
    "beinsportshaber": ["beINSportsHaber", "bein-sports-haber", "beINHaber"],
    "beinsportsmax1": ["beINSportsMax1", "bein-max-1"],
    "beinsportsmax2": ["beINSportsMax2", "bein-max-2"],

    # beIN Movies
    "beinmoviesturk": ["beINMoviesTurk", "bein-movies-turk"],
    "beinmoviesstars": ["beINMoviesStars", "bein-movies-stars"],
    "beinmoviesaction": ["beINMoviesAction", "bein-movies-action"],
    "beinmoviesaction2": ["beINMoviesAction2", "bein-movies-action-2"],
    "beinmoviesfamily": ["beINMoviesFamily", "bein-movies-family"],
    "beinmoviespremier": ["beINMoviesPremier", "bein-movies-premier"],
    "beinmoviespremiere2": ["beINMoviesPremiere2", "bein-movies-premiere-2"],
    "beinboxoffice1": ["beINBoxOffice1", "bein-box-office-1"],
    "beinboxoffice2": ["beINBoxOffice2", "bein-box-office-2"],
    "beinboxoffice3": ["beINBoxOffice3", "bein-box-office-3"],

    # beIN Series
    "beinseriescomedy": ["beINSeriesComedy", "bein-series-comedy"],
    "beinseriesdrama": ["beINSeriesDrama", "bein-series-drama"],
    "beinseriesscifi": ["beINSeriesSciFi", "bein-series-scifi"],
    "beinseriesvice": ["beINSeriesVice", "bein-series-vice"],

    # Other channels
    "beyaztv": ["BeyazTV", "beyaz-tv", "Beyaz_TV"],
    "halktv": ["HalkTV", "halk-tv", "Halk_TV"],
    "kanalb": ["KanalB", "kanal-b"],
    "ulusalkanal": ["UlusalKanal", "ulusal-kanal"],
    "powerturk": ["Powerturk", "power-turk", "PowerTurk"],
    "showmax": ["Showmax", "show-max"],
    "showturk": ["ShowTurk", "show-turk"],
}


def normalize_name(name: str) -> str:
    """Normalize channel name to create a base slug"""
    slug = name.lower().strip()
    # Remove common suffixes
    slug = re.sub(r'\s*(hd|sd|fhd|uhd|4k)$', '', slug, flags=re.IGNORECASE)
    # Turkish character normalization
    slug = slug.replace("ü", "u").replace("ö", "o").replace("ş", "s")
    slug = slug.replace("ç", "c").replace("ğ", "g").replace("ı", "i")
    slug = slug.replace("İ", "i").replace("Ş", "s").replace("Ç", "c")
    slug = slug.replace("Ğ", "g").replace("Ü", "u").replace("Ö", "o")
    # Remove spaces and special characters
    slug = re.sub(r'[^a-z0-9]', '', slug)
    return slug


def generate_channel_ids(channel_name: str, primary_id: str) -> List[str]:
    """
    Generate multiple channel IDs for a single channel.
    Optimized to generate only the most common formats to reduce file size.

    Args:
        channel_name: Original channel name (e.g., "CNN Türk")
        primary_id: Primary ID used in our EPG (e.g., "cnnturk.dsmart.tr")

    Returns:
        List of all possible IDs for this channel
    """
    ids = set()

    # Always include the primary ID
    ids.add(primary_id)

    # Extract base slug from primary_id
    base_slug = primary_id.replace(".dsmart.tr", "").replace(".tr", "")

    # Generate lowercase version
    lowercase = normalize_name(channel_name)

    # Key formats: lowercase.tr and CamelCase.tr (most common IPTV formats)
    ids.add(f"{lowercase}.tr")

    # Reconstruct CamelCase properly
    cc = ''.join(word.capitalize() for word in re.findall(r'[A-Za-z][a-z]*|\d+', channel_name))
    cc = cc.replace("Ü", "u").replace("ö", "o").replace("ş", "s")
    cc = cc.replace("ç", "c").replace("ğ", "g").replace("ı", "i")
    cc = cc.replace("İ", "I").replace("Ş", "S").replace("Ç", "C")
    cc = cc.replace("Ğ", "G").replace("Ü", "U").replace("Ö", "O")
    if cc:
        ids.add(f"{cc}.tr")

    # Add manual aliases if available (only with .tr suffix for consistency)
    if base_slug in MANUAL_ALIASES:
        for alias in MANUAL_ALIASES[base_slug]:
            ids.add(f"{alias}.tr")

    # Also check normalized slug
    normalized = normalize_name(channel_name)
    if normalized in MANUAL_ALIASES:
        for alias in MANUAL_ALIASES[normalized]:
            ids.add(f"{alias}.tr")

    # Remove empty strings and duplicates
    ids = {id for id in ids if id}

    return sorted(list(ids))


def get_channel_with_aliases(channel: Dict) -> Tuple[Dict, List[str]]:
    """
    Get channel info with all its aliases.

    Args:
        channel: Channel dict with 'id', 'name', 'logo'

    Returns:
        Tuple of (channel_dict, list_of_all_ids)
    """
    primary_id = channel["id"]
    name = channel["name"]

    all_ids = generate_channel_ids(name, primary_id)

    return channel, all_ids
