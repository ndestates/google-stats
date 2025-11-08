#!/usr/bin/env python3
"""
Google Stats - Main entry point for analytics scripts
"""

import sys
import os

def main():
    """Main entry point for the application."""
    print("🚀 Google Stats - GA4 Analytics Tool")
    print("=" * 50)
    print("Available scripts:")
    print("  • Yesterday Report: python -m scripts.yesterday_report")
    print("  • Monthly Report: python -m scripts.all_pages_sources_report")
    print("  • Top Pages: python -m scripts.get_top_pages")
    print("  • Google Ads Performance: python -m scripts.google_ads_performance")
    print("  • Social Media Timing: python -m scripts.social_media_timing")
    print()
    print(f"Reports are saved to: {os.path.join(os.path.dirname(__file__), 'reports')}")
    print(f"Python version: {sys.version}")

if __name__ == "__main__":
    main()