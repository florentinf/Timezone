"""
Enhanced timezone parser for Discord Timezone Bot.
Supports various timezone formats including:
- IANA timezone names (America/New_York)
- Common abbreviations (EST, PST, CEST)
- UTC/GMT offsets (UTC+2, GMT-5)
- Cities and countries
- Various natural language expressions
"""

import re
import pytz
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, List, Union
from difflib import get_close_matches

# Mapping of common timezone abbreviations to IANA timezones
# This is not exhaustive but covers the most common ones
TIMEZONE_ABBREVIATIONS = {
    # North America
    "EST": "America/New_York",  # Eastern Standard Time
    "EDT": "America/New_York",  # Eastern Daylight Time
    "CST": "America/Chicago",   # Central Standard Time
    "CDT": "America/Chicago",   # Central Daylight Time
    "MST": "America/Denver",    # Mountain Standard Time
    "MDT": "America/Denver",    # Mountain Daylight Time
    "PST": "America/Los_Angeles",  # Pacific Standard Time
    "PDT": "America/Los_Angeles",  # Pacific Daylight Time
    
    # Europe
    "GMT": "Europe/London",     # Greenwich Mean Time
    "BST": "Europe/London",     # British Summer Time
    "WET": "Europe/Lisbon",     # Western European Time
    "WEST": "Europe/Lisbon",    # Western European Summer Time
    "CET": "Europe/Paris",      # Central European Time
    "CEST": "Europe/Paris",     # Central European Summer Time
    "EET": "Europe/Helsinki",   # Eastern European Time
    "EEST": "Europe/Helsinki",  # Eastern European Summer Time
    
    # Asia/Pacific
    "JST": "Asia/Tokyo",        # Japan Standard Time
    "KST": "Asia/Seoul",        # Korea Standard Time
    "CST_CN": "Asia/Shanghai",  # China Standard Time
    "IST": "Asia/Kolkata",      # Indian Standard Time
    "AEST": "Australia/Sydney", # Australian Eastern Standard Time
    "AEDT": "Australia/Sydney", # Australian Eastern Daylight Time
    "ACST": "Australia/Adelaide", # Australian Central Standard Time
    "ACDT": "Australia/Adelaide", # Australian Central Daylight Time
    "AWST": "Australia/Perth",  # Australian Western Standard Time
    "NZST": "Pacific/Auckland", # New Zealand Standard Time
    "NZDT": "Pacific/Auckland", # New Zealand Daylight Time
    
    # Other
    "UTC": "UTC",               # Universal Coordinated Time
    "Z": "UTC",                 # Zulu Time (UTC)
}

