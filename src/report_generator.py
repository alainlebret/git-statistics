#!/usr/bin/env python3
"""
report_generator.py

This module generates CSV files and PDF reports from git repository statistics.
It produces global statistics (aggregated per group and member) as well as daily statistics,
and creates several PDF reports:
  - Summary table
  - Activity histogram
  - Balance report
  - Daily charts

Usage:
    Import the functions from this module in your main application.
    Example:
        from report_generator import write_volumes_to_csv, generate_summary_table, ...
        
Author: Alain Lebret, 2024-2025
License: MIT License
"""

import os
import csv
import logging
from datetime import timedelta
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def write_volumes_to_csv(student_folders, output_csv, daily_csv, target_date, analysis_days, 
                         fixed_project_start_date, excluded_members, alias_mapping_by_group, map_alias_func):
    """
    Generate CSV files containing global and daily statistics based on Git repository analysis.
    The folder name is used as the group label.

    Args:
        student_folders (str): Path to the directory containing student project folders.
        output_csv (str): File path for the global statistics CSV.
        daily_csv (str): File path for the daily statistics CSV.
        target_date (datetime): The target date for the analysis.
        analysis_days (int): Number of days to analyze after the target date.
        fixed_project_start_date (datetime): The start date for the project.
        excluded_members (list): List of author names to be excluded.
        alias_mapping_by_group (dict): Mapping of group labels to alias dictionaries.
        map_alias_func (callable): Function to map an author name to its unified alias.

    Returns:
        None
    """
    # Compute the end date and build a list of dates for the analysis period.
    end_date = target_date + timedelta(days=analysis_days)
    date_list = [fixed_project_start_date + timedelta(days=i)
                 for i in range((end_date - fixed_project_start_date).days)]

    # Open CSV files for writing global and daily statistics.
    with open(output_csv, mode='w', newline='', encoding='utf-8') as file_global, \
         open(daily_csv, mode='w', newline='', encoding='utf-8') as file_daily:
        writer_global = csv.writer(file_global)
        writer_daily = csv.writer(file_daily)

        # Write headers.
        writer_global.writerow(["Group", "Member", "Added rows", "Removed rows", "Total commits", "Active days"])
        writer_daily.writerow(["Group", "Member", "Date", "Added rows (day)", "Removed rows (day)", "Commits (day)"])

        student_folders_path = Path(student_folders)
        for student_dir in student_folders_path.iterdir():
            if student_dir.is_dir():
                # Each folder represents a group.
                git_dirs = [d for d in student_dir.iterdir() if d.is_dir()]
                if not git_dirs:
                    continue
                group_label = student_dir.name
                git_repo_path = git_dirs[0]  # Use the first subdirectory as the git repository.

                # Import the git_analyzer function here to avoid circular imports.
                from git_analyzer import collect_changes_by_group
                changes_by_group = collect_changes_by_group(
                    repo_path=str(git_repo_path),
                    group_label=group_label,
                    excluded=excluded_members,
                    start_date=fixed_project_start_date,
                    end_date=end_date,
                    alias_mapping_by_group=alias_mapping_by_group,
                    map_alias_func=map_alias_func
                )

                if not changes_by_group or group_label not in changes_by_group:
                    logging.info(f"No data found for {group_label} in {git_repo_path}")
                    continue

                sub_dict = changes_by_group[group_label]
                for member, changes in sub_dict.items():
                    total_commits = sum(changes['daily_commits'].values())
                    writer_global.writerow([
                        group_label, member,
                        changes['insertions'], changes['deletions'],
                        total_commits, changes['active_days']
                    ])

                    # Write daily data for each date in the analysis period.
                    for day in date_list:
                        day_str = day.strftime('%Y-%m-%d')
                        day_inserts = changes['daily_insertions'].get(day_str, 0)
                        day_delets = changes['daily_deletions'].get(day_str, 0)
                        day_commits = changes['daily_commits'].get(day_str, 0)
                        writer_daily.writerow([
                            group_label, member, day_str,
                            day_inserts, day_delets, day_commits
                        ])

