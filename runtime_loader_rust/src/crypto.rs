// src/crypto.rs
/// Получение встроенного AES ключа (оптимальный подход)
pub fn get_decryption_key() -> [u8; 16] {
    use crate::data::AES_KEY;
    
    // Используем ключ, сгенерированный exe_encryptor.py
    // Этот ключ уже случайный и уникальный для каждой сборки
    AES_KEY
}