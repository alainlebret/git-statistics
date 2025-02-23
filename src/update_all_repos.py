#!/usr/bin/env python3
"""
update_all_repos.py

This script iterates through each group folder in the specified root directory (e.g., "projects/").
Each group folder is expected to contain one or more repository directories (each with a .git folder).
The script performs a 'git pull' in each repository and optionally shows the output of 'git status'
and a brief log (the last 5 commits) for each repository.

Enhanced output formatting is used to separate information for each group and repository,
making it easier to read when many groups and updates are processed.

Usage:
    python3 update_all_repos.py --root projects --status --log

Arguments:
    --root    : Root directory containing group folders (default: "projects")
    --status  : If set, displays the output of 'git status' after updating.
    --log     : If set, displays the last 5 commits via 'git log -n 5 --oneline'.
"""

import subprocess
import argparse
from pathlib import Path
import logging

# Configure logging to display messages without additional prefixes
logging.basicConfig(level=logging.INFO, format="%(message)s")

def update_repo(repo_path: Path, show_status: bool = False, show_log: bool = False) -> None:
    """
    Updates the Git repository at repo_path by performing 'git pull' and, optionally,
    displays the output of 'git status' and a brief log of the last 5 commits.

    Args:
        repo_path (Path): Path to the Git repository.
        show_status (bool): If True, displays 'git status' output.
        show_log (bool): If True, displays the last 5 commits.
    """
    if not (repo_path / ".git").exists():
        logging.warning(f"{repo_path} is not a Git repository.")
        return

    # Print a clear header for the repository
    header = "=" * 60
    logging.info(f"\n{header}\nRepository: {repo_path}\n{header}")

    # Perform 'git pull'
    try:
        result = subprocess.run(
            ["git", "pull"], cwd=str(repo_path), capture_output=True, text=True, check=True
        )
        logging.info(f"git pull output:\n{result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running git pull in {repo_path}:\n{e.stderr.strip()}")

    # Optionally display 'git status'
    if show_status:
        try:
            status_result = subprocess.run(
                ["git", "status"], cwd=str(repo_path), capture_output=True, text=True, check=True
            )
            logging.info(f"\n--- git status ---\n{status_result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error running git status in {repo_path}:\n{e.stderr.strip()}")

    # Optionally display a brief commit log (last 5 commits)
    if show_log:
        try:
            log_result = subprocess.run(
                ["git", "log", "-n", "5", "--oneline"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=True,
            )
            logging.info(f"\n--- Recent commits ---\n{log_result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error running git log in {repo_path}:\n{e.stderr.strip()}")

def main():
    parser = argparse.ArgumentParser(description="Update all Git repositories in group folders.")
    parser.add_argument("--root", type=str, default="projects", help="Root directory containing group folders.")
    parser.add_argument("--status", action="store_true", help="Show 'git status' after updating each repository.")
    parser.add_argument("--log", action="store_true", help="Show the last 5 commits after updating each repository.")
    args = parser.parse_args()

    root_path = Path(args.root)
    if not root_path.exists():
        logging.error(f"Root directory {root_path} does not exist.")
        return

    # Iterate over each group folder (sorted alphabetically for consistency)
    for group_dir in sorted(root_path.iterdir()):
        if group_dir.is_dir():
            group_header = f"\n{'#' * 60}\nProcessing group: {group_dir.name}\n{'#' * 60}"
            logging.info(group_header)
            # Within each group folder, iterate through potential repository directories (sorted alphabetically)
            for repo_dir in sorted(group_dir.iterdir()):
                if repo_dir.is_dir():
                    update_repo(repo_dir, show_status=args.status, show_log=args.log)

if __name__ == "__main__":
    main()
