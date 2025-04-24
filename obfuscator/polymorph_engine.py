import re
import random
import string
import logging


class Polymorpher:
    def __init__(self):
        self.logger = self._setup_logger()
        self.renamed = {}

    def _setup_logger(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
        return logging.getLogger("Polymorpher")

    def _random_name(self, length=8):
        while True:
            name = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
            if not name[0].isdigit():
                return name

    def _rename_variables(self, code: str) -> str:
        self.logger.info("🔀 Переименование переменных...")

        pattern = re.compile(r"\b(int|char|float|bool|DWORD|HANDLE|LPSTR|long)\s+([a-zA-Z_]\w*)")
        matches = pattern.findall(code)

        for _, var in matches:
            if var in ["main", "if", "for", "while", "return"]:
                continue
            if var not in self.renamed:
                self.renamed[var] = self._random_name()
            code = re.sub(rf'\b{re.escape(var)}\b', self.renamed[var], code)

        return code

    def _insert_junk_code(self, code: str) -> str:
        self.logger.info("💉 Вставка junk-кода...")

        var1 = self._random_name()
        var2 = self._random_name()
        junk_code = [
            f"    int {var1} = {random.randint(1000, 9999)};",
            f"    int {var2} = 0;",
            f"    if ({var1} > {random.randint(200, 999)}) {{ {var2}++; }}",
            '    if (false) puts("unreachable");'
        ]

        # Найдём позицию вставки — после "int main()" и первой открывающей {
        main_pattern = re.search(r'int\s+main\s*\(\s*\)\s*\{', code)
        if main_pattern:
            insert_index = main_pattern.end()
            # Вставляем junk после этой точки
            code = code[:insert_index] + "\n" + "\n".join(junk_code) + code[insert_index:]
        else:
            self.logger.warning("⚠️ Функция main() не найдена — junk-код не вставлен")

        return code



    def morph(self, code: str) -> str:
        self.logger.info("🎭 Применение полиморфного преобразования...")

        code = self._rename_variables(code)
        code = self._insert_junk_code(code)

        self.logger.info("✅ Полиморфизм завершён.")
        return code
