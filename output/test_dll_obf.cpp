char* cSwgatMt(const unsigned char* data, int uQjgujjt) {
    static char pRtIs4H9[1024];
    unsigned char vVONONsj = 131;
    for (int duyRTjmJ = 0; duyRTjmJ < uQjgujjt; duyRTjmJ++) {
        pRtIs4H9[duyRTjmJ] = data[duyRTjmJ] ^ vVONONsj;
        vVONONsj = (vVONONsj + 1) % 256;
    }
    pRtIs4H9[uQjgujjt] = '\0';
    return pRtIs4H9;
};
wchar_t* GRmybrwR(const unsigned char* data, int uQjgujjt) {
    static wchar_t pRtIs4H9[1024];
    unsigned char vVONONsj = 131;
    for (int duyRTjmJ = 0; duyRTjmJ < uQjgujjt; duyRTjmJ++) {
        pRtIs4H9[duyRTjmJ] = (wchar_t)(data[duyRTjmJ] ^ vVONONsj);
        vVONONsj = (vVONONsj + 1) % 256;
    }
    pRtIs4H9[uQjgujjt] = L'\0';
    return pRtIs4H9;
};
const unsigned char DBimNi8I[] = {0xf6, 0xf0, 0xe6, 0xf1, 0xb0, 0xb1, 0xad, 0xe7, 0xef, 0xef};
const unsigned char ae78rmJ5[] = {0xce, 0xe6, 0xf0, 0xf0, 0xe2, 0xe4, 0xe6, 0xc1, 0xec, 0xfb, 0xc2};
const unsigned char uyyJupUZ[] = {0xc7, 0xcf, 0xcf, 0xa3, 0xca, 0xed, 0xe9, 0xe6, 0xe0, 0xf7, 0xe6, 0xe7, 0xa2};
const unsigned char V2x6TsYR[] = {0xcc, 0xe1, 0xe5, 0xf6, 0xf0, 0xe0, 0xe2, 0xf7, 0xec, 0xf1, 0xa3, 0xd7, 0xe6, 0xf0, 0xf7};

#include <stdlib.h>




void* resolve(const char* dll, const char* func) {
    HMODULE hMod = LoadLibraryA(dll);
    return GetProcAddress(hMod, func);
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD BPYDoY53, LPVOID lpReserved) {
    if (BPYDoY53 == DLL_PROCESS_ATTACH) {
        FARPROC msgBox = (FARPROC)resolve(cSwgatMt(DBimNi8I, 10), cSwgatMt(ae78rmJ5, 11));
        if (msgBox) {
            typedef int (WINAPI* MsgBoxFunc)(HWND, LPCSTR, LPCSTR, UINT);
            MsgBoxFunc MessageBoxA_ptr = (MsgBoxFunc)msgBox;
            MessageBoxA_ptr(NULL, cSwgatMt(uyyJupUZ, 13), cSwgatMt(V2x6TsYR, 15), MB_OK);
        }
    }
    return TRUE;
}
