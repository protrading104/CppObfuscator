use std::ffi::CString;
use winapi::um::libloaderapi::{GetModuleHandleA, GetProcAddress};
use winapi::shared::minwindef::HMODULE;
use obfstr::obfstr;
use crate::log;

/// Структура для хранения номеров системных вызовов
#[derive(Debug, Clone)]
pub struct SyscallNumbers {
    pub nt_allocate_virtual_memory: u16,
    pub nt_protect_virtual_memory: u16,
    pub nt_write_virtual_memory: u16,
    pub nt_read_virtual_memory: u16,
    pub nt_create_thread: u16,
    pub nt_resume_thread: u16,
    pub nt_suspend_thread: u16,
    pub nt_terminate_thread: u16,
    pub nt_query_information_process: u16,
    pub nt_set_information_thread: u16,
}

impl SyscallNumbers {
    /// Создает новый экземпляр и извлекает все syscall numbers
    pub fn new() -> Result<Self, String> {
        let ntdll = unsafe { GetModuleHandleA(obfstr!("ntdll.dll\0").as_ptr() as *const i8) };
        if ntdll.is_null() {
            return Err("Failed to get ntdll handle".to_string());
        }

        log!("[DEBUG] Successfully got ntdll handle: {:p}", ntdll);

        Ok(SyscallNumbers {
            nt_allocate_virtual_memory: extract_syscall_number(ntdll, obfstr!("NtAllocateVirtualMemory"))?,
            nt_protect_virtual_memory: extract_syscall_number(ntdll, obfstr!("NtProtectVirtualMemory"))?,
            nt_write_virtual_memory: extract_syscall_number(ntdll, obfstr!("NtWriteVirtualMemory"))?,
            nt_read_virtual_memory: extract_syscall_number(ntdll, obfstr!("NtReadVirtualMemory"))?,
            nt_create_thread: extract_syscall_number(ntdll, obfstr!("NtCreateThread"))?,
            nt_resume_thread: extract_syscall_number(ntdll, obfstr!("NtResumeThread"))?,
            nt_suspend_thread: extract_syscall_number(ntdll, obfstr!("NtSuspendThread"))?,
            nt_terminate_thread: extract_syscall_number(ntdll, obfstr!("NtTerminateThread"))?,
            nt_query_information_process: extract_syscall_number(ntdll, obfstr!("NtQueryInformationProcess"))?,
            nt_set_information_thread: extract_syscall_number(ntdll, obfstr!("NtSetInformationThread"))?,
        })
    }

    /// Выводит все найденные syscall numbers для диагностики
    pub fn print_syscalls(&self) {
        log!("[INFO] Extracted Syscall Numbers:");
        log!("  NtAllocateVirtualMemory: 0x{:02X}", self.nt_allocate_virtual_memory);
        log!("  NtProtectVirtualMemory:  0x{:02X}", self.nt_protect_virtual_memory);
        log!("  NtWriteVirtualMemory:    0x{:02X}", self.nt_write_virtual_memory);
        log!("  NtReadVirtualMemory:     0x{:02X}", self.nt_read_virtual_memory);
        log!("  NtCreateThread:          0x{:02X}", self.nt_create_thread);
        log!("  NtResumeThread:          0x{:02X}", self.nt_resume_thread);
        log!("  NtSuspendThread:         0x{:02X}", self.nt_suspend_thread);
        log!("  NtTerminateThread:       0x{:02X}", self.nt_terminate_thread);
        log!("  NtQueryInformationProcess: 0x{:02X}", self.nt_query_information_process);
        log!("  NtSetInformationThread:  0x{:02X}", self.nt_set_information_thread);
    }
}

