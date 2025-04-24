#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>  // для strcpy

char* BLNAe9xm(const unsigned char* data, int YYlNDB8y) {
    static char fqomKSpR[1024];
    unsigned char UR0G3tPz = 28;
    for (int OlZKhvhe = 0; OlZKhvhe < YYlNDB8y; OlZKhvhe++) {
        fqomKSpR[OlZKhvhe] = data[OlZKhvhe] ^ UR0G3tPz;
        UR0G3tPz = (UR0G3tPz + 1) % 256;
    }
    fqomKSpR[YYlNDB8y] = '\0';
    return fqomKSpR;
}

void* resolve(const char* dll, const char* func) {
    HMODULE hMod = LoadLibraryA(dll);
    return GetProcAddress(hMod, func);
}

// Зашифрованные строки
const unsigned char FMFkeGpt[] = {0x69, 0x6e, 0x7b, 0x6d, 0x13, 0x13, 0x0c, 0x47, 0x48, 0x49};
const unsigned char q5plYYMy[] = {0x51, 0x78, 0x6d, 0x6c, 0x41, 0x46, 0x47, 0x61, 0x4b, 0x5d, 0x67};
const unsigned char rlc5dcZu[] = {0x5f, 0x72, 0x7a, 0x7a, 0x00, 0x42, 0x4d, 0x4e, 0x54, 0x49, 0x43, 0x53, 0x4d, 0x4d, 0x0a, 0x58, 0x59, 0x4e, 0x4d, 0x4a, 0x43, 0x42, 0x54, 0x46, 0x58, 0x59, 0x4f};
const unsigned char VUzYUMf0[] = {0x53, 0x7f, 0x78, 0x6a, 0x53, 0x42, 0x43, 0x57, 0x4b, 0x57};

int main() {
    int urI9GSbA = 3128;
    int nkApqCpa = 0;
    if (urI9GSbA > 229) { nkApqCpa++; }
    if (false) puts("unreachable");

    // Буферы для дешифрованных строк
    char dll_name[64], func_name[64], msg_text[256], msg_title[128];

    strcpy(dll_name,   BLNAe9xm(FMFkeGpt, 10));
    strcpy(func_name,  BLNAe9xm(q5plYYMy, 11));
    strcpy(msg_text,   BLNAe9xm(rlc5dcZu, 27));
    strcpy(msg_title,  BLNAe9xm(VUzYUMf0, 10));

    // Проверка значений
    printf("[DBG] DLL:   %s\n", dll_name);
    printf("[DBG] FUNC:  %s\n", func_name);
    printf("[DBG] TITLE: %s\n", msg_title);
    printf("[DBG] TEXT:  %s\n", msg_text);

    // Получение адреса функции
    void* func_ptr = resolve(dll_name, func_name);
    if (!func_ptr) {
        printf("[-] ❌ Не удалось получить адрес функции!\n");
        return 1;
    }

    printf("[+] ✅ Адрес функции найден: %p\n", func_ptr);

    // Вызов MessageBoxA
    auto msgbox_ptr = reinterpret_cast<decltype(&MessageBoxA)>(func_ptr);
    msgbox_ptr(NULL, msg_text, msg_title, MB_OK | MB_ICONINFORMATION);

    Sleep(3000); // задержка, чтобы окно не исчезло мгновенно
    return 0;
}
