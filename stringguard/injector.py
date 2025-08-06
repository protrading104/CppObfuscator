import os
import re

class Injector:
    def __init__(self, inline=True):
        self.inline = inline

    def inject(self, file_path, string_map, decryptors_code):
        print(f"[INJECTOR] 🔧 Обработка файла: {file_path}")
        with open(file_path, "r", encoding="utf-8-sig") as f:
            original_lines = f.readlines()

        decrypt_arrays = []
        replacements_by_line = {}

        for entries in string_map.values():
            for entry in entries:
                decrypt_arrays.append(entry["array_decl"])
                line_no = entry.get("line", -1)
                original = entry.get("original", "")
                replacement = entry["replacement"]
                is_function = entry.get("is_function", False)
                replacement_code = replacement

                if is_function:
                    line_text = original_lines[line_no - 1] if 0 <= line_no - 1 < len(original_lines) else ""
                    if "printf(" in line_text or "wprintf(" in line_text:
                        prefix = 'L' if 'wprintf(' in line_text else ''
                        format_str = f'{prefix}"%s"'
                        original_lines[line_no - 1] = re.sub(r'(L?)"[^"]*"', f'{format_str}, {replacement}', line_text, count=1)
                        print(f"[REWRITE] Строка {line_no} заменена на: {original_lines[line_no - 1].strip()}")
                        continue

                # fallback обычная замена по original
                if line_no > 0:
                    replacements_by_line.setdefault(line_no - 1, []).append((original, replacement_code))

        for line_no, replacements in replacements_by_line.items():
            line = original_lines[line_no]
            for original, replacement in sorted(replacements, key=lambda x: -line.find(x[0])):
                index = line.find(original)
                if index != -1:
                    line = line[:index] + replacement + line[index + len(original):]
            original_lines[line_no] = line

        injected_code = ""
        if self.inline:
            injected_code += "\n// ====== DECRYPT FUNCTIONS ======\n"
            injected_code += decryptors_code
            injected_code += "\n// ====== ENCRYPTED ARRAYS ======\n"
            injected_code += "\n".join(decrypt_arrays)
            injected_code += "\n"

            for i, line in enumerate(original_lines):
                if line.strip().startswith("#include"):
                    print(f"[INJECTOR] 💉 Вставка шифровального кода перед: {line.strip()}")
                    original_lines.insert(i, injected_code + "\n")
                    break

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(original_lines)

        print(f"[INJECTOR] ✅ Обработка завершена.")
        return "".join(original_lines)