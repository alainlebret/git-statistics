import os
import tempfile
import git
from datetime import datetime, timedelta
from git_analyzer import collect_changes_by_group
from utils import map_alias_to_name

def create_temp_git_repo(repo_dir, author_name="user1"):
    """
    Create a temporary Git repository with one commit.
    """
    repo = git.Repo.init(repo_dir)
    file_path = os.path.join(repo_dir, "file.txt")
    with open(file_path, "w") as f:
        f.write("Initial content\n")
    repo.index.add(["file.txt"])
    repo.index.commit("Initial commit", author=git.Actor(author_name, f"{author_name}@example.com"))
    return repo

def test_collect_changes_by_group(tmp_path):
    # Create a temporary Git repository.
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    create_temp_git_repo(str(repo_dir), author_name="user1")
    now = datetime.now()
    start_date = now - timedelta(days=1)
    end_date = now + timedelta(days=1)
    alias_mapping = {"group1": {"user1": "User One"}, "global": {}}
    changes = collect_changes_by_group(
        repo_path=str(repo_dir),
        group_label="group1",
        excluded=[],
        start_date=start_date,
        end_date=end_date,
        alias_mapping_by_group=alias_mapping,
        map_alias_func=map_alias_to_name
    )
    assert "group1" in changes
    # Check that the unified name is present.
    assert "User One" in changes["group1"]
    user_stats = changes["group1"]["User One"]
    total_commits = sum(user_stats['daily_commits'].values())
    assert total_commits >= 1
