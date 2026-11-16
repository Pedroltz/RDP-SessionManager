# Reorganização e validação — 26/10/2026

## Diagnóstico e alterações

1. **Fluidez GTK:** carregamento e refresh consultavam contas, processos e serviços
   na thread gráfica. O painel agora recebe um snapshot em segundo plano, sem
   consultas sobrepostas, com atualização apenas das linhas alteradas. Operações
   de exclusão, listagem de executáveis e lançamento FreeRDP também foram
   retiradas dessa thread. Callbacks pertencem ao ciclo de vida das janelas.
2. **CPU:** a consulta de estatísticas bloqueava por um segundo; agora usa a
   amostra não bloqueante do psutil. A primeira leitura pode ser zero.
3. **Persistência:** configuração e estados eram truncados no destino. Agora
   usam substituição atômica, sincronização e permissão 0600. Alterações de
   estados são mescladas sob lock entre processos. O staging de perfis é sempre
   limpo, inclusive após timeout; o helper valida e substitui o JSON completo.
4. **Arquitetura e distribuição:** modelos e regras estão no domínio; casos de
   uso, snapshot e coordenação na aplicação; operações Linux na infraestrutura.
   A composição é compartilhada por GTK e CLI; os aliases antigos foram removidos a pedido do usuário.
   Wheel e instaladores incluem recursos e resolvem caminhos sem depender do cwd.
5. **Falhas encontradas por aceitação real:** a criação não emitia evento de
   sucesso porque o trap de rollback substituía o trap de auditoria. A finalização
   agora registra o resultado. A conversão para Windows conservava argv/runtime
   Linux; o vínculo ao launcher gerenciado agora é explícito. O checkout privado
   do administrador não é acessível à conta RDP: launcher e módulos necessários
   são instalados em `/opt/rdp-users`, pertencentes ao root. A substituição
   atômica de manifestos e estados Windows preserva o proprietário, evitando que
   uma atualização administrativa torne o arquivo privado ilegível à sessão.

A arquitetura e os limites da migração estão em [ARCHITECTURE.md](ARCHITECTURE.md).

## Inventário das remoções

| Remoção | Evidência e substituição |
| --- | --- |
| `_ensure_rdp_group_exists`, `_create_base_directory` em UserManager | Nenhum consumidor; o helper de provisionamento já agrupa as operações com uma autenticação e rollback |
| `_is_user_enabled`, `_detect_desktop_env` | Nenhum consumidor executável; consulta atual de estado e detecção completa de sessão já substituíam essas funções |
| `_is_rdp_user` e atributo `users.conf` | Após usar o grupo uma vez por listagem, não restou consumidor; o arquivo não era lido ou escrito |
| Dispatchers inline em `create-rdp-user.sh` e `update-rdp-user-profiles.sh` | Eram sempre sobrescritos pelo wrapper versionado antes de o helper terminar |
| Construção de comando de teclado do dispatcher removido | O wrapper compartilhado lê a configuração durante a sessão; variáveis e comando anteriores não tinham consumidores |
| Carregamento de textura no About | A variável nunca era aplicada ao diálogo; o ícone da aplicação continua configurado |
| Seis fragmentos Meson | Não existia `meson.build` raiz; o fragmento src referenciava um subdiretório sem definição. Setuptools e empacotamento nativo são os caminhos executáveis |
| Imports sem referência e sugestões comentadas de dependências | Revisão AST como apoio; reexports públicos e imports usados por patches de compatibilidade foram preservados |
| Runner de testes com parsing manual de saída | Substituído pela descoberta unittest que preserva corretamente o código de saída e inclui os novos diretórios |

