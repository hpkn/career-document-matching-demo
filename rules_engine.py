"""
Rules engine for evaluating project eligibility criteria.

Applies checkbox rules from rules_config.py to normalized project data,
determining which career recognition criteria each project meets.
"""
from typing import List, Dict, Any
import copy
import pandas as pd

from rules_config import CHECKBOX_RULES


def _normalize_text(value: Any) -> str:
    """
    --- [FIX] This function was missing ---
    Safely converts any value to a normalized string.
    """
    if value is None:
        return ""
    return str(value).strip()


def _eval_rule_logic(project: Dict[str, Any], logic: Dict[str, Any]) -> bool:
    """
    Checks if a project dictionary matches a given rule logic.
    Handles both single strings and lists of strings.
    """
    logic_type = logic.get("type")

    if logic_type == "keyword_any":
        field_name = logic["field"]
        keywords = logic["keywords"]
        value = project.get(field_name) # Get the value (could be string or list)

        # --- Multi-Select Logic ---
        if isinstance(value, list):
            # Handle list fields (like 'roles' or 'original_fields')
            # Check if *any* keyword matches *any* item in the list
            value_list = [_normalize_text(v).lower() for v in value]
            keywords_lower = [kw.lower() for kw in keywords]
            
            for item in value_list:
                for kw in keywords_lower:
                    if kw in item: # Check if keyword is in the item
                        return True
            return False # No keyword matched any item
        
        elif isinstance(value, (str, int, float)):
            # Handle single string fields (like 'project_name' or 'client')
            value_str = _normalize_text(value).lower()
            return any(kw.lower() in value_str for kw in keywords)
        
        else:
            # Handle None or other types
            return False
        # --- End of Multi-Select Logic ---

    if logic_type == "field_value":
        field = logic["field"]
        expected = _normalize_text(logic.get("equals", ""))
        actual = _normalize_text(project.get(field, ""))
        return actual == expected

    return False


def apply_all_checkbox_rules(normalized_project: Dict[str, Any]) -> pd.Series:
    """
    normalized_project: A SINGLE project dict (already normalized)
    Returns: A single pd.Series with original fields + rule__* columns
    """
    if not normalized_project:
        return pd.Series(dtype=object)

    row = copy.deepcopy(normalized_project)
    checked_ids = []

    for rule in CHECKBOX_RULES:
        rid = rule["id"]
        # This call to _eval_rule_logic requires _normalize_text to exist
        is_checked = _eval_rule_logic(row, rule["logic"])
        col_name = f"rule__{rid}"
        row[col_name] = bool(is_checked)
        if is_checked:
            checked_ids.append(rid)

    row["checked_rule_ids"] = ", ".join(checked_ids)
    
    return pd.Series(row)