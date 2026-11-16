export type Locale = "pt" | "en";

type Feature = { title: string; body: string };
export type SiteContent = {
  locale: Locale;
  langName: string;
  nav: { features: string; compatibility: string; install: string };
  hero: { kicker: string; title: string; accent: string; body: string; install: string; github: string };
  preview: {
    alt: string; caption: string; label: string; choose: string; desktopDetail: string;
    terminalIntro: string; terminalOutput: string; terminalNote: string; cliDocs: string;
    terminalCaption: string; terminalDetail: string; terminalScroll: string;
  };
  features: { kicker: string; title: string; body: string; items: Feature[] };
  compatibility: { kicker: string; title: string; body: string; groups: { title: string; items: string[] }[] };
  install: { kicker: string; title: string; body: string; copy: string; copied: string; copyFailed: string; requirements: string; reqBody: string; docs: string; releases: string };
  faq: { kicker: string; title: string; items: { question: string; answer: string }[] };
  footer: string;
};

const pt: SiteContent = {
  locale: "pt",
  langName: "English",
  nav: { features: "Recursos", compatibility: "Compatibilidade", install: "Instalação" },
  hero: {
    kicker: "Open source · Feito para Linux",
    title: "Seu servidor RDP.",
    accent: "Tudo sob controle.",
    body: "Gerencie usuários, desktops e aplicações remotas em uma interface nativa para Linux. Menos configuração manual, mais tempo para o que importa.",
    install: "Começar a usar",
    github: "Ver no GitHub"
  },
  preview: {
    alt: "Interface do RDP Session Manager mostrando usuários RDP, sessões e saúde do servidor com dados de exemplo.",
    caption: "Interface real do aplicativo · Dados de exemplo",
    label: "Seu servidor, do seu jeito",
    choose: "Escolher visualização do aplicativo",
    desktopDetail: "Interface nativa · GTK 4 + libadwaita",
    terminalIntro: "A mesma operação, direto do terminal.",
    terminalOutput: "Exemplos de saída dos comandos rdpsm user list e rdpsm session list",
    terminalNote: "Comandos reais da CLI",
    cliDocs: "Explorar a CLI",
    terminalCaption: "Prévia da CLI · Dados de exemplo",
    terminalDetail: "Saída em tabela ou JSON para seus scripts",
    terminalScroll: "Deslize para ver a tabela completa."
  },
  features: {
    kicker: "Uma interface, menos trabalho",
    title: "O essencial para administrar RDP.",
    body: "Do primeiro usuário ao diagnóstico do servidor, organize sua operação em um só lugar.",
    items: [
      { title: "Usuários e sessões", body: "Crie, habilite e monitore contas RDP. Veja quem está conectado e encerre sessões quando precisar." },
      { title: "Desktops e RemoteApps", body: "Ofereça um desktop completo ou publique uma aplicação Linux em uma janela dedicada." },
      { title: "Aplicações Windows", body: "Execute aplicações compatíveis com umu/Proton, com prefixos por usuário e suporte a perfis WineGE legados." },
      { title: "Automação via CLI", body: "Use rdpsm nos seus scripts, consulte dados em JSON e automatize as rotinas do servidor." },
      { title: "Diagnóstico integrado", body: "Confira a saúde do host, dos usuários e das sessões. Revise planos de reparo antes de aplicá-los." },
      { title: "Administração com controle", body: "Operações privilegiadas passam pelo PolicyKit. Reparos gerenciados têm rollback e registro de auditoria." }
    ]
  },
  compatibility: {
    kicker: "Do Linux para a sua tela",
    title: "Escolha seu ambiente.",
    body: "O administrador roda no servidor Linux. Seus usuários acessam as sessões com um cliente RDP compatível.",
    groups: [
      { title: "Servidor", items: ["Ubuntu 22.04+", "Debian 12+", "Arch Linux e derivados"] },
      { title: "Desktop remoto", items: ["GNOME", "KDE Plasma", "XFCE"] },
      { title: "Clientes RDP", items: ["Windows · Linux · macOS", "Android · iOS", "Cliente com suporte ao tipo de sessão"] }
    ]
  },
  install: {
    kicker: "Comece em poucos passos",
    title: "Seu próximo passo é simples.",
    body: "Execute o instalador oficial no servidor Linux. Ele identifica a distribuição, verifica os artefatos e orienta a instalação das dependências.",
    copy: "Copiar comando",
    copied: "Copiado!",
    copyFailed: "Selecione o comando e copie manualmente.",
    requirements: "Requisitos do servidor",
    reqBody: "Python 3.9+, GTK 4, libadwaita e PolicyKit em uma distribuição suportada. Consulte o guia para dependências e opções de instalação.",
    docs: "Guia de instalação",
    releases: "Ver releases"
  },
  faq: {
    kicker: "Dúvidas frequentes",
    title: "Antes de começar.",
    items: [
      { question: "Preciso instalar o aplicativo no computador de cada usuário?", answer: "O RDP Session Manager roda no servidor Linux. Nos dispositivos dos usuários, basta um cliente RDP compatível com o tipo de sessão oferecido." },
      { question: "Qualquer aplicação Windows funciona?", answer: "A compatibilidade depende da aplicação e do runtime umu/Proton. Aplicações que precisam de drivers próprios ou recursos específicos do Windows podem não funcionar. Prefixos WineGE existentes continuam com suporte legado." },
      { question: "Preciso oferecer um desktop completo?", answer: "Não. Você pode oferecer um desktop GNOME, KDE Plasma ou XFCE, ou publicar apenas uma aplicação Linux ou Windows compatível como RemoteApp." },
      { question: "Posso administrar pelo terminal?", answer: "Sim. A CLI rdpsm permite gerenciar usuários, sessões, dependências e configuração, além de consultar a saúde do servidor com rdpsm health." }
    ]
  },
  footer: "Administração RDP mais simples no Linux. Código aberto, licença GPL-3.0."
};

