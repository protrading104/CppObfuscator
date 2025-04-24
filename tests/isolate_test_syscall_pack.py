# -*- coding: utf-8 -*-
import logging
import pefile

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("TestSyscallPack")


def get_real_syscall_index(syscall_name):
    """Читаем ntdll.dll и сверяем syscall index"""
    ntdll_path = "C:\\Windows\\System32\\ntdll.dll"
    pe = pefile.PE(ntdll_path)
    for entry in pe.DIRECTORY_ENTRY_EXPORT.symbols:
        if entry.name and syscall_name.encode() in entry.name:
            return entry.ordinal
    return None


def test_syscall_pack(syscall_index):
    logger.info("\n🚀 Тестируем syscall_index: %d (hex=%s)", syscall_index, hex(syscall_index))

    real_index = get_real_syscall_index("NtQuerySystemInformation")
    if real_index is not None:
        logger.info("📌 Реальный syscall_index из ntdll: %d (hex=%s)", real_index, hex(real_index))
        if real_index != syscall_index:
            logger.warning("⚠️ Разница между вычисленным и реальным syscall_index!")

    # ✅ Новый метод: ручная сборка shellcode без struct.pack()
    try:
        shellcode = b"\x4c\x8b\xd1"  # mov r10, rcx
        shellcode += b"\xb8" + syscall_index.to_bytes(4, 'little')  # mov eax, syscall_index
        shellcode += b"\x0f\x05"  # syscall
        
        logger.info("✅ Shellcode: %s, len=%d", shellcode.hex(), len(shellcode))

    except Exception as e:
        logger.error("❌ Ошибка формирования shellcode: %s", e)


if __name__ == "__main__":
    test_syscall_pack(515)  # NtQuerySystemInformation
    test_syscall_pack(4660)  # 0x1234 (проверка на 16-битные значения)
    test_syscall_pack(305419896)  # 0x12345678 (проверка на 32-битные значения)
