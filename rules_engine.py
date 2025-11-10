# rules_engine.py
from typing import List, Dict, Any
import copy
import pandas as pd

from rules_config import CHECKBOX_RULES


def _normalize_text(value: Any) -> str:
    """None, 숫자 등 어떤 값이 와도 비교하기 좋게 문자열로 정리."""
    if value is None:
        return ""
    return str(value).strip()


def _eval_rule_logic(project: Dict[str, Any], logic: Dict[str, Any]) -> bool:
    """한 프로젝트에 대해 하나의 규칙이 적용되는지 판단."""
    logic_type = logic.get("type")

    if logic_type == "keyword_any":
        field = logic["field"]
        keywords = logic["keywords"]
        value = _normalize_text(project.get(field, ""))
        # 대소문자 섞일 수 있으니 소문자로 비교 (한글은 그대로여도 괜찮음)
        lower_value = value.lower()
        return any(kw.lower() in lower_value for kw in keywords)

    if logic_type == "field_value":
        field = logic["field"]
        expected = _normalize_text(logic.get("equals", ""))
        actual = _normalize_text(project.get(field, ""))
        return actual == expected

    # TODO: regex, range 등 추가 가능
    return False


def apply_all_checkbox_rules(raw_projects: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    각 프로젝트에 대해:
      - 모든 규칙을 평가
      - rule__<id> 컬럼에 True/False 저장
      - checked_rule_ids 에 체크된 규칙 id들 모아두기
    """
    rows = []

    for p in raw_projects:
        row = copy.deepcopy(p)

        checked_ids = []
        for rule in CHECKBOX_RULES:
            rid = rule["id"]
            is_checked = _eval_rule_logic(p, rule["logic"])
            row[f"rule__{rid}"] = bool(is_checked)
            if is_checked:
                checked_ids.append(rid)

        row["checked_rule_ids"] = ", ".join(checked_ids)
        rows.append(row)

    df = pd.DataFrame(rows)
    return df
