#!/usr/bin/env python3
"""
utils.py

This module provides utility functions used by the Git Project Statistics tool.
Currently, it includes a function to map an author's name to a unified alias
based on group-specific alias mappings, with a fallback to a global mapping.

Usage:
    from utils import map_alias_to_name

Author: Alain Lebret, 2024-2025
License: MIT License
"""

def map_alias_to_name(author_name, group_label, alias_mapping_by_group):
    """
    Returns the unified alias for an author based on the group label and the provided alias mapping.

    The function normalizes the author's name (removing extra spaces and converting to lowercase)
    and then checks if the name exists in the alias mapping for the specified group.
    If not found, it then checks the global alias mapping. If the author is not found in either,
    the original normalized name is returned.

    Args:
        author_name (str): Name of the author.
        group_label (str): Label of the group to which the author belongs.
        alias_mapping_by_group (dict): Dictionary containing alias mappings for each group,
                                       including an optional "global" mapping.

    Returns:
        str: The unified alias of the author.
    """
    # Normalize the author's name: remove surrounding whitespace and convert to lowercase.
    normalized_author = author_name.strip().lower()

    # Check if there is a specific alias mapping for the given group.
    if group_label in alias_mapping_by_group:
        grp_dict = alias_mapping_by_group[group_label]
        if normalized_author in grp_dict:
            return grp_dict[normalized_author]

    # If not found in the group's mapping, check in the global mapping.
    global_dict = alias_mapping_by_group.get("global", {})
    if normalized_author in global_dict:
        return global_dict[normalized_author]

    # Return the normalized name if no alias is found.
    return normalized_author
