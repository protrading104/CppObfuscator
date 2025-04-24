import uuid  

class DecryptorGenerator:
    def __init__(self, xor_key: int, name_normal="decrypt", name_wide="decrypt_wide"):
        self.xor_key = xor_key
        self.name_normal = name_normal or f"decrypt_{uuid.uuid4().hex[:8]}"
        self.name_wide = name_wide or f"decrypt_wide_{uuid.uuid4().hex[:8]}"

    def get_decryptor(self) -> str:
        return (
            f"char* {self.name_normal}(const unsigned char* data, int len) {{\n"
            f"    static char result[1024];\n"
            f"    unsigned char key = {self.xor_key};\n"
            f"    for (int i = 0; i < len; ++i) {{\n"
            f"        result[i] = data[i] ^ key;\n"
            f"        key = (key + 1) % 256;\n"
            f"    }}\n"
            f"    result[len] = '\\0';\n"
            f"    return result;\n"
            f"}}"
        )

    def get_decryptor_wide(self) -> str:
        return (
            f"wchar_t* {self.name_wide}(const unsigned char* data, int len) {{\n"
            f"    static wchar_t result[1024];\n"
            f"    unsigned char key = {self.xor_key};\n"
            f"    for (int i = 0; i < len; ++i) {{\n"
            f"        result[i] = (wchar_t)(data[i] ^ key);\n"
            f"        key = (key + 1) % 256;\n"
            f"    }}\n"
            f"    result[len] = L'\\0';\n"
            f"    return result;\n"
            f"}}"
        )

    def get_all(self) -> str:
        return self.get_decryptor() + "\n\n" + self.get_decryptor_wide()
# ✅ Функция для генерации кода дешифраторов из словаря encoded_map
def generate_decryptor_code(encoded_strings: dict, name_normal: str, name_wide: str) -> str:
    xor_key = 42  # или использовать StringEncoder().xor_key, если нужно синхронизировать

    def get_decryptor(name):
        return (
            f"char* {name}(const unsigned char* data, int len) {{\n"
            f"    static char result[1024];\n"
            f"    unsigned char key = {xor_key};\n"
            f"    for (int i = 0; i < len; ++i) {{\n"
            f"        result[i] = data[i] ^ key;\n"
            f"        key = (key + 1) % 256;\n"
            f"    }}\n"
            f"    result[len] = '\\0';\n"
            f"    return result;\n"
            f"}}"
        )

    def get_decryptor_wide(name):
        return (
            f"wchar_t* {name}(const unsigned char* data, int len) {{\n"
            f"    static wchar_t result[1024];\n"
            f"    unsigned char key = {xor_key};\n"
            f"    for (int i = 0; i < len; ++i) {{\n"
            f"        result[i] = (wchar_t)(data[i] ^ key);\n"
            f"        key = (key + 1) % 256;\n"
            f"    }}\n"
            f"    result[len] = L'\\0';\n"
            f"    return result;\n"
            f"}}"
        )

    return get_decryptor(name_normal) + "\n\n" + get_decryptor_wide(name_wide)
