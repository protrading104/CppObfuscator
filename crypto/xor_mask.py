class RollingXOR:
    def __init__(self, key: bytes):
        """Инициализация Rolling XOR"""
        assert len(key) > 0, "Ключ XOR не может быть пустым"
        self.key = key

    def encrypt(self, data: bytes) -> bytes:
        """Шифрует данные Rolling XOR"""
        return bytes(data[i] ^ self.key[i % len(self.key)] for i in range(len(data)))

    def decrypt(self, data: bytes) -> bytes:
        """Дешифрует данные Rolling XOR (идентично шифрованию)"""
        return self.encrypt(data)
