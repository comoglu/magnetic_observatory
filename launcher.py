#!/usr/bin/env python3
"""
Launcher script for the Magnetic Observatory Data Viewer application.
Provides command-line options for configuration and debugging.
"""

import sys
import os
import argparse
import logging
from datetime import datetime

def setup_logging(debug_mode: bool):
    """Configure application logging"""
    log_dir = os.path.join(os.path.expanduser('~'), '.magnetic_observatory', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(
        log_dir, 
        f'magnetic_observatory_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    )
    
    # Configure logging format and level
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    # Set up file handler
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Magnetic Observatory Data Viewer'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with detailed logging'
    )
    
    parser.add_argument(
        '--style',
        choices=['fusion', 'windows', 'macos'],
        help='Set the application style'
    )
    
    return parser.parse_args()

def main():
    """Main launcher entry point"""
    try:
        # Parse command-line arguments
        args = parse_arguments()
        
        # Set up logging
        setup_logging(args.debug)
        
        # Log startup information
        logging.info("Starting Magnetic Observatory Data Viewer")
        logging.debug(f"Python version: {sys.version}")
        logging.debug(f"Command line arguments: {sys.argv}")
        
        # Configure environment
        os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
        
        if args.debug:
            os.environ['QT_DEBUG_PLUGINS'] = '1'
        
        # Import and start the application
        from magnetic_observatory.main import main as app_main
        
        # Set application style if specified
        if args.style:
            from PyQt5.QtWidgets import QApplication
            QApplication.setStyle(args.style)
        
        # Run the application
        app_main()
        
    except Exception as e:
        logging.error(f"Failed to start application: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()