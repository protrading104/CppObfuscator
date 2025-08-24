
Runtime Loader (Rust)
Описание функций и модулей подмодуля runtime_loader_rust.

Структура проекта
runtime_loader_rust/
├── src/
│   ├── main.rs
│   ├── crypto.rs
│   ├── utils.rs
│   ├── edr/
│   │   ├── amsi.rs
│   │   ├── anti_debug.rs
│   │   ├── etw.rs
│   │   ├── stealth.rs
│   │   └── unhook.rs
│   ├── memory/
│   │   ├── manual_map.rs
│   │   ├── pe_loader.rs
│   │   └── stealth.rs
│   └── syscall/
│       ├── indirect_syscall.rs
│       └── ntdll.rs
Основные файлы
main.rs
decrypt_aes_ecb(ciphertext, key) -> Vec<u8> — расшифровка AES‑128 ECB.

main() -> Result<(), Box<dyn Error>> — точка входа: анти‑отладка, EDR‑обход, расшифровка и исполнение PE в памяти.

crypto.rs
get_decryption_key() -> [u8; 16] — получение встроенного AES‑ключа.

utils.rs
read_file(file_path) -> io::Result<Vec<u8>> — чтение файла целиком.

log! — макрос для отладочного вывода (только в debug режиме).

Модуль edr
amsi.rs
patch_amsi() -> bool — патчит AmsiScanBuffer, возвращая ложь.

anti_debug.rs
comprehensive_debug_check() -> bool — совмещённая проверка наличия отладчика.

etw.rs
patch_etw() -> bool — отключает EtwEventWrite, NtTraceEvent и EtwEventWriteFull.

patch_etw_function(...) — служебная функция патчинга указанной ETW‑функции.

stealth.rs
mimic_legitimate_process() -> bool — подмена родителя процесса.

mimic_system_activity() — имитация безопасной активности (реестр, файловая система).

unhook.rs
unhook_ntdll() -> Result<(), String> — удаление inline‑хуков в ntdll.dll.

map_known_dll(...) — отображает «чистую» копию ntdll.dll.

find_text_section() — ищет .text секцию загруженной ntdll.dll.

patch_section(...) — копирует оригинальные байты поверх хуков.

Модуль memory
stealth.rs
EncryptedMemoryRegion

new(base, size) — описание региона.

is_valid_memory_region() — проверка корректности адреса.

change_protection_to_rw() / restore_original_protection() — управление правами доступа.

encrypt() / decrypt() — XOR‑шифрование памяти.

is_encrypted() — статус шифрования.

randomize_allocation_pattern() -> usize — рандомизация базового адреса.

MemoryStealthManager

new(), add_region(), encrypt_all(), decrypt_all(), start_background_encryption().

pe_loader.rs
PELoader

new(pe_data) -> Result<Self, String> — парсинг PE.

get_image_size(), get_pe_data(), get_entry_point(), get_sections(), pe_file().

SectionInfo — структура описания секции.

manual_map.rs
ManualMapper

new(pe_loader) -> Result<Self, String> — выделение памяти (syscall/VirtualAlloc).

map_sections(), set_section_protection(...), resolve_imports().

process_delayed_imports(...), collect_import_descriptors(...).

rva_to_file_offset(...), resolve_dll_imports(...).

process_relocations(...), initialize_tls(), execute() — запуск payload.

Модуль syscall
ntdll.rs
SyscallNumbers

new() -> Result<Self, String> — извлечение номеров системных вызовов.

print_syscalls() — вывод найденных SSN.

extract_syscall_number(...) — парсер кода функций ntdll.dll.

is_indirect_syscall_supported() -> bool — проверка поддержки indirect syscalls.

get_windows_version() -> String — версия Windows.

indirect_syscall.rs
IndirectSyscall

new(), nt_allocate_virtual_memory_internal(...), nt_protect_virtual_memory_internal(...).

Обёртки nt_allocate_virtual_memory(...) и nt_protect_virtual_memory(...) — совместимы с ManualMapper.
