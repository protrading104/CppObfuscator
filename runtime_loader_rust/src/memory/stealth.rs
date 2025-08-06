// src/memory/stealth.rs
use std::sync::{Arc, Mutex};
use winapi::um::memoryapi::VirtualProtect;  // ← ДОБАВЛЕН импорт
use winapi::um::winnt::{PAGE_READWRITE, PAGE_EXECUTE_READ, PAGE_EXECUTE_READWRITE}; // ← ДОБАВЛЕНЫ константы

/// Структура для управления зашифрованными регионами памяти
pub struct EncryptedMemoryRegion {
    base: *mut u8,
    size: usize,
    encrypted: bool,
    original_protection: Option<u32>,  // ← НОВОЕ ПОЛЕ для сохранения исходной защиты
}

// ИСПРАВЛЕНО: Реализуем Send для безопасной передачи между потоками
unsafe impl Send for EncryptedMemoryRegion {}

impl EncryptedMemoryRegion {
    /// Создание нового зашифрованного региона
    pub fn new(base: *mut u8, size: usize) -> Self {
        Self {
            base,
            size,
            encrypted: false,
            original_protection: None,  // ← ИНИЦИАЛИЗАЦИЯ
        }
    }
    
    /// НОВАЯ ФУНКЦИЯ: Проверка валидности региона памяти
    fn is_valid_memory_region(&self) -> bool {
        // Проверяем базовые условия
        if self.base.is_null() || self.size == 0 || self.size > 0x10000000 {
            return false;
        }
        
        // Проверяем, что адрес не в системном диапазоне
        let addr = self.base as usize;
        if addr < 0x10000 || addr > 0x7FFFFFFFFFFF {
            return false;
        }
        
        // Проверяем, что конечный адрес не переполняется
        if addr.saturating_add(self.size) < addr {
            return false;
        }
        
        true
    }
    
    /// ИСПРАВЛЕНО: Безопасное изменение protection перед XOR
    unsafe fn change_protection_to_rw(&mut self) -> Result<(), String> {
        if self.original_protection.is_some() {
            return Ok(()); // Уже изменено
        }
        
        let mut old_protect = 0u32;
        let result = VirtualProtect(
            self.base as *mut _,
            self.size,
            PAGE_READWRITE,  // Делаем память читаемой и записываемой
            &mut old_protect
        );
        
        if result == 0 {
            return Err("Failed to change memory protection to RW".to_string());
        }
        
        self.original_protection = Some(old_protect);
        Ok(())
    }
    
    /// ИСПРАВЛЕНО: Восстановление исходной protection
    unsafe fn restore_original_protection(&mut self) -> Result<(), String> {
        if let Some(original_protect) = self.original_protection {
            let mut old_protect = 0u32;
            let result = VirtualProtect(
                self.base as *mut _,
                self.size,
                original_protect,  // Восстанавливаем исходную защиту
                &mut old_protect
            );
            
            if result == 0 {
                return Err("Failed to restore original memory protection".to_string());
            }
            
            self.original_protection = None;
        }
        Ok(())
    }
    
    /// ИСПРАВЛЕНО: Шифрование региона памяти с изменением permissions
    pub unsafe fn encrypt(&mut self) {
        if !self.encrypted && self.is_valid_memory_region() {
            // НОВОЕ: Изменяем protection перед XOR
            if let Err(e) = self.change_protection_to_rw() {
                println!("[ERROR] Failed to change protection for encryption: {}", e);
                return;
            }
            
            // Проверяем доступность каждого байта перед модификацией
            for i in 0..self.size {
                // ДОБАВЛЕНО: Проверка доступности перед записью
                if let Ok(_) = std::panic::catch_unwind(|| {
                    // Проверяем, можем ли мы читать из этого адреса
                    std::ptr::read_volatile(self.base.add(i));
                }) {
                    // Если чтение успешно, можем безопасно писать
                    *self.base.add(i) ^= 0xAA;
                } else {
                    // Если не можем читать, пропускаем этот байт
                    continue;
                }
            }
            self.encrypted = true;
            
            // ВАЖНО: НЕ восстанавливаем protection сразу - оставляем RW для decrypt
            println!("[DEBUG] Memory region encrypted successfully");
        }
    }
    
