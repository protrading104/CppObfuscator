import subprocess
import os

def build_cpp_exe(source_cpp, output_exe):
    cmd = [
        "cl",
        "/nologo",
        "/O2",
        "/MT",
        "/LD",  # создаёт DLL; убери если нужен EXE
        source_cpp,
        "advapi32.lib",
        "user32.lib",
        "/link",
        f"/OUT:{output_exe}"
    ]

    print("[*] Compiling...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print("[!] Compilation failed")
        print(result.stdout)
        print(result.stderr)
    else:
        print(f"[+] Compilation succeeded → {output_exe}")
