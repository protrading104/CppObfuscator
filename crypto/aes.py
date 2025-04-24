# -*- coding: utf-8 -*-
from Crypto.Cipher import AES
import base64

class AES128:
    def __init__(self, key: bytes):
        """Инициализация AES-128 (ключ строго 16 байт)"""
        assert len(key) == 16, "Ключ должен быть 16 байт"
        self.key = key

    def encrypt(self, data: bytes) -> bytes:
        """Шифрует данные с использованием AES-128 ECB"""
        cipher = AES.new(self.key, AES.MODE_ECB)
        padded_data = data + b"\x00" * (16 - len(data) % 16)  # Дополняем до блока
        return cipher.encrypt(padded_data)

    def decrypt(self, data: bytes) -> bytes:
        """Дешифрует данные AES-128 ECB"""
        cipher = AES.new(self.key, AES.MODE_ECB)
        return cipher.decrypt(data).rstrip(b"\x00")  # Убираем доп. байты
