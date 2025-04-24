import struct

syscall_index = 515  # Тестовый номер системного вызова

# Определяем правильный формат
if syscall_index < 65536:
    fmt = "<BBHBB"  # 5 элементов (ожидает 5)
    syscall_bytes = struct.pack("H", syscall_index)  # 2 байта
else:
    fmt = "<BBIB"  # 5 элементов (ожидает 5)
    syscall_bytes = struct.pack("I", syscall_index)  # 4 байта

# Лог перед упаковкой
print(f"🔍 Используемый формат: {fmt}, syscall_index={syscall_index} (hex={hex(syscall_index)})")
print(f"📄 Упакованные байты syscall_index: {syscall_bytes.hex()}")

# Формируем shellcode вручную
try:
    shellcode = struct.pack(
        fmt[:-1],  # Убираем последнюю букву (чтобы передать `syscall_bytes` вручную)
        0x4C, 0x8B,  # mov r10, rcx (2 байта)
        0xD1,        # mov r10, rcx (1 байт)
        0xB8,        # mov eax, <syscall_number> (1 байт)
    ) + syscall_bytes + struct.pack("BB", 0x0F, 0x05)  # syscall (2 байта)

    print(f"✅ Shellcode: {shellcode.hex()}, len={len(shellcode)}")
except struct.error as e:
    print(f"❌ Ошибка struct.pack(): {e}")
