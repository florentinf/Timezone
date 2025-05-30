#!/usr/bin/env python3
"""
Timezone Bot Examples Script

This script demonstrates the various timezone formats supported by the Timezone Bot.
Run it to see how different formats are parsed and converted to standard IANA timezone identifiers.
"""

import sys
import os
from datetime import datetime

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our timezone parser
from src.utils.timezone_parser import parse_timezone, get_current_time

def display_timezone_example(input_str):
    """Display how a timezone string is parsed"""
    print(f"\nInput: '{input_str}'")
    print("-" * 40)
    
    tz_id, message, exact = parse_timezone(input_str)
    if tz_id:
        current_time, _, _ = get_current_time(tz_id)
        formatted_time = current_time.strftime('%I:%M %p, %A, %b %d') if current_time else "Unknown"
        
        print(f"✓ Valid timezone: {tz_id}")
        print(f"  Current time:   {formatted_time}")
        if message:
            print(f"  Note:          {message}")
    else:
        print(f"✗ Invalid timezone: {message}")

def main():
    """Show examples of different timezone formats"""
    print("\n=== TIMEZONE BOT EXAMPLES ===\n")
    print("This script demonstrates the various timezone formats supported by the bot.\n")
    
    examples = [
        # IANA Timezone Formats
        "America/New_York",
        "Europe/London",
        "Asia/Tokyo",
        "Australia/Sydney",
        
        # Abbreviations
        "EST",
        "PST",
        "CEST",
        "JST",
        "GMT",
        "UTC",
        
        # UTC/GMT Offsets
        "UTC+2",
        "GMT-5",
        "UTC+5:30",
        "UTC-3:30",
        "UTC0",
        "+8",
        "-4",
        
        # City Names
        "New York",
        "London",
        "Tokyo",
        "Sydney",
        "Paris",
        "Berlin",
        "Moscow",
        "Beijing",
        
        # Country Names
        "USA",
        "UK",
        "Japan",
        "Australia",
        "Germany",
        "France",
        "India",
        
        # Natural Language
        "Eastern Time",
        "Pacific",
        "Central Europe",
        "Mountain Time",
        
        # Close matches and typos (to demonstrate fuzzy matching)
        "NewYork",
        "Lundon",
        "Tokkyo",
        "Sydny",
        "Paciffic",
        
        # Invalid inputs
        "Not a timezone",
        "UTC+25",  # Invalid offset
    ]
    
    for example in examples:
        display_timezone_example(example)
    
    print("\n=== Custom Input ===")
    while True:
        user_input = input("\nEnter a timezone to test (or 'q' to quit): ")
        if user_input.lower() in ('q', 'quit', 'exit'):
            break
        display_timezone_example(user_input)

if __name__ == "__main__":
    main()