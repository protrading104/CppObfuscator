import os

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
                column = entry.get("column", -1)
                original = entry.get("original", "")
                replacement = entry["replacement"]
                is_function = entry.get("is_function", False)
                replacement_code = replacement if is_function else f'"{replacement}"'

                print(f"[DEBUG] Строка для замены: '{original}' -> '{replacement_code}' @ {line_no}:{column}")

                if line_no > 0:
                    replacements_by_line.setdefault(line_no - 1, []).append((column, original, replacement_code))


        # Применение замен
        for line_no, replacements in replacements_by_line.items():
            line = original_lines[line_no]
            original_line = line
            for column, original, replacement in sorted(replacements, key=lambda x: -x[0]):
                replacement_code = replacement if isinstance(replacement, str) else replacement[1]
                index = line.find(original, column)
                if index != -1:
                    line = line[:index] + replacement_code + line[index + len(original):]
            original_lines[line_no] = line
            if original_line != line:
                print(f"[DEBUG] Изменена строка {line_no + 1}:")
                print(f"  ДО: {original_line.strip()}")
                print(f"  ПОСЛЕ: {line.strip()}")

        # Подготовка вставки
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

        # Запись файла
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(original_lines)

        print(f"[INJECTOR] ✅ Обработка завершена.")
        return "".join(original_lines)