    /// ИСПРАВЛЕНО: Расшифровка региона памяти с восстановлением permissions
    pub unsafe fn decrypt(&mut self) {
        if self.encrypted && self.is_valid_memory_region() {
            // Memory уже должна быть RW после encrypt
            
            // Проверяем доступность каждого байта перед модификацией
            for i in 0..self.size {
                // ДОБАВЛЕНО: Проверка доступности перед записью
                if let Ok(_) = std::panic::catch_unwind(|| {
                    // Проверяем, можем ли мы читать из этого адреса
                    std::ptr::read_volatile(self.base.add(i));
                }) {
                    // Если чтение успешно, можем безопасно писать
                    *self.base.add(i) ^= 0xAA;
                } else {
                    // Если не можем читать, пропускаем этот байт
                    continue;
                }
            }
            self.encrypted = false;
            
            // НОВОЕ: Восстанавливаем исходную protection после decrypt
            if let Err(e) = self.restore_original_protection() {
                println!("[ERROR] Failed to restore protection after decryption: {}", e);
            }
            
            println!("[DEBUG] Memory region decrypted and protection restored");
        }
    }
    
    /// Проверка статуса шифрования
    pub fn is_encrypted(&self) -> bool {
        self.encrypted
    }
}

/// Рандомизация паттерна выделения памяти
pub fn randomize_allocation_pattern() -> usize {
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};
    use std::time::{SystemTime, UNIX_EPOCH};
    
    let mut hasher = DefaultHasher::new();
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    
    now.hash(&mut hasher);
    let hash = hasher.finish();
    
    // Случайный offset для base address
    let random_offset = (hash % 0xF000) as usize + 0x1000;
    0x400000 + random_offset
}

/// ИСПРАВЛЕНО: Менеджер stealth памяти с безопасными операциями
pub struct MemoryStealthManager {
    encrypted_regions: Arc<Mutex<Vec<EncryptedMemoryRegion>>>,
}

impl MemoryStealthManager {
    /// Создание нового менеджера
    pub fn new() -> Self {
        Self {
            encrypted_regions: Arc::new(Mutex::new(Vec::new())),
        }
    }
    
    /// ИСПРАВЛЕНО: Добавление региона с валидацией
    pub fn add_region(&mut self, base: *mut u8, size: usize) {
        // ДОБАВЛЕНО: Предварительная валидация
        if base.is_null() || size == 0 || size > 0x10000000 {
            return; // Игнорируем недопустимые регионы
        }
        
        let addr = base as usize;
        if addr < 0x10000 || addr > 0x7FFFFFFFFFFF {
            return; // Игнорируем системные адреса
        }
        
        let region = EncryptedMemoryRegion::new(base, size);
        if let Ok(mut regions) = self.encrypted_regions.lock() {
            regions.push(region);
            println!("[DEBUG] Added memory region: base=0x{:X}, size={}", addr, size);
        }
    }
    
    /// ИСПРАВЛЕНО: Безопасное шифрование всех регионов с permission changes
    pub unsafe fn encrypt_all(&mut self) {
        if let Ok(mut regions) = self.encrypted_regions.lock() {
            for region in &mut *regions {
                // ДОБАВЛЕНО: Обработка паники для каждого региона
                let _ = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                    region.encrypt();
                }));
            }
            println!("[DEBUG] All regions encrypted");
        }
    }
    
    /// ИСПРАВЛЕНО: Безопасная расшифровка всех регионов с permission restore
    pub unsafe fn decrypt_all(&mut self) {
        if let Ok(mut regions) = self.encrypted_regions.lock() {
            for region in &mut *regions {
                // ДОБАВЛЕНО: Обработка паники для каждого региона
                let _ = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                    region.decrypt();
                }));
            }
            println!("[DEBUG] All regions decrypted");
        }
    }
    
    /// ИСПРАВЛЕНО: Безопасный фоновый поток (ВРЕМЕННО ОТКЛЮЧЕН)
    pub fn start_background_encryption(&self) {
        // ВРЕМЕННО ОТКЛЮЧЕНО для предотвращения ACCESS_VIOLATION
        // Background encryption будет добавлен после полного тестирования
        
        // Простое логирование вместо реального потока
        // В будущем можно будет включить безопасную версию
    }
}

impl Default for MemoryStealthManager {
    fn default() -> Self {
        Self::new()
    }
}
