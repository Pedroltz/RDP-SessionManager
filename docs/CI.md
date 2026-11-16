# Continuous integration

`Quality Checks` roda em pushes e pull requests e valida compilação, sintaxe
shell, a suíte unittest completa, bootstrap do instalador, wheel e ativação GTK
sob Xvfb. Também constrói e instala os pacotes em contêineres Debian 13 e Arch,
com o mesmo roteiro local `tests/integration/native-package.sh`. Um job separado
executa `npm ci`, build Astro e a verificação estática do site.

`Deploy Website to GitHub Pages` continua responsável pela publicação do site.
`Publish Release` continua limitado a tags, verifica a versão canônica em
`src/rdp_session_manager/version.py` e inclui `python3-rich` nas dependências dos
gates. Esta rodada não cria tags nem publica releases.

Os testes privilegiados RDP são locais: esta árvore não contém um workflow
agendado para eles. Execute os roteiros descritos em [tests/README.md](../tests/README.md)
sequencialmente em um host com xrdp, sessões X11 e ferramentas de captura.
A fixture Windows é compilável a partir do C incluído no repositório. A carga
verifica memória antes de cada criação e durante a espera, para a partir de
85%, e verifica contas/processos após a limpeza.

Os artefatos de pacote do CI ficam disponíveis por sete dias. A aprovação de
branch protection e a execução em outras distribuições/versões não são
configuradas automaticamente.
