# -*- coding: utf-8 -*-
import ctypes
import logging
from keystone import Ks, KS_ARCH_X86, KS_MODE_64

# Подключаем модули шифрования
from crypto.aes import AES128
from crypto.rc4 import RC4Cipher
from crypto.xor_mask import RollingXOR

class JITCompiler:
    def __init__(self):
        """Инициализация JIT-компилятора"""
        self.logger = self._setup_logger()
        self.kernel32 = ctypes.windll.kernel32

        # Указываем правильные типы аргументов для API
        self.kernel32.GetProcessHeap.restype = ctypes.c_void_p
        self.kernel32.HeapAlloc.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_size_t]
        self.kernel32.HeapAlloc.restype = ctypes.c_void_p
        self.kernel32.HeapFree.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p]
        self.kernel32.HeapFree.restype = ctypes.c_int  # BOOL

        # Ключи шифрования (можно делать генерацию случайных ключей)
        self.aes_key = b"1234567890abcdef"  # Ровно 16 байт
        self.rc4_key = b"myRC4secretKEY"
        self.xor_key = b"\xAB\xCD\xEF"

        self.aes = AES128(self.aes_key)
        self.rc4 = RC4Cipher(self.rc4_key)
        self.xor = RollingXOR(self.xor_key)

    def _setup_logger(self):
        """Настройка логирования"""
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
        return logging.getLogger("JITCompiler")

    def assemble_shellcode(self, asm_code):
        """Компилирует ассемблерный код в shell-код (байт-код)"""
        self.logger.info("Компиляция shell-кода...")
        ks = Ks(KS_ARCH_X86, KS_MODE_64)
        encoding, _ = ks.asm(asm_code)
        shellcode = bytes(encoding)
        self.logger.info(f"Скомпилированный shell-код: {shellcode.hex()}")
        return shellcode

    def encrypt_shellcode(self, shellcode: bytes) -> bytes:
        """🔒 Шифрует shell-код перед выполнением"""
        self.logger.info("🔒 Шифруем shell-код...")
        encrypted = self.aes.encrypt(shellcode)
        encrypted = self.rc4.encrypt(encrypted)
        encrypted = self.xor.encrypt(encrypted)
        self.logger.info(f"🔒 Зашифрованный shell-код: {encrypted.hex()}")
        return encrypted

    def decrypt_shellcode(self, shellcode: bytes) -> bytes:
        """🔓 Дешифрует shell-код перед выполнением"""
        decrypted = self.xor.decrypt(shellcode)
        decrypted = self.rc4.decrypt(decrypted)
        decrypted = self.aes.decrypt(decrypted)
        self.logger.info(f"🔓 Расшифрованный shell-код: {decrypted.hex()}")
        return decrypted

    def execute_shellcode(self, shellcode):
        """Исполняет ЗАШИФРОВАННЫЙ shell-код"""
        self.logger.info("Исполнение shell-кода в памяти...")

        # 🔒 Шифруем shell-код перед загрузкой
        encrypted_shellcode = self.encrypt_shellcode(shellcode)

        # 🔓 Дешифруем перед запуском
        decrypted_shellcode = self.decrypt_shellcode(encrypted_shellcode)

        size = len(decrypted_shellcode)
        if size == 0:
            raise ValueError("Ошибка: Shell-код пустой!")

        # Получаем heap текущего процесса
        heap = self.kernel32.GetProcessHeap()
        if not heap:
            raise MemoryError("Ошибка получения хендла к процессному heap")

        self.logger.info(f"✅ Получен heap: {hex(heap)}")

        # Выделяем память через HeapAlloc()
        ptr = self.kernel32.HeapAlloc(heap, 0x8, size)  # HEAP_ZERO_MEMORY

        if not ptr or ptr == 0:
            error_code = self.kernel32.GetLastError()
            raise MemoryError(f"❌ Ошибка выделения памяти через HeapAlloc (размер: {size}, код ошибки: {error_code})")

        self.logger.info(f"✅ Выделена память через HeapAlloc: {hex(ptr)} (размер: {size})")

        # Делаем память исполняемой с помощью VirtualProtect
        PAGE_EXECUTE_READWRITE = 0x40
        old_protect = ctypes.c_ulong()
        ptr_cvoid = ctypes.c_void_p(ptr)
        success = self.kernel32.VirtualProtect(ptr_cvoid, size, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))

        if not success:
            error_code = self.kernel32.GetLastError()
            self.kernel32.HeapFree(heap, 0, ptr)
            raise MemoryError(f"❌ Ошибка VirtualProtect (код ошибки: {error_code})")

        self.logger.info(f"✅ Память сделана исполняемой: {hex(ptr)}")

        # Записываем shell-код в выделенную память
        ctypes.memmove(ptr, decrypted_shellcode, size)

        # Проверяем содержимое памяти перед вызовом
        try:
            mem_value = ctypes.string_at(ptr, size)
            self.logger.info(f"📄 Дамп памяти перед выполнением: {mem_value.hex()}")
        except Exception as e:
            self.logger.error(f"❌ Ошибка чтения памяти перед выполнением: {e}")
            self.kernel32.HeapFree(heap, 0, ptr)
            raise MemoryError("Ошибка доступа к памяти перед выполнением")

        # Создаем исполняемую функцию с использованием WINFUNCTYPE
        func_type = ctypes.WINFUNCTYPE(ctypes.c_void_p)
        jit_function = func_type(ptr)

        # Лог перед вызовом
        self.logger.info(f"🚀 Запуск shell-кода по адресу: {hex(ptr)}")

        try:
            jit_function()  # Исполняем код
        except Exception as e:
            self.logger.error(f"❌ Ошибка во время выполнения shell-кода: {e}")
            self.kernel32.HeapFree(heap, 0, ptr)
            raise MemoryError("Ошибка при выполнении shell-кода")

        # Освобождаем память после выполнения
        success = self.kernel32.HeapFree(heap, 0, ptr)
        if not success:
            self.logger.error(f"❌ Ошибка освобождения памяти HeapFree (адрес: {hex(ptr)})")

        self.logger.info("✅ Shell-код выполнен и память освобождена.")
