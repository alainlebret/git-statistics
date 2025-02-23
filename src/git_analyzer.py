#!/usr/bin/env python3
"""
git_analyzer.py

This module provides functionality to analyze git repositories and collect
commit statistics for a specified time period. The main function, 
`collect_changes_by_group`, aggregates data by group and by unified author name,
including counts of daily commits, insertions, deletions, and active days.

Usage:
    from git_analyzer import collect_changes_by_group
    changes = collect_changes_by_group(
                 repo_path, group_label, excluded, start_date, end_date,
                 alias_mapping_by_group, map_alias_func
             )

Author: Alain Lebret, 2024-2025
License: MIT License
"""

import os
import git
import logging
from datetime import datetime
from collections import defaultdict, Counter

def collect_changes_by_group(repo_path, group_label, excluded, start_date, end_date, alias_mapping_by_group, map_alias_func):
    """
    Analyze a git repository and return a nested dictionary containing commit statistics,
    grouped by group label and unified author names.

    The function iterates over all local branches and remote branches (from the "origin" remote
    if available) and collects statistics for commits made within the period [start_date, end_date).

    Args:
        repo_path (str): Path to the git repository.
        group_label (str): Label representing the group for which statistics are collected.
        excluded (list): List of author names to exclude (case-insensitive).
        start_date (datetime): Start date of the analysis period.
        end_date (datetime): End date of the analysis period.
        alias_mapping_by_group (dict): Dictionary mapping group labels to dictionaries of author aliases.
        map_alias_func (function): Function that maps an author name to a unified alias given the group and mapping.

    Returns:
        dict: A nested dictionary structured as:
              { group_label: { unified_author: {
                    'insertions': int,
                    'deletions': int,
                    'daily_commits': Counter(),
                    'daily_insertions': Counter(),
                    'daily_deletions': Counter(),
                    'active_days': int
                } } }
    """
    # Verify that the repository contains a .git folder.
    if not os.path.isdir(os.path.join(repo_path, '.git')):
        return {}

    try:
        repo = git.Repo(repo_path)
    except Exception as e:
        logging.warning(f"Unable to open repository {repo_path}: {e}")
        return {}

    # Attempt to fetch remote updates from the "origin" remote if available.
    try:
        repo.remotes.origin.fetch()
    except Exception:
        pass

    # Initialize the nested dictionary to store changes per group and per unified author.
    changes_by_group = defaultdict(lambda: defaultdict(lambda: {
        'insertions': 0,
        'deletions': 0,
        'daily_commits': Counter(),
        'daily_insertions': Counter(),
        'daily_deletions': Counter(),
        'active_days': 0
    }))

    # Gather all branches: local branches plus remote branches from origin if available.
    all_branches = list(repo.branches)
    if repo.remotes:
        try:
            origin = repo.remotes["origin"]
        except Exception:
            origin = repo.remotes[0]
        all_branches += list(origin.refs)

    # Iterate over each branch to process commits.
    for branch in all_branches:
        try:
            # Iterate through all commits in the branch.
            for commit in repo.iter_commits(branch):
                commit_date = datetime.fromtimestamp(commit.committed_date)
                # Only consider commits within the specified date range.
                if not (start_date <= commit_date < end_date):
                    continue

                # Normalize author name and check if it should be excluded.
                author_raw = commit.author.name.strip().lower()
                if author_raw in map(str.lower, excluded):
                    continue

                # Map the raw author name to a unified alias using the provided function.
                unified_name = map_alias_func(author_raw, group_label, alias_mapping_by_group)
                stats = commit.stats.total  # Commit statistics (insertions, deletions, etc.)
                day_str = commit_date.strftime('%Y-%m-%d')

                # Update the counters for the corresponding unified author.
                ch = changes_by_group[group_label][unified_name]
                ch['daily_commits'][day_str] += 1
                ch['daily_insertions'][day_str] += stats.get('insertions', 0)
                ch['daily_deletions'][day_str] += stats.get('deletions', 0)
        except Exception as e:
            logging.warning(f"Error on branch {branch} in {repo_path}: {e}")

    # Summarize totals for each author: compute overall insertions, deletions, and active days.
    for grp in changes_by_group:
        for member, data in changes_by_group[grp].items():
            data['insertions'] = sum(data['daily_insertions'].values())
            data['deletions'] = sum(data['daily_deletions'].values())
            data['active_days'] = sum(1 for _, count in data['daily_commits'].items() if count > 0)

    return changes_by_group