# Major cities and their timezones
# This list includes major cities from around the world
CITY_TIMEZONES = {
    # North America
    "new york": "America/New_York",
    "los angeles": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "toronto": "America/Toronto",
    "vancouver": "America/Vancouver",
    "mexico city": "America/Mexico_City",
    "denver": "America/Denver",
    "phoenix": "America/Phoenix",
    "las vegas": "America/Los_Angeles",
    "montreal": "America/Montreal",
    "miami": "America/New_York",
    "dallas": "America/Chicago",
    "seattle": "America/Los_Angeles",
    "boston": "America/New_York",
    "san francisco": "America/Los_Angeles",
    "atlanta": "America/New_York",
    "houston": "America/Chicago",
    
    # Europe
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "rome": "Europe/Rome",
    "madrid": "Europe/Madrid",
    "amsterdam": "Europe/Amsterdam",
    "brussels": "Europe/Brussels",
    "vienna": "Europe/Vienna",
    "stockholm": "Europe/Stockholm",
    "oslo": "Europe/Oslo",
    "copenhagen": "Europe/Copenhagen",
    "helsinki": "Europe/Helsinki",
    "athens": "Europe/Athens",
    "warsaw": "Europe/Warsaw",
    "prague": "Europe/Prague",
    "zurich": "Europe/Zurich",
    "dublin": "Europe/Dublin",
    "lisbon": "Europe/Lisbon",
    "budapest": "Europe/Budapest",
    
    # Asia
    "tokyo": "Asia/Tokyo",
    "beijing": "Asia/Shanghai",
    "shanghai": "Asia/Shanghai",
    "hong kong": "Asia/Hong_Kong",
    "singapore": "Asia/Singapore",
    "seoul": "Asia/Seoul",
    "bangkok": "Asia/Bangkok",
    "mumbai": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "dubai": "Asia/Dubai",
    "istanbul": "Europe/Istanbul",  # Geographically in both Europe and Asia
    "taipei": "Asia/Taipei",
    "jakarta": "Asia/Jakarta",
    "kuala lumpur": "Asia/Kuala_Lumpur",
    "manila": "Asia/Manila",
    
    # Oceania
    "sydney": "Australia/Sydney",
    "melbourne": "Australia/Melbourne",
    "brisbane": "Australia/Brisbane",
    "perth": "Australia/Perth",
    "auckland": "Pacific/Auckland",
    "wellington": "Pacific/Auckland",
    
    # South America
    "sao paulo": "America/Sao_Paulo",
    "rio de janeiro": "America/Sao_Paulo",
    "buenos aires": "America/Argentina/Buenos_Aires",
    "santiago": "America/Santiago",
    "lima": "America/Lima",
    "bogota": "America/Bogota",
    
    # Africa
    "johannesburg": "Africa/Johannesburg",
    "cairo": "Africa/Cairo",
    "lagos": "Africa/Lagos",
    "nairobi": "Africa/Nairobi",
    "casablanca": "Africa/Casablanca",
}

# Country to timezone mapping (uses a representative timezone for each country)
COUNTRY_TIMEZONES = {
    "usa": "America/New_York",
    "united states": "America/New_York",
    "us": "America/New_York",
    "canada": "America/Toronto",
    "mexico": "America/Mexico_City",
    "uk": "Europe/London",
    "united kingdom": "Europe/London",
    "england": "Europe/London",
    "france": "Europe/Paris",
    "germany": "Europe/Berlin",
    "italy": "Europe/Rome",
    "spain": "Europe/Madrid",
    "japan": "Asia/Tokyo",
    "china": "Asia/Shanghai",
    "india": "Asia/Kolkata",
    "australia": "Australia/Sydney",
    "russia": "Europe/Moscow",
    "brazil": "America/Sao_Paulo",
    "south korea": "Asia/Seoul",
    "korea": "Asia/Seoul",
    "netherlands": "Europe/Amsterdam",
    "belgium": "Europe/Brussels",
    "sweden": "Europe/Stockholm",
    "norway": "Europe/Oslo",
    "denmark": "Europe/Copenhagen",
    "finland": "Europe/Helsinki",
    "poland": "Europe/Warsaw",
    "austria": "Europe/Vienna",
    "switzerland": "Europe/Zurich",
    "portugal": "Europe/Lisbon",
    "greece": "Europe/Athens",
    "ireland": "Europe/Dublin",
    "new zealand": "Pacific/Auckland",
    "south africa": "Africa/Johannesburg",
    "egypt": "Africa/Cairo",
    "nigeria": "Africa/Lagos",
    "kenya": "Africa/Nairobi",
    "morocco": "Africa/Casablanca",
    "argentina": "America/Argentina/Buenos_Aires",
    "chile": "America/Santiago",
    "peru": "America/Lima",
    "colombia": "America/Bogota",
    "philippines": "Asia/Manila",
    "malaysia": "Asia/Kuala_Lumpur",
    "indonesia": "Asia/Jakarta",
    "singapore": "Asia/Singapore",
    "thailand": "Asia/Bangkok",
    "vietnam": "Asia/Ho_Chi_Minh",
    "turkey": "Europe/Istanbul",
    "ukraine": "Europe/Kiev",
    "czech republic": "Europe/Prague",
    "hungary": "Europe/Budapest",
}

