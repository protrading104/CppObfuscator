use std::{
    thread,
    time::{Duration, Instant},
};

use ntapi::ntpebteb::NtCurrentTeb;
use windows::Win32::System::Diagnostics::Debug::IsDebuggerPresent;

#[repr(C)]
struct PEB {
    _reserved: [u8; 2],
    BeingDebugged: u8,
    _pad: [u8; 1],
}

#[repr(C)]
struct TEB {
    _reserved: [u8; 0x60],
    ProcessEnvironmentBlock: *const PEB,
}

pub fn comprehensive_debug_check() -> bool {
    unsafe {
        if IsDebuggerPresent().as_bool() {
            return true;
        }

        let teb = NtCurrentTeb() as *const TEB;
        let peb = (*teb).ProcessEnvironmentBlock;
        if (*peb).BeingDebugged != 0 {
            return true;
        }

        let start = Instant::now();
        thread::sleep(Duration::from_millis(100));
        if start.elapsed() < Duration::from_millis(90) {
            return true;
        }
    }
    false
}
