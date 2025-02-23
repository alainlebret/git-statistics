import json
import tempfile
from datetime import datetime
import pytest
from config import load_config, validate_date_format, parse_arguments

def test_validate_date_format():
    date_str = "2025-02-14"
    dt = validate_date_format(date_str)
    assert isinstance(dt, datetime)
    assert dt.year == 2025 and dt.month == 2 and dt.day == 14

def test_load_config_valid(tmp_path):
    # Create a temporary config file with valid JSON.
    config_data = {
        "excluded_members": ["user1", "user2"],
        "alias_mapping_by_group": {"group1": {"user1": "User One"}}
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))
    config = load_config(str(config_file))
    assert config == config_data

def test_load_config_invalid(tmp_path):
    # Create a temporary config file with invalid JSON.
    config_file = tmp_path / "config.json"
    config_file.write_text("not valid json")
    config = load_config(str(config_file))
    assert config == {}