def read_volumes(csv_file):
    """
    Read the global statistics from a CSV file.

    Args:
        csv_file (str): Path to the global statistics CSV file.

    Returns:
        dict: A dictionary with the global statistics data.
    """
    data = defaultdict(dict)
    with open(csv_file, newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # We skip header
        for row in reader:
            group, member, insertions, deletions, total_commits, active_days = row
            data[group][member] = {
                'insertions': int(insertions),
                'deletions': int(deletions),
                'total_commits': int(total_commits),
                'active_days': int(active_days)
            }
    return data

def read_daily_volumes(daily_csv):
    """
    Read the daily statistics from a CSV file.

    Args:
        daily_csv (str): Path to the daily statistics CSV file.

    Returns:
        dict: A dictionary with the daily statistics data.
    """
    data = defaultdict(lambda: defaultdict(dict))
    with open(daily_csv, newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            group, member, date_str, inserts, delets, commits = row
            data[group][member][date_str] = {
                'insertions': int(inserts),
                'deletions': int(delets),
                'commits': int(commits)
            }
    return data

def calculate_balance_indicators(data):
    """
    Calculate balance indicators for each group, determining the dominant member.

    Args:
        data (dict): The global statistics data.

    Returns:
        dict: A dictionary with balance indicators per group.
    """
    balance = {}
    for group, members in data.items():
        total_commits = sum(m['total_commits'] for m in members.values())
        if total_commits > 0:
            max_commits = max(m['total_commits'] for m in members.values())
            for mem, val in members.items():
                if val['total_commits'] == max_commits:
                    balance[group] = {
                        'dominant_ratio': max_commits / total_commits,
                        'dominant_member': mem
                    }
                    break
        else:
            balance[group] = {
                'dominant_ratio': 0,
                'dominant_member': None
            }
    return balance

def generate_summary_table(data, balance, filename='summary_table.pdf', low=10, medium=30, high=100):
    """
    Generate a PDF summary table of global statistics with color-coded cells.

    Args:
        data (dict): Global statistics data.
        balance (dict): Balance indicators for each group.
        filename (str, optional): Output filename for the PDF. Defaults to 'summary_table.pdf'.
        low (int, optional): Low activity threshold (default: 10).
        medium (int, optional): Medium activity threshold (default: 30).
        high (int, optional): High activity threshold (default: 100).

    Returns:
        None
    """
    with PdfPages(filename) as pdf:
        pdf.infodict()['Title'] = "Summary table"
        fig, ax = plt.subplots(figsize=(8.27, 11.69))
        ax.axis('off')
        rows = []
        header = ['Group', 'Member', 'Insertions', 'Deletions', 'Total commits', 'Active days', 'Dominant ratio']
        # Build table rows.
        for group, members in data.items():
            group_balance = balance.get(group, {'dominant_ratio': 0})
            ratio = f"{group_balance['dominant_ratio']*100:.1f}%" if group_balance['dominant_ratio'] else 'N/A'
            for member, stats in members.items():
                rows.append([
                    group, member,
                    stats['insertions'], stats['deletions'],
                    stats['total_commits'], stats['active_days'],
                    ratio
                ])
        if not rows:
            logging.info("No rows found. Skipping summary table.")
            return

        # Create table.
        table = ax.table(cellText=rows, colLabels=header, loc='center', cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.auto_set_column_width(list(range(len(header))))

        # Color coding for insertions and deletions columns.
        for (row_idx, col_idx), cell in table.get_celld().items():
            if row_idx == 0:
                cell.set_facecolor('#DDDDDD')
            else:
                if col_idx in [2, 3]:
                    val = int(rows[row_idx - 1][col_idx])
                    if val >= high:
                        cell.set_facecolor('#ff9999')
                    elif val >= medium:
                        cell.set_facecolor('#b3ffb3')
                    elif val >= low:
                        cell.set_facecolor('#ffffcc')
        pdf.savefig(fig)
        plt.close(fig)

def generate_activity_histogram(data, filename='activity_histogram.pdf'):
    """
    Generate a PDF histogram indicating total commits per group and member.

    Args:
        data (dict): Global statistics data.
        filename (str, optional): Output filename for the PDF. Defaults to 'activity_histogram.pdf'.

    Returns:
        None
    """
    with PdfPages(filename) as pdf:
        pdf.infodict()['Title'] = "Activity histogram"
        groups = sorted(data.keys())
        fig, ax = plt.subplots(figsize=(8, len(groups)*0.5+2))
        y_positions, heights, labels = [], [], []
        y_pos = 0
        # Build data for histogram.
        for group in groups:
            for member, stats in data[group].items():
                labels.append(f"{group} - {member}")
                heights.append(stats['total_commits'])
                y_positions.append(y_pos)
                y_pos += 1
        ax.barh(y_positions, heights, color='#89CFF0')
        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel("Total commits on period")
        ax.set_title("Histogram of commits per group and member")
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

def generate_balance_report(balance, filename='balance_report.pdf'):
    """
    Generate a PDF balance report showing the dominant member for each group.

    Args:
        balance (dict): Balance indicators per group.
        filename (str, optional): Output filename for the PDF (default: 'balance_report.pdf').

    Returns:
        None
    """
    with PdfPages(filename) as pdf:
        pdf.infodict()['Title'] = "Balance report"
        fig, ax = plt.subplots(figsize=(8, 11))
        ax.axis('off')
        rows = []
        header = ["Group", "Dominant member", "Dominant ratio (%)"]
        for group, info in balance.items():
            ratio_str = f"{info['dominant_ratio']*100:.1f}%" if info['dominant_member'] else "N/A"
            rows.append([group, info['dominant_member'], ratio_str])
        if not rows:
            logging.info("No rows found. Skipping balance report.")
            return
        table = ax.table(cellText=rows, colLabels=header, loc='center', cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.auto_set_column_width([0, 1, 2])
        pdf.savefig(fig)
        plt.close(fig)

def generate_daily_charts(daily_data, target_date, analysis_days, top_n=5,
                               filename='daily_charts.pdf', project_name="XXX", fixed_project_start_date=None):
    """
    Generate a multi-page PDF containing daily charts for commit activity.
    Each chart displays the daily commit counts for up to top_n members of a group.

    Args:
        daily_data (dict): Daily statistics data.
        target_date (datetime): The target date for the analysis.
        analysis_days (int): Number of days to analyze after the target date.
        top_n (int, optional): Number of top members per chart (default: 5).
        filename (str, optional): Output filename for the PDF (default: 'daily_charts.pdf').
        project_name (str, optional): Name of the project for report title (default to "XXX").
        fixed_project_start_date (datetime, optional): Start date for the analysis (default to target_date if not provided).

    Returns:
        None
    """
    if fixed_project_start_date is None:
        fixed_project_start_date = target_date  # Fallback to target_date if not specified.

    end_date = target_date + timedelta(days=analysis_days)
    total_days = (end_date - fixed_project_start_date).days
    date_list = [fixed_project_start_date + timedelta(days=i) for i in range(total_days)]
    date_str_list = [d.strftime('%Y-%m-%d') for d in date_list]

    # Determine the index corresponding to the first date after the target date.
    target_index = next((i for i, d in enumerate(date_list) if d > target_date), len(date_list))

    cmap = plt.cm.get_cmap('tab10')
    subplots_to_draw = []
    # Flatten daily data into subplots per group.
    for group, members_data in daily_data.items():
        member_totals = []
        for member, days_dict in members_data.items():
            total_commits = sum(v['commits'] for v in days_dict.values())
            member_totals.append((member, total_commits))
        member_totals.sort(key=lambda x: x[1], reverse=True)
        start_idx = 0
        while start_idx < len(member_totals):
            subset = member_totals[start_idx:start_idx + top_n]
            subset_data = []
            for i_color, (member, _) in enumerate(subset):
                # Build a list of commit counts for each day in the period.
                commits_list = [members_data[member].get(ds, {}).get('commits', 0) for ds in date_str_list]
                commits_before = commits_list[:target_index]
                commits_after = commits_list[target_index:]
                subset_data.append({
                    'member': member,
                    'commits_before': commits_before,
                    'commits_after': commits_after,
                    'color': cmap(i_color % 10)
                })
            subplots_to_draw.append((group, start_idx, subset_data))
            start_idx += top_n

    with PdfPages(filename) as pdf:
        pdf.infodict()['Title'] = f"Statistics of project {project_name} - {target_date.strftime('%Y-%m-%d')}"
        # 4 subplots per page max.
        for page_index in range(0, len(subplots_to_draw), 4):
            fig, axes = plt.subplots(2, 2, figsize=(11.69, 8.27))
            axes = axes.flatten()
            subset_page = subplots_to_draw[page_index:page_index + 4]
            for ax_idx, (group, start_idx, subset_data) in enumerate(subset_page):
                ax = axes[ax_idx]
                ax.grid(True, which='major', linestyle='--', alpha=0.5)
                title_sub = f"{group} - {start_idx+len(subset_data)} active member(s)"
                ax.set_title(title_sub, fontsize=10)
                for data_member in subset_data:
                    member = data_member['member']
                    color = data_member['color']
                    commits_before = data_member['commits_before']
                    commits_after = data_member['commits_after']
                    label_given = False
                    # Plot commit data before the target date.
                    if any(c > 0 for c in commits_before):
                        ax.plot(date_str_list[:target_index],
                                commits_before,
                                marker='o',
                                label=member,
                                alpha=0.7,
                                linewidth=1,
                                color=color)
                        label_given = True
                    # Plot commit data after the target date.
                    if any(c > 0 for c in commits_after):
                        ax.plot(date_str_list[target_index:],
                                commits_after,
                                marker='o',
                                label=member if not label_given else None,
                                alpha=0.4,
                                linewidth=1,
                                color='grey')
                ax.set_xticks(date_str_list)
                ax.set_xticklabels(date_str_list, rotation=45, ha='right', fontsize=7)
                ax.set_ylabel("Commits / day", fontsize=8)
                _, labels = ax.get_legend_handles_labels()
                if labels:
                    ax.legend(fontsize=6, loc='upper left')
            # Hide unused subplots on the page.
            for empty_ax in axes[len(subset_page):]:
                empty_ax.axis('off')
            date_str = target_date.strftime('%Y-%m-%d')
            fig.suptitle(f"Daily commits (until {date_str}) - page {page_index//4 + 1}",
                         fontsize=12, fontweight='bold')
            plt.tight_layout(rect=[0, 0, 1, 0.97])
            pdf.savefig(fig)
            plt.close(fig)
