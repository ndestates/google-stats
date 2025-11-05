#!/usr/bin/env python3
"""
Google Stats - A Python application for Google Analytics data processing
"""

import sys
import os

def main():
    """Main entry point for the application."""
    print("Welcome to Google Stats!")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")

if __name__ == "__main__":
    main()