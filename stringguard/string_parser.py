import re
from dataclasses import dataclass
from typing import List

@dataclass
class StringEntry:
    filename: str
    line: int
    column: int
    raw_text: str
    type: str  # "normal", "wide", "raw", "obf"
    full_line: str
    is_excluded: bool

class StringParser:
    def __init__(self):
        self.patterns = [
            (r'(?<!L)\"(.*?)\"', "normal"),
            (r'L\"(.*?)\"', "wide"),
            (r'R"\((.*?)\)"', "raw"),
            (r'OBF_STR\((.*?)\)', "obf")
        ]

    def parse_file(self, filepath: str) -> List[dict]:
        results = []
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            line_strip = line.strip()
            if line_strip.startswith("#include") or line_strip.startswith("//") or line_strip.startswith("/*"):
                continue
            for pattern, typ in self.patterns:
                for match in re.finditer(pattern, line):
                    entry = {
                        "filename": filepath,
                        "line": i + 1,
                        "column": match.start() + 1,
                        "value": match.group(1),
                        "type": typ,
                        "full_line": line.strip(),
                        "is_excluded": False
                    }
                    results.append(entry)
        return results

    def parse_files(self, file_list: List[str]) -> List[dict]:
        all_entries = []
        for file in file_list:
            entries = self.parse_file(file)
            all_entries.extend(entries)
        return all_entries
