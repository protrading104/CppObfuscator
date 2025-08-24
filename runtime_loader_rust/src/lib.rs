// src/lib.rs

// Основные модули
pub mod constants;
pub mod crypto;
pub mod data;
pub mod syscall;
pub mod utils;

// EDR bypass модули
pub mod edr {
    pub mod amsi;
    pub mod anti_debug;
    pub mod etw;
    pub mod stealth;
    pub mod unhook;
}

// Memory management модули
pub mod memory {
    pub mod manual_map;
    pub mod pe_loader;
}

// Re-export для прямого доступа из main.rs
pub use data::*;
pub use utils::*;

// EDR функции
pub use edr::amsi::patch_amsi;
pub use edr::anti_debug::comprehensive_debug_check;
pub use edr::etw::patch_etw;
pub use edr::unhook::unhook_ntdll;

// Memory типы
pub use memory::manual_map::ManualMapper;
pub use memory::pe_loader::PELoader;
