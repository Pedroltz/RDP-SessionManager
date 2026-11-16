# README media

These assets are shared by the Portuguese and English READMEs. They use the
website's graphite/violet palette without depending on website build output.

- `banner.svg`: vector banner using the website's overlapping terminal mark.
  It includes an opaque background, an accessible title and description, and
  no external fonts, scripts or remote resources.
- `dashboard.png`: actual GTK `MainWindow`, captured at 1040 × 700 in dark mode
  on an isolated Xvfb display. The application services were replaced with
  example data; no server accounts, settings or services were modified.
- `create-user.png`: actual GTK `UserDialog`, captured at 1040 × 820 in the same
  isolated setup, with a fictional `office-team` account and LibreOffice Writer
  RemoteApp configuration. Password fields remain empty and Create is never
  activated.
- `cli.png`: HTML-rendered terminal frame containing stdout from the actual
  `CLI.user_list` and `CLI.session_list` methods, called with example user and
  session services. Formatting and values come from the CLI rather than a
  manually drawn output table. No administrative commands were executed.

The example accounts are `design-team`, `libreoffice` and `remote-desktop`.
`192.0.2.10` is a documentation example address. Health results are illustrative,
not a diagnosis of the machine used to create the assets. Captions in both
READMEs identify sample data. Clickable image links expose the full resolution.

To refresh the captures, use the actual UI classes and CLI output with the same
isolated example data. Preserve the read-only capture process and check that no
real account names, addresses, credentials or operational logs are included.
