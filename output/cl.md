python tests/test_obfuscator.py

===================================

`sample
cl c:\TEMP\CppObfuscator\sample\test_gui.cpp /link user32.lib kernel32.lib /Fe:c:\TEMP\CppObfuscator\sample\test_gui_sample.exe
===================================
											**** sample EXE 

` чистая сборка
cl c:\TEMP\CppObfuscator\sample\test_exe.cpp /link user32.lib kernel32.lib /Fe:c:\TEMP\CppObfuscator\output\test_exe.exe

`.CPP to OBF .CPP
python main.py --obfuscate --input c:\TEMP\CppObfuscator\sample\test_exe.cpp --output c:\TEMP\CppObfuscator\output\test_obf.cpp 

`OBF to EXE
cl c:\TEMP\CppObfuscator\output\test_obf.cpp /link user32.lib kernel32.lib /Fe:c:\TEMP\CppObfuscator\output\test_obf_exe.exe


===================================

` собрать dll с c:\TEMP\CppObfuscator\sample\test_dll.cpp

cl /LD c:\TEMP\CppObfuscator\sample\test_dll.cpp /link /OUT:c:\TEMP\CppObfuscator\output\test_dll.dll user32.lib

`Зашифруй новую DLL:
python utils/encrypt_dll.py


===================================


