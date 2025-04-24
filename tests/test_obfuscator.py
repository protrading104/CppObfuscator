import unittest
import os
import sys
import logging
logging.basicConfig(level=logging.DEBUG)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from obfuscator.code_transformer import CodeTransformer

class TestCodeTransformer(unittest.TestCase):
    def test_transform_cpp_file(self):
        input_path = "sample/test_gui.cpp"
        output_path = "output/test_gui.cpp"

        os.makedirs("output", exist_ok=True)

        # ⬅️ Передаём конфиг с указанием, что это C++
        config = {"language": "cpp"}
        transformer = CodeTransformer(config=config)
        transformer.run(input_path, output_path)

        self.assertTrue(os.path.exists(output_path), "❌ Обфусцированный файл не создан")

        print("✅ Обфускация завершена. Результат:", output_path)

if __name__ == "__main__":
    unittest.main()
