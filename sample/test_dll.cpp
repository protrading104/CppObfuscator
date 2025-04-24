#include <windows.h>
#include <stdio.h>

void* resolve(const char* dll, const char* func) {
    HMODULE hMod = LoadLibraryA(dll);
    return GetProcAddress(hMod, func);
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpReserved) {
    if (fdwReason == DLL_PROCESS_ATTACH) {
        FARPROC msgBox = (FARPROC)resolve("user32.dll", "MessageBoxA");
        if (msgBox) {
            typedef int (WINAPI* MsgBoxFunc)(HWND, LPCSTR, LPCSTR, UINT);
            MsgBoxFunc MessageBoxA_ptr = (MsgBoxFunc)msgBox;
            MessageBoxA_ptr(NULL, "DLL Injected!", "Obfuscator Test", MB_OK);
        }
    }
    return TRUE;
}
