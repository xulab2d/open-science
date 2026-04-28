# Xu Lab Codex UI

Lightweight Codex web UI fork for Xu Lab deployment.

[![npm](https://img.shields.io/npm/v/codexapp?style=for-the-badge&logo=npm&logoColor=white)](https://www.npmjs.com/package/codexapp)
[![platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20Android-blue?style=for-the-badge)](#-quick-start)
[![node](https://img.shields.io/badge/Node-18%2B-339933?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org/)
[![license](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](./LICENSE)

This fork starts from `friuns2/codexui` and changes the deployment assumptions:
- external auth and access control are expected to be handled by Cloudflare or another reverse proxy
- the built-in password gate is disabled by default
- the GitHub trending-projects surface is removed

```text
 ██████╗ ██████╗ ██████╗ ███████╗██╗  ██╗██╗   ██╗██╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝╚██╗██╔╝██║   ██║██║
██║     ██║   ██║██║  ██║█████╗   ╚███╔╝ ██║   ██║██║
██║     ██║   ██║██║  ██║██╔══╝   ██╔██╗ ██║   ██║██║
╚██████╗╚██████╔╝██████╔╝███████╗██╔╝ ██╗╚██████╔╝██║
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝
```

---

## 🤯 What Is This?
**`codexapp`** is a lightweight bridge that gives you a browser-accessible UI for Codex app-server workflows.

You run one command. It starts a local web server. You open it from your machine, your LAN, or wherever your setup allows.  

**TL;DR 🧠: Codex app UI, unlocked for Linux, Windows, and Termux-powered Android setups.**

---

## Deployment model

This fork is intended to run behind external auth.

Default behavior:
- no app-level password gate
- Codex account management remains available inside the UI

## Quick Start

```bash
# run locally from source
pnpm install
pnpm run build
node dist-cli/index.js --port 5901

# 🌐 Then open in browser
# http://localhost:18923
```

If you do not want automatic `codex login` bootstrap:

```bash
node dist-cli/index.js --port 5901 --no-login
```

## Notes

- this fork still supports the upstream account-management features for Codex itself
- tunnel support remains available, but auth is expected to be handled outside the app
- upstream repository: [friuns2/codexui](https://github.com/friuns2/codexui)
