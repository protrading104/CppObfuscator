import os
from crypto.aes import AES128

def encrypt_dll_file(input_path: str, output_path: str, key: bytes):
    """Шифрует DLL-файл с помощью AES-128 и сохраняет в output_path"""
    aes = AES128(key)

    with open(input_path, "rb") as f:
        data = f.read()

    encrypted = aes.encrypt(data)

    with open(output_path, "wb") as f:
        f.write(encrypted)

    print(f"✅ DLL зашифрована и сохранена как {output_path}")