/// Извлекает syscall number из конкретной функции ntdll.dll
fn extract_syscall_number(ntdll: HMODULE, function_name: &str) -> Result<u16, String> {
    let func_name = CString::new(function_name)
        .map_err(|_| format!("{}: {}", obfstr!("Invalid function name"), function_name))?;
    
    let func_addr = unsafe { GetProcAddress(ntdll, func_name.as_ptr()) };
    if func_addr.is_null() {
        return Err(format!("{}: {}", obfstr!("Failed to get address for"), function_name));
    }

    log!("[DEBUG] {} address: {:p}", function_name, func_addr);

    // Читаем первые 32 байта функции для анализа
    let bytes = unsafe { std::slice::from_raw_parts(func_addr as *const u8, 32) };
    
    // Выводим hex dump для диагностики
    #[cfg(debug_assertions)]
    {
        print!("[DEBUG] {} bytes: ", function_name);
        for i in 0..std::cmp::min(16, bytes.len()) {
            print!("{:02X} ", bytes[i]);
        }
        log!();
    }

    // Паттерн 1: x64 Windows 10/11 - mov r10, rcx; mov eax, imm32; syscall
    // Байты: 4C 8B D1 B8 XX XX 00 00 0F 05
    for i in 0..24 {
        if i + 7 < bytes.len() && 
           bytes[i] == 0x4C && bytes[i + 1] == 0x8B && bytes[i + 2] == 0xD1 &&  // mov r10, rcx
           bytes[i + 3] == 0xB8 {  // mov eax, imm32
            let syscall_num = u16::from_le_bytes([bytes[i + 4], bytes[i + 5]]);
            log!("[DEBUG] {} syscall number: 0x{:02X} (pattern 1)", function_name, syscall_num);
            return Ok(syscall_num);
        }
    }

    // Паттерн 2: Старые версии Windows - mov eax, imm32; mov edx, imm32; syscall
    // Байты: B8 XX XX 00 00 BA XX XX XX XX 0F 05
    for i in 0..28 {
        if i + 5 < bytes.len() && bytes[i] == 0xB8 {  // mov eax, imm32
            let syscall_num = u16::from_le_bytes([bytes[i + 1], bytes[i + 2]]);
            // Проверяем, что следом идет корректный паттерн
            if i + 10 < bytes.len() && bytes[i + 5] == 0xBA {  // mov edx, imm32
                log!("[DEBUG] {} syscall number: 0x{:02X} (pattern 2)", function_name, syscall_num);
                return Ok(syscall_num);
            }
        }
    }

    // Паттерн 3: Windows 11 22H2+ с дополнительными инструкциями
    // mov r10, rcx; mov eax, imm32; test byte ptr [...], 1; jne ...; syscall
    for i in 0..20 {
        if i + 10 < bytes.len() &&
           bytes[i] == 0x4C && bytes[i + 1] == 0x8B && bytes[i + 2] == 0xD1 &&  // mov r10, rcx
           bytes[i + 3] == 0xB8 {  // mov eax, imm32
            
            let syscall_num = u16::from_le_bytes([bytes[i + 4], bytes[i + 5]]);
            
            // Проверяем наличие syscall инструкции дальше в коде
            for j in (i + 6)..(i + 20) {
                if j + 1 < bytes.len() && bytes[j] == 0x0F && bytes[j + 1] == 0x05 {  // syscall
                    log!("[DEBUG] {} syscall number: 0x{:02X} (pattern 3)", function_name, syscall_num);
                    return Ok(syscall_num);
                }
            }
        }
    }

    Err(format!("Could not extract syscall number for {} - no known pattern found", function_name))
}

/// Проверяет, поддерживаются ли indirect syscalls в текущей системе
pub fn is_indirect_syscall_supported() -> bool {
    match SyscallNumbers::new() {
        Ok(syscalls) => {
            // Проверяем, что базовые syscalls найдены
            syscalls.nt_allocate_virtual_memory > 0 && 
            syscalls.nt_protect_virtual_memory > 0
        },
        Err(_) => false,
    }
}

/// Получает версию Windows для адаптации паттернов
pub fn get_windows_version() -> String {
    use winapi::um::sysinfoapi::GetVersionExA;
    use winapi::um::winnt::OSVERSIONINFOA;
    use std::mem;

    let mut version_info: OSVERSIONINFOA = unsafe { mem::zeroed() };
    version_info.dwOSVersionInfoSize = mem::size_of::<OSVERSIONINFOA>() as u32;

    let success = unsafe { GetVersionExA(&mut version_info) };
    if success != 0 {
        format!("{}.{}.{}", 
               version_info.dwMajorVersion, 
               version_info.dwMinorVersion, 
               version_info.dwBuildNumber)
    } else {
        "Unknown".to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_syscall_extraction() {
        let result = SyscallNumbers::new();
        assert!(result.is_ok(), "Failed to extract syscall numbers: {:?}", result.err());
        
        let syscalls = result.unwrap();
        assert!(syscalls.nt_allocate_virtual_memory > 0);
        assert!(syscalls.nt_protect_virtual_memory > 0);
        
        syscalls.print_syscalls();
    }

    #[test]
    fn test_indirect_syscall_support() {
        let supported = is_indirect_syscall_supported();
        log!("Indirect syscalls supported: {}", supported);
        assert!(supported, "Indirect syscalls should be supported on this system");
    }

    #[test]
    fn test_windows_version() {
        let version = get_windows_version();
        log!("Windows version: {}", version);
        assert!(!version.is_empty());
    }
}
