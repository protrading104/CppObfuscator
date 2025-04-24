import re
import logging


class ApiCallRewriter:
    def __init__(self):
        self.logger = self._setup_logger()
        self.api_map = {
            "CreateFileA": "kernel32.dll",
            "ReadFile": "kernel32.dll",
            "WriteFile": "kernel32.dll",
            "CloseHandle": "kernel32.dll",
            "LoadLibraryA": "kernel32.dll",
            "GetProcAddress": "kernel32.dll",
            "VirtualAlloc": "kernel32.dll",
            "VirtualProtect": "kernel32.dll",
            "Sleep": "kernel32.dll",
            "WinExec": "kernel32.dll",
            "ShellExecuteA": "shell32.dll",
            "MessageBoxA": "user32.dll"
        }

    def _setup_logger(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
        return logging.getLogger("ApiCallRewriter")

    def rewrite_calls(self, code: str) -> str:
        self.logger.info("🔁 Переписываем WinAPI вызовы через GetProcAddress...")
        self.logger.debug("🔍 До преобразования:\n" + code[:500])

        # 1️⃣ Соберем нужные includes
        includes = []
        for inc in ["#include <windows.h>", "#include <stdio.h>", "#include <stdlib.h>"]:
            if inc not in code:
                includes.append(inc)

        includes_code = "\n".join(includes)

        # 2️⃣ resolve() всегда вставляем после includes
        resolve_stub = """
    void* resolve(const char* dll, const char* func) {
        HMODULE hMod = LoadLibraryA(dll);
        return GetProcAddress(hMod, func);
    }
    """

        if "void* resolve(" not in code:
            self.logger.info("➕ Вставляем resolve()")
            header_block = includes_code + "\n\n" + resolve_stub
        else:
            self.logger.info("ℹ️ resolve() уже существует")
            header_block = includes_code

        # 3️⃣ Удалим уже существующие includes из code, чтобы не было дублей
        for inc in ["#include <windows.h>", "#include <stdio.h>", "#include <stdlib.h>"]:
            code = code.replace(inc, "")

        code = header_block + "\n\n" + code

        # 4️⃣ Заменяем API вызовы
        skip_apis = {"LoadLibraryA", "GetProcAddress"}
        for api_func, dll_name in self.api_map.items():
            if api_func in skip_apis:
                continue
            pattern = r'\b' + re.escape(api_func) + r'\s*\('
            replacement = f'reinterpret_cast<decltype(&{api_func})>(resolve("{dll_name}", "{api_func}"))('
            code, count = re.subn(pattern, replacement, code)
            if count > 0:
                self.logger.info(f"🔁 Заменён вызов: {api_func} ({count} раз)")

        self.logger.debug("🔍 После преобразования:\n" + code[:500])
        self.logger.info("✅ WinAPI вызовы заменены.")
        return code

