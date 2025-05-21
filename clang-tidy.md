

cd c:\TEMP\FindProcessesWithNamedPipes_OBF\FindProcessesWithNamedPipes\
clang-tidy FindProcessesWithNamedPipes.cpp -- -std=c++17


c:\TEMP\FindProcessesWithNamedPipes_OBF\FindProcessesWithNamedPipes\FindProcessesWithNamedPipes.cpp

========================================

Для корректной работы кода в текущей среде необходимо:
Воссоздать структуру подмодуля stringguard как пакет (stringguard/ с __init__.py).
Разложить все загруженные файлы туда.


протестируй шифрование строк на файле - FindProcessesWithNamedPipes.cpp
если нужны еще файлы из проекта скажи чего не хватает и я предоставлю

структура подмодуля stringguard

c:\TEMP\CppObfuscator\stringguard>tree /f
Folder PATH listing
Volume serial number is D256-35F7
C:.
│   backup_restore.py
│   decryptor_generator.py
│   filter_engine.py
│   injector.py
│   solution_manager.py
│   string_encoder.py
│   string_parser.py
│   validator.py
│   vcxproj_parser.py
│   __init__.py
│   __main__.py
│
└───__pycache__

првоерь файл исходник. олжен лежать по этмоу пути  '/mnt/data/FindProcessesWithNamedPipes.cpp'
что бы в нем не было обфусцированных строк 

но ты внес изменения в /mnt/data/injector_corrected.py

теперь переименуй /mnt/data/injector_corrected.py  в оригинал /mnt/data/injector.py

выполни коррекцию логики вставки массивов и вызовов в injector.py

исправь логику генерации ошибочных  строк в injector.py


===============================================================

последняя ошибка

в сгенерированном коде появляются конструкции вроде wprintf(L""%s", decrypt(...)), где ""%s" интерпретируется как неправильная строка из-за лишней кавычки.
Это происходит потому, что:
В исходной строке, которую мы заменяем, есть L"...".
Обфускатор не удаляет внешние кавычки L"..." должным образом.
В итоге вставляется ещё один набор кавычек вокруг %s, и компилятор видит L""%s".



`В injector.py удалить лишние кавычки из оригинала, если они присутствуют, перед созданием replacement_code.