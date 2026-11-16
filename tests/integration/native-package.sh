#!/usr/bin/env bash
# Run only inside a disposable Debian or Arch environment as root.
set -euo pipefail
FAMILY="${1:?usage: native-package.sh debian|arch}"
case "$FAMILY" in
    debian)
        apt-get update
        DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
            ruby ruby-dev build-essential zstd python3 python3-gi python3-gi-cairo \
            python3-psutil gir1.2-gtk-4.0 gir1.2-adw-1 polkitd ca-certificates
        ;;
    arch)
        pacman -Syu --noconfirm --needed ruby base-devel zstd python python-gobject \
            python-cairo python-psutil gtk4 libadwaita polkit ca-certificates
        ;;
    *) exit 2 ;;
esac
gem install --no-document --bindir /usr/local/bin fpm erb
export PATH="/usr/local/bin:$PATH"
mkdir -p /work /out
cp -a /source/src /source/helpers /source/data /source/imgs /source/installer /work/
cd /work
RDPSM_PACKAGE_TARGET="$FAMILY" RDPSM_RELEASE_DIR=/out bash installer/build_packages.sh
case "$FAMILY" in
    debian) apt-get install -y /out/rdp-session-manager.deb ;;
    arch) pacman -U --noconfirm /out/rdp-session-manager.pkg.tar.zst ;;
esac
# Run from outside the checkout; assert installed implementation and resources.
cd /
rdpsm --version
rdpsm --help >/dev/null
python3 - <<'PY'
import sys
sys.path.insert(0, '/usr/share/rdp-session-manager/src')
from rdp_session_manager.infrastructure.paths import helper_dir, ui_file
from rdp_session_manager.infrastructure.windows_app import RecipeCatalog
assert helper_dir().joinpath('audit-exec.py').is_file()
assert ui_file('main-window.ui').is_file()
assert RecipeCatalog().list()
from rdp_session_manager.presentation.gtk.main_window import MainWindow
print('Native installation imports, CLI, GTK template, helpers, recipes: OK')
PY
