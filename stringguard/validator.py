import re
import logging

class Validator:
    def __init__(self):
        self.logger = logging.getLogger("Validator")
        self._setup_logger()

    def _setup_logger(self):
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def validate_code_strings(self, file_path, original_strings):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        found = []
        for s in original_strings:
            if s in content:
                found.append(s)

        if found:
            self.logger.warning(f"[⚠️] Найдено {len(found)} незашифрованных строк в {file_path}")
            for s in found:
                self.logger.warning(f"  → \"{s}\"")
        else:
            self.logger.info(f"[✅] Все строки успешно зашифрованы в {file_path}")

        return found

    def scan_binary_for_plaintext(self, binary_path, strings):
        found = []
        try:
            with open(binary_path, 'rb') as f:
                data = f.read()

            for s in strings:
                if s.encode() in data:
                    found.append(s)
        except Exception as e:
            self.logger.error(f"[❌] Ошибка при чтении бинарника: {e}")

        if found:
            self.logger.warning(f"[⚠️] Строки в бинарнике не зашифрованы: {len(found)}")
            for s in found:
                self.logger.warning(f"  → \"{s}\"")
        else:
            self.logger.info(f"[🔒] Бинарник не содержит открытых строк")

        return found


def log_results(file_path, strings, encoded_map):
    print(f"[✅] Валидатор: обработан файл {file_path}")
    print(f"     🔹 Найдено строк: {len(strings)}")
    print(f"     🔐 Зашифровано: {len(encoded_map)}")

