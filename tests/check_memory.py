import ctypes

# Определяем структуру MEMORY_BASIC_INFORMATION
class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_ulong),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.c_ulong),
        ("Protect", ctypes.c_ulong),
        ("Type", ctypes.c_ulong),
    ]

# Укажи нужный адрес (например, RIP, который ты проверяешь)
rip_value = 0x100000

# Создаём экземпляр структуры
mbi = MEMORY_BASIC_INFORMATION()

# Вызываем VirtualQuery
status = ctypes.windll.kernel32.VirtualQuery(ctypes.c_void_p(rip_value), ctypes.byref(mbi), ctypes.sizeof(mbi))

if status == 0:
    print("❌ VirtualQuery не смог получить информацию о памяти!")
else:
    print(f"✅ VirtualQuery выполнен успешно:")
    print(f"   BaseAddress: {hex(mbi.BaseAddress)}")
    print(f"   AllocationProtect: {hex(mbi.AllocationProtect)}")
    print(f"   State: {hex(mbi.State)}")  # Должно быть 0x1000 (MEM_COMMIT)
    print(f"   Protect: {hex(mbi.Protect)}")  # Должно быть 0x40 (PAGE_EXECUTE_READWRITE)
