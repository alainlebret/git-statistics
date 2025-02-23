#!/usr/bin/env python3
"""
config.py

This module handles command-line argument parsing, configuration file loading,
and date format validation for the Git Project Statistics tool.

The configuration file has a JSON format, and it should include keys such as:
  - "excluded_members": a list of user names to be excluded from analysis (e.g. the instructor).
  - "alias_mapping_by_group": a dictionary mapping group names to alias dictionaries.
  - "fixed_project_start_date" (optional): the start date for the project analysis, e.g., "2025-02-1".

Usage:
  Import the functions from this module in your main application.
  Example:
    from config import parse_arguments, load_config, validate_date_format

Author: Alain Lebret, 2024-2025
License: MIT License
"""

import argparse
import json
import logging
from datetime import datetime

def parse_arguments():
    """
    Parse the command-line arguments.

    Returns:
        argparse.Namespace: The namespace containing all parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Analyze git repositories with a full history since the project start."
    )
    parser.add_argument(
        '--student-folders', type=str, default='fake_project_example',
        help="Directory containing students' projects."
    )
    parser.add_argument(
        '--output-csv', type=str, default='total_member_volumes.csv',
        help="CSV for global statistics."
    )
    parser.add_argument(
        '--daily-csv', type=str, default='daily_stats.csv',
        help="CSV for daily statistics."
    )
    parser.add_argument(
        '--target-date', type=str, default='2025-02-1',
        help="Target date (YYYY-MM-DD) from which to start analysis."
    )
    parser.add_argument(
        '--analysis-days', type=int, default=10,
        help="Number of days to analyze after the target date."
    )
    parser.add_argument(
        '--low-threshold', type=int, default=10,
        help="Low activity threshold."
    )
    parser.add_argument(
        '--medium-threshold', type=int, default=30,
        help="Medium activity threshold."
    )
    parser.add_argument(
        '--high-threshold', type=int, default=100,
        help="High activity threshold."
    )
    parser.add_argument(
        '--top-n', type=int, default=4,
        help="Max number of members per subplot for daily charts."
    )
    parser.add_argument(
        '--project-name', type=str, default='XXX',
        help="Project name for PDF titles."
    )
    parser.add_argument(
        '--config-file', type=str, default='sample_config.json',
        help="Path to the JSON configuration file."
    )
    return parser.parse_args()

def load_config(config_file_path):
    """
    Load the configuration file in JSON format.

    Args:
        config_file_path (str): Path to the configuration file.

    Returns:
        dict: The loaded configuration as a dictionary. Returns an empty dictionary if loading fails.
    """
    try:
        with open(config_file_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
            return config
    except Exception as e:
        logging.error(f"Error loading config file {config_file_path}: {e}")
        return {}

def validate_date_format(date_str):
    """
    Validate that the date string follows the YYYY-MM-DD format and return a datetime object.

    Args:
        date_str (str): The date string to validate.

    Returns:
        datetime: The corresponding datetime object.

    Raises:
        ValueError: If the date_str does not match the expected format.
    """
    return datetime.strptime(date_str, "%Y-%m-%d")
