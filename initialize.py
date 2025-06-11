#!/usr/bin/env python
"""
Initialization script to download ephemeris files required by the application.
Run this script before deploying to Azure or after installing dependencies locally.
"""

import os
import sys
import logging
from skyfield.api import load

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Download the required ephemeris files.
    """
    logging.info("Starting initialization process...")
    
    # Create data directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Try to download the more precise DE440 ephemeris
    try:
        logging.info("Downloading DE440 ephemeris...")
        eph_de440 = load('de440.bsp')
        logging.info(f"DE440 downloaded successfully. Objects available: {len(eph_de440)}")
    except Exception as e:
        logging.warning(f"Failed to download DE440: {str(e)}. Falling back to DE421.")
        try:
            # Fall back to DE421 if DE440 fails
            logging.info("Downloading DE421 ephemeris...")
            eph_de421 = load('de421.bsp')
            logging.info(f"DE421 downloaded successfully. Objects available: {len(eph_de421)}")
        except Exception as e2:
            logging.error(f"Failed to download ephemeris: {str(e2)}")
            return 1
    
    # Download Hipparcos star catalog for constellation calculations
    try:
        logging.info("Downloading Hipparcos star catalog...")
        hip = load('hipparcos')
        logging.info(f"Star catalog downloaded successfully. Stars available: {len(hip)}")
    except Exception as e:
        logging.warning(f"Failed to download star catalog: {str(e)}. This may affect constellation calculations.")
    
    logging.info("Initialization completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 