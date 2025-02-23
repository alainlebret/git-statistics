from utils import map_alias_to_name

def test_map_alias_to_name_group():
    alias_mapping = {
        "group1": {
            "user1": "User One",
            "user2": "User Two"
        },
        "global": {
            "user3": "User Three"
        }
    }
    # Test that group-specific alias is applied.
    result = map_alias_to_name(" user1 ", "group1", alias_mapping)
    assert result == "User One"

def test_map_alias_to_name_global():
    alias_mapping = {
        "group1": {
            "user1": "User One"
        },
        "global": {
            "user2": "User Two"
        }
    }
    result = map_alias_to_name("User2", "group1", alias_mapping)
    assert result == "User Two"

def test_map_alias_to_name_no_match():
    alias_mapping = {
        "group1": {},
        "global": {}
    }
    result = map_alias_to_name("UserX", "group1", alias_mapping)
    # The function normalizes the name, so "UserX" becomes "userx".
    assert result == "userx"
