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

def get_skip_reason(value: str) -> str | None:
    value = value.strip()

    # ⛔️ Исключаем технические конструкции
    if not value or value in {" ", "\n", "\r\n"}:
        return "Empty or whitespace"

    if value.startswith("#include") or value.startswith("#define") or value.startswith("#pragma"):
        return "Preprocessor directive"

    if value.startswith("using namespace"):
        return "Using namespace statement"

    if any(fmt in value for fmt in ["%s", "%d", "%x", "%p", "%f"]):
        return "Format string (likely for printf/scanf)"

    # Проверка по YAML-файлу
    if rules_cache is not None:
        if "exclude" in rules_cache and isinstance(rules_cache["exclude"], list):
            for pattern in rules_cache["exclude"]:
                if pattern in value:
                    return f"Matched exclude rule: {pattern}"

    return None  # 🚀 Строка может быть обфусцирована



