import re
import sys
import random
import logging

class StringEncryptor:
    def __init__(self):
        self.xor_key = random.randint(1, 255)
        self.decrypt_func_name = self._generate_random_name()
        self.decrypt_wide_func_name = self._generate_random_name()
        self.decrypt_func_declared = False
        self.logger = self._setup_logger()

    def _generate_random_name(self):
        import string
        return ''.join(random.choices(string.ascii_letters, k=8))

    def _setup_logger(self):
        logger = logging.getLogger("StringEncryptor")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)
        return logger

    def encrypt_strings(self, code):
        code_lines = code.splitlines()
        include_lines = [line.strip() for line in code_lines if line.strip().startswith("#include")]
        matches = re.findall(r'([L]?)"(.*?)"', code)

        if not matches:
            self.logger.info("⚠️ Не найдено строк для шифрования.")
            return code

        replacements = {}
        arrays_code = ""

        for prefix, match in matches:
            if not match.strip():
                continue

            if any(f'"{match}"' in line or f'<{match}>' in line for line in include_lines):
                self.logger.debug(f"⛔ Пропущена строка из-за #include: {prefix}{match}")
                continue

            try:
                enc = [(b ^ self.xor_key) & 0xFF for b in match.encode('utf-8')]
                var_name = self._generate_random_name()
                enc_array = ', '.join(f"0x{b:02x}" for b in enc)
                arrays_code += f"const unsigned char {var_name}[] = {{{enc_array}}};\n"
                if prefix == 'L':
                    replacement = f"{self.decrypt_wide_func_name}({var_name}, {len(enc)})"
                else:
                    replacement = f"{self.decrypt_func_name}({var_name}, {len(enc)})"
                replacements[f'{prefix}\"{match}\"'] = replacement
                self.logger.debug(f"[OK] Зашифровано: {prefix}\"{match}\" → {var_name}")
            except Exception as e:
                self.logger.error(f"❌ Ошибка при обработке строки '{match}': {e}")
                sys.exit(1)

        for orig, repl in replacements.items():
            code = code.replace(orig, repl)

        if not self.decrypt_func_declared:
            self.decrypt_func_declared = True

            decrypt_func = (
                f"char* {self.decrypt_func_name}(const unsigned char* data, int len) {{\n"
                f"    static char result[1024];\n"
                f"    unsigned char key = {self.xor_key};\n"
                f"    for (int i = 0; i < len; i++) {{\n"
                f"        result[i] = data[i] ^ key;\n"
                f"        key = (key + 1) % 256;\n"
                f"    }}\n"
                f"    result[len] = '\\0';\n"
                f"    return result;\n"
                f"}};\n"
            )

            decrypt_wide_func = (
                f"wchar_t* {self.decrypt_wide_func_name}(const unsigned char* data, int len) {{\n"
                f"    static wchar_t result[1024];\n"
                f"    unsigned char key = {self.xor_key};\n"
                f"    for (int i = 0; i < len; i++) {{\n"
                f"        result[i] = (wchar_t)(data[i] ^ key);\n"
                f"        key = (key + 1) % 256;\n"
                f"    }}\n"
                f"    result[len] = L'\\0';\n"
                f"    return result;\n"
                f"}};\n"
            )

            code = decrypt_func + decrypt_wide_func + arrays_code + "\n" + code
        else:
            code = arrays_code + "\n" + code

        return code

