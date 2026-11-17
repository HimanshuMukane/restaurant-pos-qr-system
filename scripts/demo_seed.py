#!/usr/bin/env python3
"""
CLI wrapper: seed (or re-seed) the demo database.

Usage:
    python scripts/demo_seed.py           # always wipes + re-seeds
    python scripts/demo_seed.py --if-empty  # only seeds if DB is empty
"""
import sys
import os

# Make sure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(filename=".env", usecwd=True))

from utils.demo_seed import run_seed

if __name__ == "__main__":
    if_empty = "--if-empty" in sys.argv
    print("Seeding demo data" + (" (skipping if already populated)..." if if_empty else "..."))
    run_seed(if_empty=if_empty)
    print("Done.")
