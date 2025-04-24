import xml.etree.ElementTree as ET

class VcxprojParser:
    def __init__(self, vcxproj_path):
        self.vcxproj_path = vcxproj_path

    def extract_source_files(self):
        tree = ET.parse(self.vcxproj_path)
        root = tree.getroot()
        namespace = {'ns': 'http://schemas.microsoft.com/developer/msbuild/2003'}

        source_files = []
        for item_group in root.findall('ns:ItemGroup', namespace):
            for cl in item_group.findall('ns:ClCompile', namespace):
                if 'Include' in cl.attrib:
                    source_files.append(cl.attrib['Include'])
            for cl in item_group.findall('ns:ClInclude', namespace):
                if 'Include' in cl.attrib:
                    source_files.append(cl.attrib['Include'])

        return source_files
