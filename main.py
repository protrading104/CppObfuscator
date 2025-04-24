import argparse
import os
import subprocess
import logging

from obfuscator import code_transformer
from obfuscator.dll_loader import ReflectiveDLLLoader
from utils.encrypt_dll import AES128

# 🔧 Импортируем модули stringguard напрямую
from stringguard import (
    vcxproj_parser, solution_manager,
    string_parser, string_encoder,
    decryptor_generator, injector,
    backup_restore, validator
)

logger = logging.getLogger("CLI")

def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s:%(name)s: %(message)s")

def obfuscate_cpp(input_file, output_file, project_type="dll"):
    logger.info("🎭 Обфусцируем C++ код...")
    with open(input_file, "r", encoding="utf-8", errors="replace") as f:
        code = f.read()
    obfuscated = code_transformer.obfuscate(code, project_type)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(obfuscated)
    logger.info("✅ Обфускация завершена.")

def compile_dll(source_file, output_dll):
    logger.info("🛠️ Компиляция DLL из C++ файла...")
    result = subprocess.run([
        "cl", "/LD", source_file,
        "/link", f"/OUT:{output_dll}", "user32.lib"
    ], shell=True)
    if result.returncode != 0:
        raise RuntimeError("❌ Ошибка компиляции DLL")
    logger.info("✅ Компиляция завершена.")

def encrypt_dll(input_dll, output_bin, key):
    logger.info("🔐 Шифруем DLL (AES128)...")
    with open(input_dll, "rb") as f:
        data = f.read()
    encrypted = AES128(key).encrypt(data)
    with open(output_bin, "wb") as f:
        f.write(encrypted)
    logger.info("✅ DLL зашифрована.")

def load_encrypted(encrypted_bin, key):
    logger.info("📦 Загружаем зашифрованную DLL в память...")
    loader = ReflectiveDLLLoader(key)
    dll_data = loader.load_encrypted_dll(encrypted_bin)
    dll_base = loader.manual_map(dll_data)
    loader.call_entry_point(dll_base)
    logger.info("✅ DLL успешно загружена и выполнена.")

# 🔧 Функция для stringguard обработки проекта
def run_stringguard_project(project_path, debug=False):
    if project_path.endswith(".sln"):
        projects = solution_manager.SolutionManager(project_path).extract_vcxproj_paths()
    elif project_path.endswith(".vcxproj"):
        projects = [project_path]
    else:
        raise ValueError("❌ Укажите .sln или .vcxproj")

    for proj in projects:
        base_dir = os.path.dirname(os.path.abspath(proj))
        source_files = vcxproj_parser.VcxprojParser(proj).extract_source_files()

        for rel_path in source_files:
            abs_path = os.path.normpath(os.path.join(base_dir, rel_path))
            if not os.path.exists(abs_path):
                print(f"[!] Пропущен несуществующий файл: {abs_path}")
                continue

            backup_mgr = backup_restore.BackupManager()
            backup_mgr.backup_file(abs_path)

            parser = string_parser.StringParser()
            strings = parser.parse_file(abs_path)


            # ✅ Вставь здесь для отладки:
            for s in strings:
                print(f"[DEBUG] Строка: '{s['value']}' | Тип: {s['type']} | Линия: {s['line']}, Колонка: {s['column']}")

            if not strings:
                validator.log_results(abs_path, [], {})
                continue  # ⛔️ Пропустить, если строк нет

            encoder = string_encoder.StringEncoder()

            # ✅ Генерация уникальных имен дешифраторов
            base_name = os.path.splitext(os.path.basename(abs_path))[0]
            name_normal = f"decrypt_{base_name}"
            name_wide = f"decrypt_wide_{base_name}"

            # ⬇️ Передаём строки напрямую, они уже включают line/column
            encoded = encoder.encode_strings(
                strings,
                name_normal=name_normal,
                name_wide=name_wide
            )

            decryptor_gen = decryptor_generator.DecryptorGenerator(encoder.xor_key, name_normal, name_wide)
            decryptor_code = decryptor_gen.get_decryptor() + "\n" + decryptor_gen.get_decryptor_wide()

            injection = injector.Injector(inline=True)
            updated_code = injection.inject(abs_path, encoded, decryptor_code)

            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(updated_code)

            validator.log_results(abs_path, strings, encoded)





if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🎯 Обфускатор C++ кода с Reflective DLL Loading и шифрованием строк")

    parser.add_argument("--obfuscate", action="store_true", help="Применить обфускацию к C++ файлу")
    parser.add_argument("--compile-dll", action="store_true", help="Скомпилировать обфусцированный файл в DLL")
    parser.add_argument("--encrypt-dll", action="store_true", help="Зашифровать DLL файл")
    parser.add_argument("--load-encrypted", action="store_true", help="Загрузить зашифрованную DLL вручную")
    parser.add_argument("--debug", action="store_true", help="Включить подробное логирование")

    parser.add_argument("--type", choices=["dll", "exe"], default="dll", help="Тип проекта: dll или exe (по умолчанию: dll)")
    parser.add_argument("--input", help="Входной C++ файл", default="sample/test_dll.cpp")
    parser.add_argument("--output", help="Обфусцированный C++ файл", default="output/test_dll_obf.cpp")
    parser.add_argument("--dll", help="Путь к DLL", default="output/test_dll.dll")
    parser.add_argument("--bin", help="Путь к зашифрованному бинарному файлу", default="output/test_dll_encrypted.bin")
    parser.add_argument("--key", help="AES ключ (16 байт)", default="0123456789abcdef")

    # ✅ Поддержка проектов
    parser.add_argument("--project", help="Путь к .vcxproj или .sln файлу")

    args = parser.parse_args()
    setup_logging(args.debug)

    if args.project:
        run_stringguard_project(args.project, debug=args.debug)

    if args.obfuscate:
        obfuscate_cpp(args.input, args.output, args.type)

    if args.compile_dll:
        compile_dll(args.output, args.dll)

    if args.encrypt_dll:
        encrypt_dll(args.dll, args.bin, args.key.encode())

    if args.load_encrypted:
        load_encrypted(args.bin, args.key.encode())
