char* IJeRoTQV(const unsigned char* data, int aurk5joF) {
    static char XYaUXrsf[1024];
    unsigned char wAeu1b8q = 210;
    for (int kDNrSySu = 0; kDNrSySu < aurk5joF; kDNrSySu++) {
        XYaUXrsf[kDNrSySu] = data[kDNrSySu] ^ wAeu1b8q;
        wAeu1b8q = (wAeu1b8q + 1) % 256;
    }
    XYaUXrsf[aurk5joF] = '\0';
    return XYaUXrsf;
};
wchar_t* IoJmUWae(const unsigned char* data, int aurk5joF) {
    static wchar_t XYaUXrsf[1024];
    unsigned char wAeu1b8q = 210;
    for (int kDNrSySu = 0; kDNrSySu < aurk5joF; kDNrSySu++) {
        XYaUXrsf[kDNrSySu] = (wchar_t)(data[kDNrSySu] ^ wAeu1b8q);
        wAeu1b8q = (wAeu1b8q + 1) % 256;
    }
    XYaUXrsf[aurk5joF] = L'\0';
    return XYaUXrsf;
};
const unsigned char A2Fz5lTX[] = {0xa7, 0xa1, 0xb7, 0xa0, 0xe1, 0xe0, 0xfc, 0xb6, 0xbe, 0xbe};
const unsigned char R2CdFTh6[] = {0x9f, 0xb7, 0xa1, 0xa1, 0xb3, 0xb5, 0xb7, 0x90, 0xbd, 0xaa, 0x93};
const unsigned char nvETOUwh[] = {0x96, 0x9e, 0x9e, 0xf2, 0x9b, 0xbc, 0xb8, 0xb7, 0xb1, 0xa6, 0xb7, 0xb6, 0xf3};
const unsigned char lDjIBdBO[] = {0x9d, 0xb0, 0xb4, 0xa7, 0xa1, 0xb1, 0xb3, 0xa6, 0xbd, 0xa0, 0xf2, 0x86, 0xb7, 0xa1, 0xa6};

#include <stdlib.h>




void* resolve(const char* dll, const char* func) {
    HMODULE hMod = LoadLibraryA(dll);
    return GetProcAddress(hMod, func);
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD yPECISm4, LPVOID lpReserved) {
    if (yPECISm4 == DLL_PROCESS_ATTACH) {
        FARPROC msgBox = (FARPROC)resolve(IJeRoTQV(A2Fz5lTX, 10), IJeRoTQV(R2CdFTh6, 11));
        if (msgBox) {
            typedef int (WINAPI* MsgBoxFunc)(HWND, LPCSTR, LPCSTR, UINT);
            MsgBoxFunc MessageBoxA_ptr = (MsgBoxFunc)msgBox;
            MessageBoxA_ptr(NULL, IJeRoTQV(nvETOUwh, 13), IJeRoTQV(lDjIBdBO, 15), MB_OK);
        }
    }
    return TRUE;
}
