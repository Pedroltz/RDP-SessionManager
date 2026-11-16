# Arquitetura

A implementação fica exclusivamente em `src/rdp_session_manager`. Os módulos e
aliases antigos de `core`, `utils`, `ui`, `application`, `cli`, `main` e `version`
foram removidos. Os comandos instalados `rdpsm` e `rdp-session-manager` continuam
apontando para a implementação nova. No checkout, use `./run.sh` para GTK ou
`PYTHONPATH=src python3 -m rdp_session_manager.presentation.cli` para a CLI.

| Camada | Responsabilidade |
| --- | --- |
| `domain` | Usuários, perfis, sessões, contratos serializados de saúde/reparo, regras e limites do servidor; sem GTK, subprocessos ou APIs Linux |
| `application` | Casos de uso de usuários, planos de reparo, vínculo de aplicações Windows, snapshot do painel e coordenação de tarefas; depende de contratos estruturais |
| `infrastructure` | Contas Linux, arquivos, privilégios, comandos com timeout, diagnóstico do host, runtimes e recursos |
| `presentation/gtk` | Widgets, sinais, renderização incremental e ciclo de vida dos callbacks |
| `presentation/cli` | Argumentos, saída e códigos de retorno |
| `bootstrap.py` | Composição preguiçosa das dependências compartilhadas |

`UserManager` agora é o adaptador Linux. Os modelos saíram para `domain/users.py`,
a persistência de perfis para `infrastructure/user_profiles.py` e o cache de
estados para `infrastructure/persistence.py`. `UserService` serializa consultas
e alterações e invalida sessões inclusive após falhas parciais. As instâncias
com configuração e somente leitura compartilham o mesmo lock na composição.

O painel consulta cada repositório uma vez por ciclo, fora da thread GTK. Uma
nova atualização solicitada após alteração fica pendente caso uma consulta esteja
em andamento. Consultas periódicas sobrepostas são descartadas. A renderização
compara os dados e mantém as linhas inalteradas. A descoberta de sessões e a
coleta de consumo compartilham uma enumeração de processos e um cache protegido
por lock. A primeira amostra de CPU sem intervalo pode ser zero; as seguintes
representam o intervalo entre consultas.

`BackgroundTasks` controla trabalho em andamento; `CallbackScope` registra os
sources GLib. Fechar janelas/diálogos cancela os sources e impede novas entregas.
Operações privilegiadas já iniciadas terminam normalmente, sem atualizar
widgets fechados. Isso evita interromper uma transação no meio da execução.

Gravações de configuração e estados usam arquivo temporário no mesmo diretório,
`fsync` e substituição atômica. Estados são mesclados sob `flock`, com permissão
0600. Perfis mantêm a versão 2 e o fallback para listas/perfil único legado;
o helper valida o JSON e substitui o arquivo completo com permissão 0644. Essa
substituição não torna atômico o conjunto de alterações em perfis, wrapper e
limites systemd; reparos continuam usando os snapshots e rollback existentes.

Aplicações Windows gerenciadas guardam `windows_app_id`, `runtime=managed` e argv
explícito do launcher; perfis Wine/UMU antigos continuam no caminho anterior.
Não se reutiliza o argv Linux ao converter um perfil para Windows. O wrapper
privilegiado instala o launcher e os módulos Python em um runtime compartilhado
pertencente ao root, pois contas RDP não podem acessar o checkout privado do
administrador. As gravações atômicas de estados Windows preservam o proprietário
original para que o launcher da sessão possa ler e atualizar o estado.

Os adaptadores de diagnóstico do host e de lifecycle Windows continuam agrupados
na infraestrutura porque realizam leitura de certificados, processos e arquivos.
A apresentação utiliza a composição e casos de uso compartilhados, além de
adaptadores técnicos de caminhos, logging, privilégios e execução de comandos.
Testes, launchers e empacotamento usam diretamente os módulos novos. O entry
point absoluto da CLI funciona mesmo quando a elevação remove PYTHONPATH.

`paths.py` resolve recursos tanto no checkout como em instalações nativas e
wheels. O pacote inclui UI, receitas, helpers e políticas. A ativação de serviços
e políticas no sistema continua sendo responsabilidade da instalação nativa.

As regras de dependência e a CLI sem GTK são verificadas em
`tests/architecture`. Novos testes ficam em `unit`, `integration`, `architecture`
e `e2e`; os testes preexistentes na raiz continuam descobertos pelo mesmo comando,
evitando mover arquivos com alterações locais durante esta rodada.
