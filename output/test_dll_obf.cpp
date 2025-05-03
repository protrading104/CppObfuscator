char* yQfgKysN(const unsigned char* data, int JaQkJgPW) {
    static char B2jlbWI7[1024];
    unsigned char PPOcesl8 = 238;
    for (int TcyBWdmQ = 0; TcyBWdmQ < JaQkJgPW; TcyBWdmQ++) {
        B2jlbWI7[TcyBWdmQ] = data[TcyBWdmQ] ^ PPOcesl8;
        PPOcesl8 = (PPOcesl8 + 1) % 256;
    }
    B2jlbWI7[JaQkJgPW] = '\0';
    return B2jlbWI7;
};
wchar_t* kLXxGTYu(const unsigned char* data, int JaQkJgPW) {
    static wchar_t B2jlbWI7[1024];
    unsigned char PPOcesl8 = 238;
    for (int TcyBWdmQ = 0; TcyBWdmQ < JaQkJgPW; TcyBWdmQ++) {
        B2jlbWI7[TcyBWdmQ] = (wchar_t)(data[TcyBWdmQ] ^ PPOcesl8);
        PPOcesl8 = (PPOcesl8 + 1) % 256;
    }
    B2jlbWI7[JaQkJgPW] = L'\0';
    return B2jlbWI7;
};
const unsigned char tLf9PKHL[] = {0x9b, 0x9d, 0x8b, 0x9c, 0xdd, 0xdc, 0xc0, 0x8a, 0x82, 0x82};
const unsigned char aVBXQklE[] = {0xa3, 0x8b, 0x9d, 0x9d, 0x8f, 0x89, 0x8b, 0xac, 0x81, 0x96, 0xaf};
const unsigned char G0oLTiKc[] = {0xaa, 0xa2, 0xa2, 0xce, 0xa7, 0x80, 0x84, 0x8b, 0x8d, 0x9a, 0x8b, 0x8a, 0xcf};
const unsigned char cU0it2wK[] = {0xa1, 0x8c, 0x88, 0x9b, 0x9d, 0x8d, 0x8f, 0x9a, 0x81, 0x9c, 0xce, 0xba, 0x8b, 0x9d, 0x9a};

#include <stdlib.h>




void* resolve(const char* dll, const char* func) {
    HMODULE hMod = LoadLibraryA(dll);
    return GetProcAddress(hMod, func);
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD jzdCu1hg, LPVOID lpReserved) {
    if (jzdCu1hg == DLL_PROCESS_ATTACH) {
        FARPROC msgBox = (FARPROC)resolve(yQfgKysN(tLf9PKHL, 10), yQfgKysN(aVBXQklE, 11));
        if (msgBox) {
            typedef int (WINAPI* MsgBoxFunc)(HWND, LPCSTR, LPCSTR, UINT);
            MsgBoxFunc MessageBoxA_ptr = (MsgBoxFunc)msgBox;
            MessageBoxA_ptr(NULL, yQfgKysN(G0oLTiKc, 13), yQfgKysN(cU0it2wK, 15), MB_OK);
        }
    }
    return TRUE;
}
