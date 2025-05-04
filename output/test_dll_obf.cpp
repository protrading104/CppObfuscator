char* ASodQxUi(const unsigned char* data, int ICVqCPRR) {
    static char tcTEUTNQ[1024];
    unsigned char fkvbFFGq = 175;
    for (int dMIzqJGM = 0; dMIzqJGM < ICVqCPRR; dMIzqJGM++) {
        tcTEUTNQ[dMIzqJGM] = data[dMIzqJGM] ^ fkvbFFGq;
        fkvbFFGq = (fkvbFFGq + 1) % 256;
    }
    tcTEUTNQ[ICVqCPRR] = '\0';
    return tcTEUTNQ;
};
wchar_t* kbJFhDVt(const unsigned char* data, int ICVqCPRR) {
    static wchar_t tcTEUTNQ[1024];
    unsigned char fkvbFFGq = 175;
    for (int dMIzqJGM = 0; dMIzqJGM < ICVqCPRR; dMIzqJGM++) {
        tcTEUTNQ[dMIzqJGM] = (wchar_t)(data[dMIzqJGM] ^ fkvbFFGq);
        fkvbFFGq = (fkvbFFGq + 1) % 256;
    }
    tcTEUTNQ[ICVqCPRR] = L'\0';
    return tcTEUTNQ;
};
const unsigned char SvNSL98u[] = {0xda, 0xdc, 0xca, 0xdd, 0x9c, 0x9d, 0x81, 0xcb, 0xc3, 0xc3};
const unsigned char Gd0trPOI[] = {0xe2, 0xca, 0xdc, 0xdc, 0xce, 0xc8, 0xca, 0xed, 0xc0, 0xd7, 0xee};
const unsigned char wHPoXo9t[] = {0xeb, 0xe3, 0xe3, 0x8f, 0xe6, 0xc1, 0xc5, 0xca, 0xcc, 0xdb, 0xca, 0xcb, 0x8e};
const unsigned char WtmvFqCO[] = {0xe0, 0xcd, 0xc9, 0xda, 0xdc, 0xcc, 0xce, 0xdb, 0xc0, 0xdd, 0x8f, 0xfb, 0xca, 0xdc, 0xdb};

#include <stdlib.h>




void* resolve(const char* dll, const char* func) {
    HMODULE hMod = LoadLibraryA(dll);
    return GetProcAddress(hMod, func);
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD b9myXBJz, LPVOID lpReserved) {
    if (b9myXBJz == DLL_PROCESS_ATTACH) {
        FARPROC msgBox = (FARPROC)resolve(ASodQxUi(SvNSL98u, 10), ASodQxUi(Gd0trPOI, 11));
        if (msgBox) {
            typedef int (WINAPI* MsgBoxFunc)(HWND, LPCSTR, LPCSTR, UINT);
            MsgBoxFunc MessageBoxA_ptr = (MsgBoxFunc)msgBox;
            MessageBoxA_ptr(NULL, ASodQxUi(wHPoXo9t, 13), ASodQxUi(WtmvFqCO, 15), MB_OK);
        }
    }
    return TRUE;
}
