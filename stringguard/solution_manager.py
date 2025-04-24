import os
import xml.etree.ElementTree as ET

class SolutionManager:
    def __init__(self, sln_path):
        self.sln_path = sln_path

    def extract_vcxproj_paths(self):
        projects = []
        with open(self.sln_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.strip().startswith('Project(') and '.vcxproj' in line:
                    parts = line.split('", "')
                    if len(parts) > 1:
                        relative_path = parts[1].strip('"')
                        full_path = os.path.normpath(os.path.join(os.path.dirname(self.sln_path), relative_path))
                        projects.append(full_path)
        return projects
