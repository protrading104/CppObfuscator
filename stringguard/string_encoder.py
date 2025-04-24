
from typing import List, Dict
import random

class StringEncoder:
    def __init__(self, xor_key: int = None):
        self.xor_key = xor_key if xor_key is not None else random.randint(1, 255)

    def _generate_var_name(self) -> str:
        return ''.join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=8))

    def encrypt_xor(self, text: str) -> List[int]:
        key = self.xor_key
        return [(ord(c) ^ key + i) & 0xFF for i, c in enumerate(text)]

    def encode_strings(self, strings: List, name_normal="decrypt", name_wide="decrypt_wide") -> Dict[str, List[Dict]]:
        result = {}
        for s in strings:
            original = s["value"]
            if not original.strip():
                continue

            is_wide = s["type"] == "wide"
            enc_bytes = self.encrypt_xor(original)
            var_name = self._generate_var_name()
            array_decl = f"const unsigned char {var_name}[] = {{" + ', '.join(f"0x{b:02x}" for b in enc_bytes) + "};"
            call_expr = f'{name_wide}({var_name}, {len(enc_bytes)})' if is_wide else f'{name_normal}({var_name}, {len(enc_bytes)})'

            entry = {
                "encrypted": enc_bytes,
                "array_decl": array_decl,
                "replacement": call_expr,
                "var_name": var_name,
                "line": s["line"],
                "column": s["column"],
                "original": original
            }

            result.setdefault(original, []).append(entry)
        return result
