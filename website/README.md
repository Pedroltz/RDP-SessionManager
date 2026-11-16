# RDP Session Manager website

Static Astro landing page in Portuguese and English, deployed to
https://pedroltz.github.io/RDP-SessionManager/.

## Local development

Use the Node version in `.nvmrc` (with nvm: `nvm install && nvm use`), then:

```bash
npm ci
npm run dev
```

Open http://localhost:4321/RDP-SessionManager/. The English page is at
`/RDP-SessionManager/en/`.

Before publishing:

```bash
npm run build
npm run verify
npm run preview -- --host 127.0.0.1
```

With preview running, check the served pages and assets in another terminal:

```bash
npm run verify:deployment -- http://127.0.0.1:4321/RDP-SessionManager/
```

Also review both languages at desktop and phone widths, keyboard navigation,
the installation copy button, and FAQ entries. Without JavaScript, all page
content remains available and the installation command can be selected manually.

## Content and assets

`src/data/content.ts` contains both translations. Both routes use the same
landing component and layout. `astro.config.mjs` defines the public origin and
case-sensitive Pages base; all internal navigation and assets use Astro's base.
If these settings change, update `public/robots.txt` and `public/sitemap*.xml`.
`npm run verify` checks that these files agree with the Astro configuration and
that local links, anchors and generated assets resolve.

`public/app-preview.webp` is a capture of the actual GTK main window, rendered
in an isolated Xvfb display at 1040 × 700 with example accounts and the reserved
example address `192.0.2.10`. It contains no real user or server information.
The caption identifies it as sample data. Desktop/Terminal tabs switch between
this capture and an illustrative transcript of the real `rdpsm user list` and
`rdpsm session list` commands. Both previews remain visible without JavaScript;
the website does not execute commands or connect to a server.

## Deployment

See [the CI guide](../docs/CI.md). Pull requests build and validate without
publishing. Relevant pushes to `master` publish the validated artifact. Manual
runs on other branches validate only.
