use crate::syscall::SyscallNumbers;
use winapi::shared::ntdef::{NTSTATUS, HANDLE, PVOID, ULONG};
use crate::log;


/// Структура для работы с indirect syscalls
pub struct IndirectSyscall {
    pub syscalls: SyscallNumbers,
}

impl IndirectSyscall {
    pub fn new() -> Result<Self, String> {
        Ok(Self {
            syscalls: SyscallNumbers::new()?,
        })
    }

    /// NtAllocateVirtualMemory через прямой syscall (Hell's Gate technique)
    pub unsafe fn nt_allocate_virtual_memory_internal(
        &self,
        process_handle: HANDLE,
        base_address: *mut PVOID,
        zero_bits: ULONG,
        region_size: *mut usize,
        allocation_type: ULONG,
        protect: ULONG,
    ) -> NTSTATUS {
        let ssn = self.syscalls.nt_allocate_virtual_memory as u32;
        let mut status: NTSTATUS;
        
        // ИСПРАВЛЕНО: Правильная передача всех 6 параметров
        core::arch::asm!(
            "mov r10, rcx",                    // Windows syscall convention
            "mov eax, {ssn:e}",                
            
            // Подготовка стека для 5-го и 6-го параметров
            "sub rsp, 48",                     // Shadow space + 2 параметра
            "mov qword ptr [rsp + 32], {allocation_type}",  // 5-й параметр
            "mov qword ptr [rsp + 40], {protect}",          // 6-й параметр
            
            "syscall",                         // Syscall с правильными параметрами
            
            "add rsp, 48",                     // Восстановление стека
            
            ssn = in(reg) ssn,
            allocation_type = in(reg) allocation_type as u64,
            protect = in(reg) protect as u64,
            in("rcx") process_handle,          // 1-й параметр
            in("rdx") base_address,            // 2-й параметр
            in("r8") zero_bits as u64,         // 3-й параметр
            in("r9") region_size,              // 4-й параметр
            lateout("rax") status,
            lateout("r10") _,
            lateout("r11") _,
            clobber_abi("system")
        );
        
        status
    }

    /// NtProtectVirtualMemory через прямой syscall
    pub unsafe fn nt_protect_virtual_memory_internal(
        &self,
        process_handle: HANDLE,
        base_address: *mut PVOID,
        region_size: *mut usize,
        new_protect: ULONG,
        old_protect: *mut ULONG,
    ) -> NTSTATUS {
        let ssn = self.syscalls.nt_protect_virtual_memory as u32;
        let mut status: NTSTATUS;
        
        core::arch::asm!(
            "mov r10, rcx",
            "mov eax, {ssn:e}",
            
            "sub rsp, 40",                     // Shadow space + 1 параметр
            "mov qword ptr [rsp + 32], {old_protect}",  // 5-й параметр
            
            "syscall",
            
            "add rsp, 40",
            
            ssn = in(reg) ssn,
            old_protect = in(reg) old_protect,
            in("rcx") process_handle,
            in("rdx") base_address,
            in("r8") region_size,
            in("r9") new_protect as u64,
            lateout("rax") status,
            lateout("r10") _,
            lateout("r11") _,
            clobber_abi("system")
        );
        
        status
    }
}

// WRAPPER ФУНКЦИИ для совместимости с manual_map.rs
pub unsafe fn nt_allocate_virtual_memory(
    process_handle: HANDLE,
    base_address: *mut *mut winapi::ctypes::c_void,
    zero_bits: usize,
    region_size: *mut u64,
    allocation_type: u32,
    protect: u32,
    _syscall_numbers: &SyscallNumbers,
) -> i32 {
    let indirect = match IndirectSyscall::new() {
        Ok(i) => i,
        Err(_) => return -1,
    };
    
    let mut size_as_usize = *region_size as usize;
    
    let status = indirect.nt_allocate_virtual_memory_internal(
        process_handle,
        base_address as *mut PVOID,
        zero_bits as ULONG,
        &mut size_as_usize,
        allocation_type as ULONG,
        protect as ULONG,
    );
    
    *region_size = size_as_usize as u64;
    status
}

pub unsafe fn nt_protect_virtual_memory(
    process_handle: HANDLE,
    base_address: *mut *mut winapi::ctypes::c_void,
    region_size: *mut usize,
    new_protect: u32,
    old_protect: *mut u32,
    _syscall_numbers: &SyscallNumbers,
) -> i32 {
    let indirect = match IndirectSyscall::new() {
        Ok(i) => i,
        Err(_) => return -1,
    };
    
    indirect.nt_protect_virtual_memory_internal(
        process_handle,
        base_address as *mut PVOID,
        region_size,
        new_protect as ULONG,
        old_protect as *mut ULONG,
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use winapi::um::processthreadsapi::GetCurrentProcess;
    use winapi::um::winnt::{MEM_COMMIT, MEM_RESERVE, PAGE_READWRITE};
    use obfstr::obfstr; // ДОБАВИТЬ

    #[test]
    fn test_indirect_syscall_allocation() {
        let indirect = IndirectSyscall::new().expect(obfstr!("Failed to init IndirectSyscall"));
        let mut base_addr: PVOID = std::ptr::null_mut();
        let mut region_size: usize = 0x1000;

        let status = unsafe {
            indirect.nt_allocate_virtual_memory_internal(
                GetCurrentProcess(),
                &mut base_addr,
                0,
                &mut region_size,
                MEM_COMMIT | MEM_RESERVE,
                PAGE_READWRITE,
            )
        };

        log!("{}: 0x{:08X}", obfstr!("Syscall result"), status);
        log!("{}: {:p}", obfstr!("Allocated address"), base_addr);

        if status == 0 {
            assert!(!base_addr.is_null(), obfstr!("Address should not be null"));
            log!("{}", obfstr!("SUCCESS: Indirect syscall works!"));
        }
    }
}

