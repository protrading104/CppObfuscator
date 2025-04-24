# -*- coding: utf-8 -*-
import sys
import os

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from obfuscator.jit_compiler import JITCompiler

def test_jit():
    jit = JITCompiler()

    # Простой x86_64 shell-код (возвращает 0)
    asm_code = """
        mov rax, 0
        ret
    """

    shellcode = jit.assemble_shellcode(asm_code)

    # ВАЖНО: убедись, что вызывается ПРАВИЛЬНЫЙ метод
    if hasattr(jit, "execute_shellcode"):
        jit.execute_shellcode(shellcode)
    else:
        print("❌ Ошибка: метод execute_shellcode() не найден в JITCompiler!")

if __name__ == "__main__":
    test_jit()
