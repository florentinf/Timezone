#!/usr/bin/env python3
import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the bot
from src.bot import main

if __name__ == "__main__":
    main()