# Various alternative expressions and their mapping to timezone identifiers
TIMEZONE_EXPRESSIONS = {
    "eastern": "America/New_York",
    "eastern time": "America/New_York",
    "eastern us": "America/New_York",
    "et": "America/New_York",
    "central": "America/Chicago",
    "central time": "America/Chicago", 
    "central us": "America/Chicago",
    "ct": "America/Chicago",
    "mountain": "America/Denver",
    "mountain time": "America/Denver",
    "mountain us": "America/Denver",
    "mt": "America/Denver",
    "pacific": "America/Los_Angeles", 
    "pacific time": "America/Los_Angeles",
    "pacific us": "America/Los_Angeles",
    "pt": "America/Los_Angeles",
    "western europe": "Europe/Paris",
    "central europe": "Europe/Berlin",
    "eastern europe": "Europe/Kiev",
    "japanese time": "Asia/Tokyo",
    "korea time": "Asia/Seoul",
    "china time": "Asia/Shanghai",
    "australian eastern": "Australia/Sydney",
    "australian western": "Australia/Perth",
    "aest": "Australia/Sydney",
    "aedt": "Australia/Sydney",
    "awst": "Australia/Perth",
    "nz": "Pacific/Auckland",
    "nzt": "Pacific/Auckland",
}


def parse_timezone(timezone_str: str) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Parse a timezone string into a valid IANA timezone identifier.
    
    Args:
        timezone_str: Input timezone string (can be abbreviation, offset, city, etc.)
        
    Returns:
        Tuple of:
        - IANA timezone identifier if successful, None otherwise
        - Error or info message
        - Boolean indicating if timezone was found exactly or if it's a best guess
    """
    if not timezone_str:
        return None, "Please provide a timezone.", False
    
    # Normalize input: lowercase and strip whitespace
    input_str = timezone_str.strip().lower()
    
    # Check if it's directly a valid IANA timezone
    if input_str in pytz.all_timezones_set:
        return input_str, None, True
    
    # Case-insensitive search in IANA timezones
    for tz in pytz.all_timezones:
        if tz.lower() == input_str:
            return tz, None, True
    
    # Check if it's a common abbreviation (case-sensitive)
    if timezone_str.upper() in TIMEZONE_ABBREVIATIONS:
        return TIMEZONE_ABBREVIATIONS[timezone_str.upper()], None, True
    
    # Check if it's a city
    if input_str in CITY_TIMEZONES:
        return CITY_TIMEZONES[input_str], None, True
    
    # Check if it's a country
    if input_str in COUNTRY_TIMEZONES:
        return COUNTRY_TIMEZONES[input_str], None, True
    
    # Check for timezone expressions
    if input_str in TIMEZONE_EXPRESSIONS:
        return TIMEZONE_EXPRESSIONS[input_str], None, True
    
    # Parse UTC/GMT offset
    utc_pattern = re.compile(r'^(utc|gmt)?\s*([+-])?\s*(\d{1,2})(?::(\d{2}))?$', re.IGNORECASE)
    match = utc_pattern.match(input_str)
    
    if match:
        sign = match.group(2) or '+'
        hours = int(match.group(3))
        minutes = int(match.group(4)) if match.group(4) else 0
        
        if hours > 14 or (hours == 14 and minutes > 0) or (sign == '+' and hours == 0 and minutes == 0):
            return None, f"Invalid UTC offset: {timezone_str}. UTC offsets must be between -14:00 and +14:00.", False
        
        if sign == '-':
            hours = -hours
            minutes = -minutes
        
        offset = timedelta(hours=hours, minutes=minutes)
        now = datetime.now(pytz.UTC)
        target_time = now + offset
        
        # Find a timezone with the same offset at the current time
        for tz_name in pytz.all_timezones:
            tz = pytz.timezone(tz_name)
            if tz.utcoffset(now) == offset:
                # Prefer timezones without numbers in their names when possible
                if '/' in tz_name and not any(c.isdigit() for c in tz_name):
                    return tz_name, None, True
        
        # If we couldn't find a nice timezone name, just use Etc/GMT+X or Etc/GMT-X
        # Note: In IANA database, the sign is reversed for Etc/GMT+X format
        if hours == 0 and minutes == 0:
            return "UTC", None, True
        
        # Etc/GMT+X format uses opposite sign (confusingly)
        inv_sign = '-' if sign == '+' else '+'
        if minutes == 0:
            return f"Etc/GMT{inv_sign}{abs(hours)}", None, True
        else:
            # If we have minutes, we'll return UTC but with an explanation
            formatted_offset = f"{sign}{abs(hours):02d}:{abs(minutes):02d}"
            return f"UTC", f"Using UTC with offset {formatted_offset}", True
    
    # Try to find closest match in cities
    city_matches = get_close_matches(input_str, list(CITY_TIMEZONES.keys()), n=1, cutoff=0.8)
    if city_matches:
        closest_city = city_matches[0]
        return CITY_TIMEZONES[closest_city], f"Assuming you meant '{closest_city}'.", False
    
    # Try to find closest match in countries
    country_matches = get_close_matches(input_str, list(COUNTRY_TIMEZONES.keys()), n=1, cutoff=0.8)
    if country_matches:
        closest_country = country_matches[0]
        return COUNTRY_TIMEZONES[closest_country], f"Assuming you meant '{closest_country}'.", False
    
    # Try to find closest match in abbreviations (lowercase for matching)
    abbr_dict_lower = {k.lower(): v for k, v in TIMEZONE_ABBREVIATIONS.items()}
    abbr_matches = get_close_matches(input_str, list(abbr_dict_lower.keys()), n=1, cutoff=0.8)
    if abbr_matches:
        closest_abbr = abbr_matches[0]
        original_abbr = [k for k, v in TIMEZONE_ABBREVIATIONS.items() if k.lower() == closest_abbr][0]
        return abbr_dict_lower[closest_abbr], f"Assuming you meant '{original_abbr}'.", False
    
    # Try to find closest match in expressions
    expr_matches = get_close_matches(input_str, list(TIMEZONE_EXPRESSIONS.keys()), n=1, cutoff=0.8)
    if expr_matches:
        closest_expr = expr_matches[0]
        return TIMEZONE_EXPRESSIONS[closest_expr], f"Assuming you meant '{closest_expr}'.", False
    
    # Try to find closest match in IANA names (can be a bit slow but worth it for precision)
    iana_lower = [tz.lower() for tz in pytz.all_timezones]
    iana_matches = get_close_matches(input_str, iana_lower, n=1, cutoff=0.8)
    if iana_matches:
        closest_iana = iana_matches[0]
        original_iana = [tz for tz in pytz.all_timezones if tz.lower() == closest_iana][0]
        return original_iana, f"Assuming you meant '{original_iana}'.", False
    
    # Nothing found
    return None, f"Could not recognize '{timezone_str}' as a valid timezone. Please use a format like 'America/New_York', 'UTC+1', or a city name like 'London'.", False


def get_current_time(timezone_str: str) -> Tuple[Optional[datetime], Optional[str], Optional[str]]:
    """
    Get the current time in the specified timezone.
    
    Args:
        timezone_str: Input timezone string
        
    Returns:
        Tuple of:
        - datetime object in the specified timezone, or None if invalid
        - The resolved IANA timezone identifier
        - Error message if failed, or info message if timezone was guessed
    """
    iana_timezone, message, exact = parse_timezone(timezone_str)
    
    if not iana_timezone:
        return None, None, message
    
    try:
        timezone = pytz.timezone(iana_timezone)
        current_time = datetime.now(timezone)
        return current_time, iana_timezone, message if not exact else None
    except Exception as e:
        return None, None, f"Error getting time for '{timezone_str}': {str(e)}"


def list_timezone_examples() -> str:
    """Return a string with examples of supported timezone formats"""
    examples = [
        "America/New_York",
        "Europe/London",
        "UTC",
        "UTC+2",
        "GMT-5",
        "EST",
        "PST",
        "CEST", 
        "JST",
        "New York",
        "Tokyo",
        "London",
        "Paris",
        "Eastern Time",
        "Pacific",
        "Germany",
        "Australia"
    ]
    return ", ".join(f"`{ex}`" for ex in examples)