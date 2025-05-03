# filter_engine.py
import re
import yaml
from pathlib import Path

RULES_PATH = Path("rules/filter_rules.yaml")

def load_filter_rules():
    if not RULES_PATH.exists():
        raise FileNotFoundError(f"Filter rules file not found: {RULES_PATH}")

    with open(RULES_PATH, "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f)

    return {
        "skip_exact": rules.get("skip_exact", {}),
        "skip_keywords": rules.get("skip_keywords", {}),
        "regex_patterns": [(re.compile(p), reason) for p, reason in rules.get("regex_patterns", [])],
        "syntax_noise": [(re.compile(p), reason) for p, reason in rules.get("syntax_noise", [])],
    }

rules_cache = load_filter_rules()

def get_skip_reason(s: str) -> str | None:
    s = s.strip()
    if not s:
        return "empty string"
    if len(s) <= 2:
        return "too short"

    if s in rules_cache["skip_keywords"]:
        return rules_cache["skip_keywords"][s]

    for marker, reason in rules_cache["skip_exact"].items():
        if marker in s:
            return reason

    for pattern, reason in rules_cache["regex_patterns"]:
        if pattern.search(s):  # исправлено!
            return reason

    for pattern, reason in rules_cache["syntax_noise"]:
        if pattern.search(s):  # исправлено!
            return reason

    if "\\\\PIPE\\" in s:
        return "visual pipe decoration"

    visible = [c for c in s if c.isalnum()]
    if not visible:
        return "no visible characters"

    return None


