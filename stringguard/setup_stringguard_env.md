import os
import zipfile
import shutil

# Архив и рабочая директория
ZIP_PATH = "stringguard.zip"
BASE_DIR = "c:/TEMP/CppObfuscator/stringguard"
EXTRACT_DIR = os.path.join(BASE_DIR, "_temp_extract")

# Список необходимых файлов
FILES_NEEDED = [
    "backup_restore.py",
    "decryptor_generator.py",
    "filter_engine.py",
    "injector.py",
    "solution_manager.py",
    "string_encoder.py",
    "string_parser.py",
    "validator.py",
    "vcxproj_parser.py"
]

FOLDERS = ["rules", "logs"]

def extract_zip():
    if not os.path.exists(ZIP_PATH):
        print(f"[ERROR] Архив {ZIP_PATH} не найден.")
        return False
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall(EXTRACT_DIR)
    print(f"[ZIP] ✅ Распакован: {ZIP_PATH}")
    return True

def prepare_structure():
    os.makedirs(BASE_DIR, exist_ok=True)
    for folder in FOLDERS:
        os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)
    open(os.path.join(BASE_DIR, "__main__.py"), "w").close()
    print("[SETUP] 📁 Папки и __main__.py созданы")

def copy_files_from_extracted():
    for fname in FILES_NEEDED:
        for root, _, files in os.walk(EXTRACT_DIR):
            if fname in files:
                src = os.path.join(root, fname)
                dst = os.path.join(BASE_DIR, fname)
                shutil.copy(src, dst)
                print(f"[COPY] ✓ {fname}")
                break
        else:
            print(f"[WARN] ✗ Не найден: {fname}")

def cleanup():
    shutil.rmtree(EXTRACT_DIR)
    print("[CLEANUP] Временная папка удалена.")

def summary():
    print("\\n[COMPLETE] Среда готова в:", BASE_DIR)

if __name__ == "__main__":
    if extract_zip():
        prepare_structure()
        copy_files_from_extracted()
        cleanup()
        summary()
