#!/usr/bin/env bash
# Build a deterministic PE without a Windows SDK or the C runtime.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT="${1:?usage: build-windows-gui.sh OUTPUT.exe}"
WORK="$(mktemp -d -t rdpsm-fixture.XXXXXX)"
trap 'rm -rf -- "$WORK"' EXIT
printf 'LIBRARY USER32.dll\nEXPORTS\nMessageBoxA\n' > "$WORK/user32.def"
printf 'LIBRARY KERNEL32.dll\nEXPORTS\nExitProcess\n' > "$WORK/kernel32.def"
llvm-dlltool -m i386:x86-64 -d "$WORK/user32.def" -l "$WORK/user32.lib"
llvm-dlltool -m i386:x86-64 -d "$WORK/kernel32.def" -l "$WORK/kernel32.lib"
clang --target=x86_64-pc-windows-msvc -c -fno-stack-protector -o "$WORK/fixture.obj" "$ROOT/windows-gui.c"
lld-link /entry:mainCRTStartup /subsystem:windows /timestamp:0 /nodefaultlib "/out:$OUTPUT" "$WORK/fixture.obj" "$WORK/user32.lib" "$WORK/kernel32.lib"
sha256sum "$OUTPUT"
