from Crypto.Cipher import ARC4

class RC4Cipher:
    def __init__(self, key: bytes):
        """Инициализация RC4 (ключ от 5 до 256 байт)"""
        assert 5 <= len(key) <= 256, "Ключ RC4 должен быть от 5 до 256 байт"
        self.key = key

    def encrypt(self, data: bytes) -> bytes:
        """Шифрует данные RC4"""
        cipher = ARC4.new(self.key)
        return cipher.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        """Дешифрует данные RC4"""
        cipher = ARC4.new(self.key)
        return cipher.decrypt(data)
