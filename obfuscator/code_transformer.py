import os
from crypto.string_encryptor import StringEncryptor
from obfuscator.control_flow import ControlFlowFlattener
from obfuscator.opaque_predicates import OpaquePredicateInjector
from obfuscator.api_resolver import ApiCallRewriter
from obfuscator.polymorph_engine import Polymorpher
from obfuscator.syscall_hiding import SyscallHider


def obfuscate(code: str, project_type: str = "dll") -> str:
    transformer = CodeTransformer()
    return transformer.apply_transformations(code)


class CodeTransformer:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.flattener = ControlFlowFlattener()
        self.opaque_injector = OpaquePredicateInjector()
        self.api_rewriter = ApiCallRewriter()
        self.encryptor = StringEncryptor()
        self.morpher = Polymorpher()
        self.syscall_hider = SyscallHider()

    def inject_syscall_stub(self, code: str, syscall_name: str) -> str:
        index = self.syscall_hider.get_syscall_index(syscall_name)
        stub = self.syscall_hider.generate_syscall_stub(index, morph=True)

        stub_array = ", ".join(f"0x{b:02x}" for b in stub)
        stub_name = f"syscall_{syscall_name.lower()}"
        array_decl = f"unsigned char {stub_name}[] = {{{stub_array}}};\n"

        call_stmt = (
            f"    ((int(__stdcall*)(void*, void*, void*)){stub_name})(NULL, NULL, NULL);\n"
        )

        # Вставляем массив в начало
        if "int main" in code:
            insert_pos = code.find("int main")
            code = array_decl + code[:insert_pos] + code[insert_pos:]

        # Вставляем вызов shellcode внутрь main()
        main_start = code.find("int main")
        brace_pos = code.find("{", main_start)
        if brace_pos != -1:
            insert_point = code.find("if (false)", brace_pos)
            if insert_point != -1:
                insert_end = code.find(";", insert_point)
                code = code[:insert_end + 1] + "\n" + call_stmt + code[insert_end + 1:]

        return code


    def load_file(self, path: str) -> str:
        with open(path, "r", encoding="utf-8-sig") as f:  # ✅ удаляет BOM
            code = f.read()
        # 🧹 Удаляем «проблемные» символы
        bad_chars = ["\u2014", "\u200b", "\ufeff", "\u202a", "\u202c"]
        for ch in bad_chars:
            code = code.replace(ch, "")

        return code

    def save_file(self, path: str, content: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def apply_transformations(self, code: str) -> str:
        """
        Применяет обфускации к исходному коду: 
        AST-трансформации (если не C++), API-скрытие, шифрование строк, морфинг.
        """
        language = self.config.get("language", "cpp")  # По умолчанию считаем, что это C++

        if language != "cpp":
            self.log("🔁 Применение Control Flow Flattening...")
            code = self.flattener.transform(code)

            self.log("🌀 Внедрение Opaque Predicates...")
            code = self.opaque_injector.inject(code)

        self.log("🔍 Переписываем API вызовы...")
        code = self.api_rewriter.rewrite_calls(code)

        self.log("🔐 Шифруем строки и переменные...")
        code = self.encryptor.encrypt_strings(code)

        self.log("🎭 Применяем морфинг...")
        code = self.morpher.morph(code)

        # 🔥 Вставка shellcode с syscall
        self.log("📦 Вставляем shellcode для NtQuerySystemInformation...")
        code = self.inject_syscall_stub(code, "NtQuerySystemInformation")

        return code



    def run(self, input_path: str, output_path: str):
        self.log(f"📥 Загрузка исходного файла: {input_path}")
        code = self.load_file(input_path)

        code = self.apply_transformations(code)

        self.log(f"📤 Сохраняем обфусцированный файл: {output_path}")
        self.save_file(output_path, code)

    def log(self, message: str):
        print(f"[CodeTransformer] {message}")
