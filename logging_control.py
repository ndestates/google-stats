#!/usr/bin/env python3
"""
Logging Control Script
Easily turn logging on/off and change log levels for debugging
"""

import os
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def update_env_file(log_level, web_log_level=None, env_file_path=None):
    """Update the .env file with new logging levels"""
    if env_file_path is None:
        env_file = Path.cwd() / '.env'
    else:
        env_file = Path(env_file_path)

    if not env_file.exists():
        print(f"❌ .env file not found at {env_file}")
        return False

    # Read current content
    content = env_file.read_text()

    # Update LOG_LEVEL
    import re
    if re.search(r'^LOG_LEVEL=', content, re.MULTILINE):
        content = re.sub(r'^LOG_LEVEL=.*$', f'LOG_LEVEL={log_level}', content, flags=re.MULTILINE)
    else:
        content += f"\nLOG_LEVEL={log_level}"

    # Update WEB_LOG_LEVEL if specified
    if web_log_level:
        if re.search(r'^WEB_LOG_LEVEL=', content, re.MULTILINE):
            content = re.sub(r'^WEB_LOG_LEVEL=.*$', f'WEB_LOG_LEVEL={web_log_level}', content, flags=re.MULTILINE)
        else:
            content += f"\nWEB_LOG_LEVEL={web_log_level}"

    # Write back to file
    env_file.write_text(content)
    return True

def show_current_levels():
    """Show current logging levels"""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    web_log_level = os.getenv('WEB_LOG_LEVEL', os.getenv('LOG_LEVEL', 'INFO'))

    print("📊 Current Logging Configuration:")
    print(f"   Python scripts (LOG_LEVEL): {log_level}")
    print(f"   Web interface (WEB_LOG_LEVEL): {web_log_level}")
    print()
    print("📁 Log files location: logs/")
    print("   - web_interface.log (PHP web interface)")
    print("   - *.log (individual Python scripts)")

def main():
    parser = argparse.ArgumentParser(
        description='Control logging levels for Google Stats debugging',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show current logging levels
  python logging_control.py --show

  # Turn off all logging
  python logging_control.py --level OFF

  # Enable debug logging for troubleshooting
  python logging_control.py --level DEBUG

  # Set different levels for web vs scripts
  python logging_control.py --level INFO --web-level WARNING

Available log levels:
  DEBUG    - Detailed debugging information
  INFO     - General information (default)
  WARNING  - Warning messages only
  ERROR    - Error messages only
  CRITICAL - Critical errors only
  OFF      - Disable all logging
        """
    )

    parser.add_argument('--level', '-l',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'OFF'],
                       help='Set logging level for Python scripts')

    parser.add_argument('--web-level', '-w',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'OFF'],
                       help='Set logging level for web interface (defaults to same as --level)')

    parser.add_argument('--show', '-s', action='store_true',
                       help='Show current logging configuration')

    parser.add_argument('--off', action='store_true',
                       help='Turn off all logging (same as --level OFF)')

    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging (same as --level DEBUG)')

    args = parser.parse_args()

    if args.show or len(sys.argv) == 1:
        show_current_levels()
        return

    # Handle convenience flags
    if args.off:
        level = 'OFF'
    elif args.debug:
        level = 'DEBUG'
    else:
        level = args.level

    web_level = args.web_level or level

    # Update .env file
    if update_env_file(level, web_level):
        print(f"✅ Logging levels updated:")
        print(f"   Python scripts: {level}")
        print(f"   Web interface: {web_level}")
        print()
        print("🔄 Restart any running processes for changes to take effect:")
        print("   - Web interface: Restart web server or PHP process")
        print("   - Python scripts: Run new instances")
        print()
        print("📁 Log files are located in the 'logs/' directory")
    else:
        print("❌ Failed to update logging configuration")
        sys.exit(1)

if __name__ == '__main__':
    main()