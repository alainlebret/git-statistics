#!/usr/bin/env python3
"""
main.py

Git Project Statistics - Main entry point

This script analyzes git repositories (for example from student projects) to generate detailed statistics
about commits, code insertions/deletions, and activity per group member. It produces CSV files for
global and daily statistics, as well as PDF reports (summary table, activity histogram, balance report,
and daily charts).

Usage:
  python3 main.py --student-folders path/to/student_projects --target-date YYYY-MM-DD [other options]

Configuration:
  - The JSON configuration file (specified using --config-file) contains:
    - alias_mapping_by_group: mapping of author aliases per group
    - excluded_members: list of users to exclude from analysis
    - fixed_project_start_date (optional): the start date for the project analysis

Prerequisites:
  - Python 3.6 or higher
  - GitPython and Matplotlib libraries

Author: Alain Lebret, 2024-2025
License: MIT License - See LICENSE file
"""

from datetime import datetime
import logging

from config import parse_arguments, load_config, validate_date_format
from utils import map_alias_to_name
from report_generator import (
    write_volumes_to_csv,
    read_volumes,
    read_daily_volumes,
    calculate_balance_indicators,
    generate_summary_table,
    generate_activity_histogram,
    generate_balance_report,
    generate_daily_charts
)

def main():
    """
    Main function that realizes the analysis:
      - Parses command-line arguments and loads configuration.
      - Sets up project start and target dates.
      - Generates CSV files from git repository statistics.
      - Reads the CSV data and computes indicators.
      - Generates PDF reports with summary, histogram, balance, and daily charts.
    """
    # Parse command-line arguments and load the configuration JSON file.
    args = parse_arguments()
    config = load_config(args.config_file)

    # Retrieve alias mapping and exclusion list from config.
    alias_mapping_by_group = config.get("alias_mapping_by_group", {})
    excluded_members = config.get("excluded_members", [])

    # Determine the fixed project start date (default: 2025-02-1)
    fixed_project_start_date = datetime(2025, 2, 1)
    if "fixed_project_start_date" in config:
        try:
            fixed_project_start_date = datetime.strptime(config["fixed_project_start_date"], "%Y-%m-%d")
        except ValueError:
            logging.warning(f"Invalid fixed_project_start_date in config: {config['fixed_project_start_date']}")

    # Validate and set the target date for analysis.
    try:
        target_date = validate_date_format(args.target_date)
    except ValueError:
        print("Error: Invalid date format. Use YYYY-MM-DD.")
        return

    # Generate CSV files based on the git repository analysis.
    write_volumes_to_csv(
        student_folders=args.student_folders,
        output_csv=args.output_csv,
        daily_csv=args.daily_csv,
        target_date=target_date,
        analysis_days=args.analysis_days,
        fixed_project_start_date=fixed_project_start_date,
        excluded_members=excluded_members,
        alias_mapping_by_group=alias_mapping_by_group,
        map_alias_func=map_alias_to_name
    )

    # Get statistics from the generated CSV files.
    volume_data = read_volumes(args.output_csv)
    balance_data = calculate_balance_indicators(volume_data)
    daily_data = read_daily_volumes(args.daily_csv)

    # Generate PDF reports.
    generate_summary_table(volume_data, balance_data, 
                           filename='summary_table.pdf',
                           low=args.low_threshold, 
                           medium=args.medium_threshold,
                           high=args.high_threshold)
    generate_activity_histogram(volume_data, filename='activity_histogram.pdf')
    generate_balance_report(balance_data, filename='balance_report.pdf')
    generate_daily_charts(
        daily_data,
        target_date,
        args.analysis_days,
        top_n=args.top_n,
        filename='daily_charts.pdf',
        project_name=args.project_name,
        fixed_project_start_date=fixed_project_start_date
    )

    print("Analysis complete. The results (CSV & PDF) are available in the specified files.")


if __name__ == "__main__":
    main()
