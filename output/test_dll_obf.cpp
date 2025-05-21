char* wPbsddcf(const unsigned char* data, int VvWF9nUA) {
    static char UGMM4xyN[1024];
    unsigned char oDlbdSk2 = 43;
    for (int TbuMcGle = 0; TbuMcGle < VvWF9nUA; TbuMcGle++) {
        UGMM4xyN[TbuMcGle] = data[TbuMcGle] ^ oDlbdSk2;
        oDlbdSk2 = (oDlbdSk2 + 1) % 256;
    }
    UGMM4xyN[VvWF9nUA] = '\0';
    return UGMM4xyN;
};
wchar_t* DXZPKWkJ(const unsigned char* data, int VvWF9nUA) {
    static wchar_t UGMM4xyN[1024];
    unsigned char oDlbdSk2 = 43;
    for (int TbuMcGle = 0; TbuMcGle < VvWF9nUA; TbuMcGle++) {
        UGMM4xyN[TbuMcGle] = (wchar_t)(data[TbuMcGle] ^ oDlbdSk2);
        oDlbdSk2 = (oDlbdSk2 + 1) % 256;
    }
    UGMM4xyN[VvWF9nUA] = L'\0';
    return UGMM4xyN;
};
const unsigned char cHj3sAEC[] = {0x5e, 0x58, 0x4e, 0x59, 0x18, 0x19, 0x05, 0x4f, 0x47, 0x47};
const unsigned char B9Ml0EiA[] = {0x66, 0x4e, 0x58, 0x58, 0x4a, 0x4c, 0x4e, 0x69, 0x44, 0x53, 0x6a};
const unsigned char r88MefaI[] = {0x6f, 0x67, 0x67, 0x0b, 0x62, 0x45, 0x41, 0x4e, 0x48, 0x5f, 0x4e, 0x4f, 0x0a};
const unsigned char XLfliKOi[] = {0x64, 0x49, 0x4d, 0x5e, 0x58, 0x48, 0x4a, 0x5f, 0x44, 0x59, 0x0b, 0x7f, 0x4e, 0x58, 0x5f};

#include <stdlib.h>




void* resolve(const char* dll, const char* func) {
    HMODULE hMod = LoadLibraryA(dll);
    return GetProcAddress(hMod, func);
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD YHfl2RvA, LPVOID lpReserved) {
    if (YHfl2RvA == DLL_PROCESS_ATTACH) {
        FARPROC msgBox = (FARPROC)resolve(wPbsddcf(cHj3sAEC, 10), wPbsddcf(B9Ml0EiA, 11));
        if (msgBox) {
            typedef int (WINAPI* MsgBoxFunc)(HWND, LPCSTR, LPCSTR, UINT);
            MsgBoxFunc MessageBoxA_ptr = (MsgBoxFunc)msgBox;
            MessageBoxA_ptr(NULL, wPbsddcf(r88MefaI, 13), wPbsddcf(XLfliKOi, 15), MB_OK);
        }
    }
    return TRUE;
}
