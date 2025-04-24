from crypto.aes import AES128

def test_encrypt_dll():
    dll_path = "test_payloads/test_dll.dll"
    output_path = "test_payloads/test.dll.aes"
    aes_key = b"1234567890abcdef"

    aes = AES128(aes_key)

    with open(dll_path, "rb") as f:
        raw = f.read()

    encrypted = aes.encrypt(raw)

    with open(output_path, "wb") as f:
        f.write(encrypted)

    print("✅ DLL зашифрована и сохранена как:", output_path)

if __name__ == "__main__":
    test_encrypt_dll()
