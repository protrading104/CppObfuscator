use std::path::Path;

#[path = "src/utils.rs"]
mod utils;

fn main() {
    // Проверяем что файлы существуют на этапе компиляции
    let encrypted_file = "output/encrypted_agent.exe";
    let key_file = "output/agent_aes.key";

    if !Path::new(encrypted_file).exists() {
        panic!("Missing file: {}", encrypted_file);
    }

    if !Path::new(key_file).exists() {
        panic!("Missing file: {}", key_file);
    }

    println!("cargo:rerun-if-changed={}", encrypted_file);
    println!("cargo:rerun-if-changed={}", key_file);

    log!("Build: Embedded files verified");
}