Não foram removidos recursos usados por templates, helpers, receitas, políticas,
launchers ou pacotes. `change-session-type.sh` conserva o dispatcher de fallback
para contas antigas sem JSON. A API legada `get_connection_history` continua
retornando lista vazia, agora documentada como tal. Os imports antigos foram substituídos nos consumidores e seus arquivos removidos. Documentação histórica arquivada foi preservada.
A supressão de tipo no decoder privado de certificados foi substituída por
checagem explícita de disponibilidade. Nenhum teste foi desativado.

## Medições

Três repetições por operação, medianas, no mesmo host com três contas gerenciadas.
Os probes são somente leitura; não criam sessões. A CPU é tempo do coletor, sem
incluir CPU dos subprocessos. RSS é o pico do processo coletor, não do GTK nem do
servidor. A variação de carga do host limita conclusões sobre diferenças pequenas.

| Operação | Antes (ms) | Depois (ms) | Subprocessos antes/depois |
| --- | ---: | ---: | ---: |
| CLI `--help` | 150,631 | 135,787 | 1 / 1 |
| Carregar usuários | 24,238 | 13,976 | 6 / 6 |
| Atualizar sessões | 3,645 | 3,000 | 1 / 1 |
| Estatísticas do sistema | 1.004,435 | 2,836 | 1 / 1 |
| RSS máximo do coletor (KiB) | 34.240 | 31.828 | — |

A redução de aproximadamente um segundo na consulta de estatísticas decorre da
remoção da espera explícita. A redução de consultas no GTK vem do snapshot por
ciclo e de não consultar sessões por linha; o probe isolado de contas mantém os
subprocessos existentes de estado/grupos. A enumeração de processos é única por
refresh e protegida contra leituras concorrentes. O smoke GTK após a mudança
carregou interface, saúde e três usuários em aproximadamente 2,7 segundos; não
houve medição GTK anterior comparável. Execute `tests/performance/measure.py`
para repetir os probes. Os resultados brutos estão em
[before.json](performance/before.json) e [after.json](performance/after.json).

## Verificação

O baseline executou 221 testes com um erro de importação por falta de rich.
Com a dependência disponível, os 250 testes existentes passaram. Os novos testes
cobrem dependências entre camadas, CLI sem GTK, concorrência, cancelamento,
invalidação, persistência, falhas de gravação, permissões e perfis Windows.
A suíte completa terminou com **269 testes aprovados**, com rich instalado no
Python do sistema. Compilação Python, sintaxe shell, parsing de recursos XML/JSON,
bootstrap do instalador e `git diff --check` passaram. O wheel e o sdist foram
construídos; o wheel foi instalado em um ambiente separado e executado fora do
checkout, verificando CLI, UI, ícone, receitas e helpers. GTK foi validado sob Xvfb.

Na bateria real passaram XFCE, GNOME, RemoteApp Linux com xfce4-terminal, auditoria
e a aplicação Windows determinística via Wine. O estado final Windows confirmou
`ready` com `validation.rdp=true`. Duas compilações da fixture produziram o SHA-256
`2ed415d1a025deec35119f776cede60e0500dc0dd8e2a32e4e1f201d26691160`.
A bateria terminou sem novas contas no host. Debian 13 passou no build e na
instalação nativa; Arch também passou no build e na instalação, com CLI, imports
GTK, templates, receitas e helpers verificados fora do checkout. Os contêineres
foram removidos após a validação. A preparação Arch exigiu definir o diretório
de executáveis dos gems e instalar `erb`, agora incluídos no roteiro de CI.

O smoke GTK do checkout final levou aproximadamente 2,1 segundos; o wheel
instalado, em execução posterior com caches quentes, ficou pronto em 517 ms.
Essas ativações não constituem comparação antes/depois. O teste usa Xvfb com
renderização por software. A verificação final do host confirmou xrdp e
xrdp-sesman ativos, sem contas nem processos dos UIDs temporários utilizados.

## Limites de aceitação

