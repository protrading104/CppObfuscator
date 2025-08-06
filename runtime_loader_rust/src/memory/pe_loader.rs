use pelite::pe64::{Pe, PeFile};

pub struct PELoader<'a> {
    pe_data: &'a [u8],
    pe_file: PeFile<'a>,
    #[allow(dead_code)]  // Подавляем warning для неиспользуемого поля
    base_address: usize,
    entry_point: usize,
}

impl<'a> PELoader<'a> {
    pub fn new(pe_data: &'a [u8]) -> Result<Self, String> {
        let pe_file = PeFile::from_bytes(pe_data)
            .map_err(|e| format!("Failed to parse PE: {:?}", e))?;
        
        let nt_headers = pe_file.nt_headers();
        let base_address = nt_headers.OptionalHeader.ImageBase as usize;
        let entry_point = nt_headers.OptionalHeader.AddressOfEntryPoint as usize;
        
        Ok(PELoader {
            pe_data,
            pe_file,
            base_address,
            entry_point,
        })
    }
    
    pub fn get_image_size(&self) -> usize {
        self.pe_file.nt_headers().OptionalHeader.SizeOfImage as usize
    }
    
    // Добавляем публичные геттеры для приватных полей
    pub fn get_pe_data(&self) -> &[u8] {
        self.pe_data
    }
    
    pub fn get_entry_point(&self) -> usize {
        self.entry_point
    }
    
    pub fn get_sections(&self) -> Result<Vec<SectionInfo>, String> {
        let sections = self.pe_file.section_headers();
        let mut section_infos = Vec::new();
        
        for section in sections {
            section_infos.push(SectionInfo {
                name: String::from_utf8_lossy(&section.Name).trim_end_matches('\0').to_string(),
                virtual_address: section.VirtualAddress as usize,
                virtual_size: section.VirtualSize as usize,
                raw_address: section.PointerToRawData as usize,
                raw_size: section.SizeOfRawData as usize,
                characteristics: section.Characteristics,
            });
        }
        
        Ok(section_infos)
    }

    #[allow(dead_code)]  // Подавляем warning для неиспользуемого метода
    pub fn pe_file(&self) -> &PeFile<'a> {
        &self.pe_file
    }
}

#[derive(Debug)]
pub struct SectionInfo {
    pub name: String,
    pub virtual_address: usize,
    pub virtual_size: usize,
    pub raw_address: usize,
    pub raw_size: usize,
    pub characteristics: u32,
}
