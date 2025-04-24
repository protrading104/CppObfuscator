import logging
import ctypes
from obfuscator.memory_protect import MemoryProtector

print("⚠️  Тест запускается!")

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

logger.info("📝 Логирование активировано")


def test_heavens_gate():
    protector = MemoryProtector()

    # ✅ Создаём буфер (48 байт)
    buffer_size = 48
    buffer = ctypes.create_string_buffer(buffer_size)

    # ✅ Используем c_ulong (32-bit), как в memory_protect.py
    return_length = ctypes.c_ulong(0)

    # ✅ Создаём указатель корректно через ctypes.POINTER
    return_length_ptr = ctypes.pointer(return_length)  # <-- исправлено

    # Дополнительное логирование
    logging.info("🔍 Проверяем переданные параметры перед вызовом...")
    logging.info(f"📝 buffer: {hex(ctypes.addressof(buffer))}")  
    logging.info(f"📝 buffer_size: {buffer_size}")
    logging.info(f"📝 return_length: {hex(ctypes.addressof(return_length))}")
    logging.info(f"🛠 Тип return_length: {type(return_length)}")
    logging.info(f"🛠 Тип return_length_ptr: {type(return_length_ptr)}")

    print("🔍 Тест запускается...")
    logging.info("🔍 Логирование активировано")

    try:
        result = protector.heavens_gate(buffer, buffer_size, return_length_ptr)
        logging.info(f"🔍 Итоговый результат выполнения: {result}")
    except Exception as e:
        logging.error(f"❌ Ошибка выполнения heavens_gate: {e}")

if __name__ == "__main__":
    test_heavens_gate()
