from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

def encrypt_shellcode(input_path, output_path, key_path):
    with open(input_path, "rb") as f:
        data = f.read()

    key = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_ECB)
    padded = data + b"\x00" * ((16 - len(data) % 16) % 16)
    encrypted = cipher.encrypt(padded)

    with open(output_path, "wb") as f:
        f.write(encrypted)

    with open(key_path, "wb") as f:
        f.write(key)

    print(f"[+] Shellcode encrypted → {output_path}")
    print(f"[+] AES Key saved → {key_path}")


# 👇 ВНЕ функции, как должно быть:
if __name__ == "__main__":
    input_path = "sample/agent.x64.bin"
    output_path = "sample/agent.x64.aes"
    key_path = "sample/aes_key.bin"

    print("[*] Encrypting shellcode...")
    encrypt_shellcode(input_path, output_path, key_path)
    print("[+] Done.")
