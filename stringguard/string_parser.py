import re
import os
from typing import List
from .filter_engine import get_skip_reason

SKIP_LOG_FILE = "logs/skipped_strings.txt"

class StringParser:
    def __init__(self):
        self.pattern_normal = re.compile(r'"((?:[^"\\]|\\.)*?)"')
        self.pattern_wide = re.compile(r'L"((?:[^"\\]|\\.)*?)"')
        self.skipped = {}

    def should_skip(self, s: str) -> bool:
        reason = get_skip_reason(s)
        if reason:
            self.skipped[s] = reason
            try:
                print(f"[FILTER] Skipped: {repr(s)} -> {reason}")
            except UnicodeEncodeError:
                print("[FILTER] Skipped: <unprintable string> ->", reason)
            return True
        return False

    def log_skipped(self):
        os.makedirs(os.path.dirname(SKIP_LOG_FILE), exist_ok=True)
        with open(SKIP_LOG_FILE, "w", encoding="utf-8") as f:
            for s, reason in sorted(self.skipped.items()):
                f.write(f"{s}    # skipped because: {reason}\n")

    def parse_file(self, file_path: str) -> List[dict]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        results = []

        for i, line in enumerate(lines):
            for match in self.pattern_normal.finditer(line):
                value = match.group(1)
                if self.should_skip(value):
                    continue
                results.append({
                    "type": "normal",
                    "value": value,
                    "line": i + 1,
                    "column": match.start() + 1
                })

            for match in self.pattern_wide.finditer(line):
                value = match.group(1)
                if self.should_skip(value):
                    continue
                results.append({
                    "type": "wide",
                    "value": value,
                    "line": i + 1,
                    "column": match.start() + 1
                })

        # ⬅️ это сохраняет причины в skipped_strings.txt
        self.log_skipped()
        return results

