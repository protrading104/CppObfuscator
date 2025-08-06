
import os
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

def pad(data):
    padding_length = 16 - (len(data) % 16)
    return data + bytes([padding_length]) * padding_length

def encrypt_exe(input_path, output_path, key_path):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"[❌] Входной .exe файл не найден: {input_path}")
    if os.path.getsize(input_path) == 0:
        raise ValueError(f"[❌] Входной .exe файл пустой: {input_path}")

    print(f"[✔] Входной файл найден: {input_path}")
    print(f"[✔] Размер файла: {os.path.getsize(input_path)} байт")

    with open(input_path, "rb") as f:
        data = f.read()

    key = get_random_bytes(16)
    print(f"[✔] Сгенерирован AES-128 ключ (длина: {len(key)} байт)")

    cipher = AES.new(key, AES.MODE_ECB)
    encrypted = cipher.encrypt(pad(data))

    with open(output_path, "wb") as f:
        f.write(encrypted)

    with open(key_path, "wb") as f:
        f.write(key)

    print(f"[+] Encrypted EXE → {output_path}")
    print(f"[+] AES Key saved → {key_path}")

if __name__ == "__main__":
    input_exe = r"C:\TEMP\CppObfuscator\sample\agent.x64.exe"  # Заменить на свой путь
    out_enc = r"C:\TEMP\CppObfuscator\output\encrypted_agent.exe"
    out_key = r"C:\TEMP\CppObfuscator\output\agent_aes.key"

    print("[*] Encrypting .exe using AES-128...")
    encrypt_exe(input_exe, out_enc, out_key)
    print("[+] Done.")
