
										#Пайплайн

										✅ STEP 1 — Обфускация исходного C++ кода
Ключ: --obfuscate

Использует code_transformer.obfuscate() и применяет:
		Перезапись API (через resolve)
		Шифрование строк (XOR rolling)
		Полиморфизм (ренейминг, junk code)
		Инъекция shellcode (напр., NtQuerySystemInformation)

🔧 Модифицируется исходный файл → сохраняется как output/test_dll_obf.cpp
🧠 Управляется флагом --type dll|exe, чтобы понять: вставлять junk или нет.


python main.py --obfuscate --input some_file.cpp --output obf.cpp --type exe




										✅ STEP 2 — Компиляция обфусцированного кода
Ключ: --compile-dll

Запускает компилятор cl /LD ..., чтобы собрать DLL из обфусцированного .cpp.

📥 Вход: output/test_dll_obf.cpp
📤 Выход: output/test_dll.dll

python main.py --compile-dll --input output/test_dll_obf.cpp --dll output/test_dll.dll


										✅ STEP 3 — Шифрование собранной DLL
Ключ: --encrypt-dll

Шифрует .dll с помощью AES-128, результат сохраняется в бинарный файл.

📥 Вход: output/test_dll.dll
📤 Выход: output/test_dll_encrypted.bin

🧩 Параметр --key позволяет задать свой 16-байтовый ключ.

										
										✅ STEP 4 — Загрузка зашифрованной DLL в память
Ключ: --load-encrypted

Использует ReflectiveDLLLoader, выполняет:

		Расшифровку
		Ручной маппинг в память (Manual Mapping)
		Исправление релокаций
		IAT-фикс
		Запуск DllMain (Reflective Entry)

📥 Вход: output/test_dll_encrypted.bin
📤 Выполнение DLL без использования LoadLibrary, незаметно для AV/EDR