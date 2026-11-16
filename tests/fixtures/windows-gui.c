/* Deterministic GUI fixture; no CRT, network, filesystem writes, or timing. */
__declspec(dllimport) int __stdcall MessageBoxA(void *, const char *, const char *, unsigned);
__declspec(dllimport) void __stdcall ExitProcess(unsigned);
void mainCRTStartup(void) {
    MessageBoxA(0, "RDPSM Windows application acceptance fixture", "RDPSM deterministic fixture", 0);
    ExitProcess(0);
}
