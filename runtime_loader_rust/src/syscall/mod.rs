pub mod ntdll;
pub mod indirect_syscall;

// Экспортируем основные типы и функции
pub use ntdll::SyscallNumbers;
pub use indirect_syscall::{nt_allocate_virtual_memory, nt_protect_virtual_memory};
