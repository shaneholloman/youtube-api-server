#!/usr/bin/env python3
"""
Simple Environment Variable Checker for YouTube API Server
"""

import os


def load_env_file():
    """
    Check environment variables from os.environ.
    This function maintains compatibility with the existing main.py import.
    """
    required_vars = [
        'WEBSHARE_PROXY'
    ]

    optional_vars = [
        'HOST',
        'PORT',
        'WEBSHARE_PROXY_LOCATIONS'
    ]

    print("Checking environment variables...")

    # Check required variables
    missing_required = []
    for var in required_vars:
        if os.getenv(var):
            print(f"✓ {var}: Set")
        else:
            print(f"✗ {var}: Not Set")
            missing_required.append(var)

    # Check optional variables
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: Set")
        else:
            print(f"- {var}: Not Set (optional)")

    if missing_required:
        print(f"WARNING: Missing required variables: {', '.join(missing_required)}")
        print("The server will work without proxy but may face IP blocking")
    else:
        print("✓ All required variables are set!")


if __name__ == "__main__":
    load_env_file()