const en: SiteContent = {
  locale: "en",
  langName: "Português",
  nav: { features: "Features", compatibility: "Compatibility", install: "Install" },
  hero: {
    kicker: "Open source · Built for Linux",
    title: "Your RDP server.",
    accent: "Under control.",
    body: "Manage users, desktops and remote applications in a native Linux interface. Less manual configuration, more time for what matters.",
    install: "Get started",
    github: "View on GitHub"
  },
  preview: {
    alt: "RDP Session Manager interface showing RDP users, sessions and server health with sample data.",
    caption: "Actual application interface · Sample data",
    label: "Your server, your workflow",
    choose: "Choose application preview",
    desktopDetail: "Native interface · GTK 4 + libadwaita",
    terminalIntro: "The same workflow, straight from your terminal.",
    terminalOutput: "Example output of rdpsm user list and rdpsm session list",
    terminalNote: "Real CLI commands",
    cliDocs: "Explore the CLI",
    terminalCaption: "CLI preview · Sample data",
    terminalDetail: "Table or JSON output for your scripts",
    terminalScroll: "Swipe to see the full table."
  },
  features: {
    kicker: "One interface, less work",
    title: "The essentials for managing RDP.",
    body: "From your first user to server diagnostics, keep your operation in one place.",
    items: [
      { title: "Users and sessions", body: "Create, enable and monitor RDP accounts. See who is connected and end sessions when needed." },
      { title: "Desktops and RemoteApps", body: "Offer a full desktop or publish a Linux application in its own remote window." },
      { title: "Windows applications", body: "Run compatible applications with umu/Proton, per-user prefixes and support for legacy WineGE profiles." },
      { title: "Automation through the CLI", body: "Use rdpsm in your scripts, query JSON output and automate routine server tasks." },
      { title: "Integrated diagnostics", body: "Check host, user and session health. Review repair plans before applying them." },
      { title: "Controlled administration", body: "Privileged operations use PolicyKit. Managed repairs include rollback and audit records." }
    ]
  },
  compatibility: {
    kicker: "From Linux to your screen",
    title: "Choose your environment.",
    body: "The administration app runs on your Linux server. Users connect through an RDP client compatible with their session type.",
    groups: [
      { title: "Server", items: ["Ubuntu 22.04+", "Debian 12+", "Arch Linux and derivatives"] },
      { title: "Remote desktop", items: ["GNOME", "KDE Plasma", "XFCE"] },
      { title: "RDP clients", items: ["Windows · Linux · macOS", "Android · iOS", "Client with support for the session type"] }
    ]
  },
  install: {
    kicker: "Get started in a few steps",
    title: "A simple next step.",
    body: "Run the official installer on your Linux server. It detects your distribution, verifies release assets and guides dependency installation.",
    copy: "Copy command",
    copied: "Copied!",
    copyFailed: "Select the command and copy it manually.",
    requirements: "Server requirements",
    reqBody: "Python 3.9+, GTK 4, libadwaita and PolicyKit on a supported distribution. See the guide for dependencies and installation options.",
    docs: "Installation guide",
    releases: "View releases"
  },
  faq: {
    kicker: "Frequently asked questions",
    title: "Before you get started.",
    items: [
      { question: "Does every user need to install the application?", answer: "RDP Session Manager runs on the Linux server. User devices only need an RDP client compatible with the session type you offer." },
      { question: "Will every Windows application work?", answer: "Compatibility depends on the application and the umu/Proton runtime. Applications requiring custom drivers or Windows-specific features may not work. Existing WineGE prefixes retain legacy support." },
      { question: "Do I need to offer a full desktop?", answer: "No. You can offer a GNOME, KDE Plasma or XFCE desktop, or publish a single compatible Linux or Windows application as a RemoteApp." },
      { question: "Can I manage the server from a terminal?", answer: "Yes. The rdpsm CLI manages users, sessions, dependencies and configuration. You can also check server health with rdpsm health." }
    ]
  },
  footer: "Simpler RDP administration on Linux. Open source, licensed under GPL-3.0."
};

export const content: Record<Locale, SiteContent> = { pt, en };
