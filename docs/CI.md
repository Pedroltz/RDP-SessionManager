# Continuous integration

The repository has GitHub Actions workflows for quality checks, website validation/deployment
and installer release publishing.

## Website validation and deployment

`Deploy Website to GitHub Pages` runs for pull requests targeting `master` and
pushes to `master` that change `website/**` or its workflow. It can also be
started manually from Actions.

Every run installs dependencies with `npm ci`, using the Node version in
`website/.nvmrc`, and runs:

```bash
cd website
npm run build
npm run verify
```

These gates check Astro/TypeScript, PT-BR and EN pages, language links, metadata,
sitemap URLs, duplicate IDs, anchors and local assets under the case-sensitive
`/RDP-SessionManager/` base. See the [website guide](../website/README.md) for
local preview and visual checks.

Pull requests never publish. Pushes and manual runs on `master` upload the
validated `website/dist` artifact, configure Pages, then deploy it to the
`github-pages` environment. Runs on other branches only validate. Only the
deploy job receives `pages: write` and `id-token: write`; other jobs have
read-only repository access. Production runs are serialized without cancelling
an ongoing deployment.

The final job checks both published languages, a referenced stylesheet, script
and application image. It requires HTTP 200, appropriate content types and the
expected commit revision in the HTML. It retries up to six times, five seconds
apart, to allow Pages propagation. A failed check leaves the run red and logs
the failing URL; it does not automatically roll back the deployment.

The public address is:
https://pedroltz.github.io/RDP-SessionManager/

The old lowercase `/rdp-session-manager/` path returns 404; repository redirects
do not provide a Pages redirect for that path. Use the official URL above.

### GitHub configuration and manual publication

In repository **Settings → Pages**, select **GitHub Actions** as the source.
This was already configured when the website recovery was investigated. Ensure
the `github-pages` environment allows deployments from `master`.

To publish manually, open **Actions → Deploy Website to GitHub Pages → Run
workflow**, select `master`, and run it. A failed build or static verification
prevents publication. Add `Build Astro Website` as a required status check if
branch protection is configured; path filters mean this check only exists on
pull requests touching the website or workflow, so do not require it globally
without adjusting the trigger to run on all pull requests.

### Recovery

If publication fails, inspect the failing job and correct its configuration or
build errors. To recover from a content regression, revert the responsible
commit on `master`; the resulting website change triggers a fresh deploy. If
needed, run the workflow manually on the reverted `master`. Check the published
verification job before considering recovery complete.

## Publish Release

`Publish Release` runs for tags matching `v*.*.*`. It verifies the tag against
`src/rdp_session_manager/version.py`, compiles Python sources, checks shell syntax, runs the
unittest suite and installer bootstrap tests, then builds checksummed installer
assets and publishes the release.

This workflow is independent of website deployment. Privileged RDP E2E checks run locally.

## Quality checks and local RDP validation

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
