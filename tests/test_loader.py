# -*- coding: utf-8 -*-
import os
import sys
import logging
import pefile

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from obfuscator.dll_loader import ReflectiveDLLLoader

def dump_imports(dll_data: bytes):
    """Выводит все импортируемые функции и библиотеки"""
    print("\n📦 Список импортируемых DLL и функций:")
    pe = pefile.PE(data=dll_data)
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        dll_name = entry.dll.decode(errors='ignore')
        print(f"  ▶ DLL: {dll_name}")
        for imp in entry.imports:
            if imp.name:
                print(f"     └─ Импорт по имени: {imp.name.decode(errors='ignore')}")
            elif imp.ordinal:
                print(f"     └─ Импорт по ординалу: Ordinal({imp.ordinal})")

def test_dll_loading():
    logging.basicConfig(level=logging.INFO)

    # AES ключ должен совпадать с utils/encrypt_dll.py
    key = b'1234567890abcdef'
    loader = ReflectiveDLLLoader(key)

    path = "output/test_dll_encrypted.bin"
    dll_data = loader.load_encrypted_dll(path)

    # 🔍 Показываем все импорты из DLL перед маппингом
    dump_imports(dll_data)

    dll_base = loader.manual_map(dll_data)
    loader.call_entry_point(dll_base)

    print("\n✅ DLL успешно загружена в память и выполнена.")

if __name__ == "__main__":
    test_dll_loading()