O host usa `MaxSessions=7` em `/etc/xrdp/sesman.ini`. A carga de cinco sessões
passou; a tentativa de dez ficou em sete e foi interrompida. O estágio de 25
não foi iniciado. Não foi alterado o limite do host. A limpeza verificou ausência
de contas temporárias; o roteiro de carga também verifica processos por UID.
KDE não foi executado porque `startplasma-x11` não está instalado. Snap está ausente;
Flatpak sem org.gnome.Calculator é registrado como não executado. A aceitação
Windows utilizou Wine; UMU/Proton não recebeu teste gráfico nesta rodada. Os
testes de instalação nativa nos contêineres não exercitam sessões xrdp ou
ativação real de políticas systemd/PolicyKit dentro desses contêineres.

O build e a verificação estática do site passaram sem alteração do site. `npm ci`
reportou 12 vulnerabilidades nas dependências existentes (1 moderada, 10 altas,
1 crítica); a atualização desse conjunto não faz parte da reorganização.
Não houve publicação de release.

## Alterações locais preservadas

A cópia para os módulos canônicos incluiu as alterações já existentes em
`de_installer.py` e `server_config.py`. Foram preservadas as alterações locais
nos helpers `apply-user-resource.py`, `create-session-wrapper.sh`,
`rdpsm-session.py`, no instalador, em TROUBLESHOOTING e nos testes de desktops,
servidor e sessões nativas. Ambientes locais, caches, logs, backups e arquivos
ignorados pelo Git não foram objeto da remoção.

## Remoção da estrutura antiga

Após a validação inicial, foram removidos os 32 arquivos Python da estrutura
antiga, incluindo os aliases de `src/core`, `src/ui`, `src/utils` e as entradas
`src/main.py`, `src/cli.py`, `src/application.py`, `src/version.py` e `src/__init__.py`.
Os testes e seus mocks usam os módulos canônicos. O pacote distribui somente
`rdp_session_manager`, sem `py_modules` antigos. Os entry points novos aceitam
execução por módulo e por caminho absoluto, inclusive fora do checkout.
Os dados persistidos e os helpers funcionais não são duplicatas da arquitetura
e permanecem na implementação nova. Foram limpos os bytecodes exclusivos dos módulos removidos e suas cópias em
`build/lib`, para impedir sua reintrodução em um wheel. Os demais caches, logs
e ambientes locais foram preservados.

A limpeza posterior passou em **270 testes** e o wheel foi inspecionado para
confirmar ausência dos pacotes e módulos removidos.

## Etapa intermediária: pacote na raiz

O pacote foi movido de `src/rdp_session_manager` para `rdp_session_manager/` na
raiz do repositório. A pasta `src` foi removida, e setuptools, launchers,
resolução de recursos, cópia do runtime para as sessões, testes, scripts de
empacotamento e CI passaram a usar esse layout. A documentação ativa também
foi atualizada; menções à árvore anterior neste relatório descrevem o histórico
da migração, e não um segundo código disponível.

O layout na raiz passou nos 270 testes e no bootstrap. Wheel e sdist foram
inspecionados para confirmar ausência de `src/`. O wheel instalado fora do
checkout localizou interfaces, helpers e receitas, e abriu GTK sob Xvfb.
A sessão Windows com a fixture confirmou o provisionamento do runtime pelo
novo caminho. Debian 13 e Arch passaram novamente no build e na instalação.

## Estrutura definitiva em src

Por preferência final do usuário, o pacote voltou para
`src/rdp_session_manager/`. Existe somente essa implementação; os módulos antigos
não foram restaurados. Testes, helpers, launchers, setuptools, receitas de
empacotamento e CI estão alinhados com esse layout. A documentação ativa usa
os caminhos em src; a etapa na raiz acima é apenas o registro da migração.

A restauração passou novamente nos **270 testes**, na CLI sem GTK, na ativação
GTK sob Xvfb, no bootstrap e na inspeção de wheel/sdist. As limitações de carga
e dos cenários não executados descritas neste relatório permanecem válidas.
