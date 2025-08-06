import pefile

class Disassembler:
    def __init__(self, dll_path):
        self.pe = pefile.PE(dll_path)

    def get_section_data(self, section_name):
        for section in self.pe.sections:
            if section_name.encode() in section.Name:
                return section.get_data()
        return None

    def list_imports(self):
        imports = []
        if hasattr(self.pe, 'DIRECTORY_ENTRY_IMPORT'):
            for entry in self.pe.DIRECTORY_ENTRY_IMPORT:
                for imp in entry.imports:
                    if imp.name:
                        imports.append((entry.dll.decode(), imp.name.decode()))
        return imports

    def extract_strings(self, min_length=4):
        all_strings = []
        for section in self.pe.sections:
            data = section.get_data()
            str_buff = b""
            for byte in data:
                if 32 <= byte < 127:
                    str_buff += bytes([byte])
                else:
                    if len(str_buff) >= min_length:
                        all_strings.append(str_buff.decode(errors='ignore'))
                    str_buff = b""
            if len(str_buff) >= min_length:
                all_strings.append(str_buff.decode(errors='ignore'))
        return all_strings