# Testes

Instale as dependências Python de desenvolvimento em um ambiente com acesso ao
PyGObject do sistema:

```bash
python3 -m venv --system-site-packages venv
venv/bin/pip install -r requirements-dev.txt
venv/bin/python -m unittest discover -s tests -v
bash tests/test_installer_bootstrap.sh
```

`tests/run_tests.sh` executa a mesma descoberta com `python3` disponível no PATH.
A suíte cobre domínio, usuários, sessões, persistência, privilégios, reparo e
rollback, installer, auditoria, runtimes e lógica GTK. Os testes preexistentes
na raiz continuam suportados. Novas regressões são organizadas em:

| Diretório | Escopo |
| --- | --- |
| `unit` | Snapshot, serialização, cache, invalidação e coordenação de tarefas |
| `integration` | Concorrência de arquivos/processos, falha de gravação e pacotes nativos |
| `architecture` | Regras de dependência, ausência de módulos antigos e CLI sem GTK |
| `fixtures` | Scheduler determinístico e fonte da aplicação Windows |
| `e2e` | Ativação GTK e sessões RDP reais |
| `performance` | Medições somente leitura do host |

O teste multiprocessos precisa de suporte a processos e sockets Unix; um sandbox
que bloqueia essa capacidade exige execução fora dele. Nenhum teste foi
desativado para contornar a restrição.

Para validar GTK no checkout:

```bash
xvfb-run -a env GDK_BACKEND=x11 GSETTINGS_BACKEND=memory python3 tests/e2e/gtk_smoke.py
```

Para validar pacotes nativos em ambientes descartáveis:

```bash
mkdir -p artifacts/packages
sudo docker run --rm -v "$PWD:/source:ro" -v "$PWD/artifacts/packages:/out" debian:13 bash /source/tests/integration/native-package.sh debian
sudo docker run --rm -v "$PWD:/source:ro" -v "$PWD/artifacts/packages:/out" archlinux:base bash /source/tests/integration/native-package.sh arch
```

Para testes RDP reais, instale Xvfb, FreeRDP, ImageMagick, `xdpyinfo`, `xprop`,
`xdotool`, Openbox e os desktops/aplicativos selecionados. Rode sequencialmente:

```bash
sudo bash tests/e2e/test_all_desktops.sh xfce gnome kde
sudo bash tests/e2e/test_remoteapps.sh
sudo bash tests/e2e/test_audit_trail.sh
bash tests/fixtures/build-windows-gui.sh /tmp/windows-test.exe
sudo env RDPSM_WINDOWS_FIXTURE=/tmp/windows-test.exe RDPSM_WINDOWS_RUNNER=winege-legacy bash tests/e2e/test_windows_apps.sh
sudo bash tests/e2e/test_server_load.sh
```

A fixture exige Clang, `llvm-dlltool` e `lld-link` e não usa SDK Windows. O linker
fixa o timestamp PE em zero; duas compilações devem produzir bytes idênticos.
O teste Windows usa um único perfil para não depender de escolhas em um diálogo.
Snap e Flatpak precisam dos aplicativos instalados; ausência não comprova suporte.
Os desktops explicitamente passados são os únicos testados.

A carga usa estágios 5/10/25, interrompe diante de falha ou memória a partir de
85% e limpa contas/processos temporários. Execute em host dedicado ou em uma
janela compatível com a carga. Resultados, exclusões e limitações desta rodada
estão em [REFACTOR_REPORT.md](../docs/REFACTOR_REPORT.md).

Para repetir medições sem criar usuários nem alterar serviços:

```bash
python3 tests/performance/measure.py
```
