# -*- coding: utf-8 -*-
import sys
import os
import unittest
import ctypes

# 🔧 Добавляем путь к корню проекта (один уровень вверх)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from obfuscator.syscall_hiding import SyscallHider

class TestSyscallMechanisms(unittest.TestCase):
    def setUp(self):
        self.hider = SyscallHider()

    def test_unhook_ntdll(self):
        """Проверка: удаление хуков из ntdll.dll"""
        try:
            self.hider.unhook_ntdll()
        except Exception as e:
            self.fail(f"API Unhooking провалился: {e}")

    def test_syscall_index_resolution(self):
        """Проверка получения индекса syscall"""
        idx = self.hider.get_syscall_index("NtQuerySystemInformation")
        self.assertIsInstance(idx, int)
        self.assertGreater(idx, 0)

    def test_indirect_syscall_executes(self):
        """Тест выполнения Indirect Syscall"""
        syscall_id = self.hider.get_syscall_index("NtQuerySystemInformation")
        buffer_size = 1024
        buffer = ctypes.create_string_buffer(buffer_size)
        return_length = ctypes.c_ulong(0)

        try:
            result = self.hider.indirect_syscall(
                syscall_id,
                ctypes.addressof(buffer),
                buffer_size,
                ctypes.addressof(return_length)
            )
            self.assertIsInstance(result, int)
        except Exception as e:
            self.fail(f"Indirect syscall execution failed: {e}")

if __name__ == "__main__":
    unittest.main()
