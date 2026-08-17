# GitHub credentials for Cloud Agents on this machine

**Canonical store:** `~/.config/agent/` (mirrored to Cursor, Devin, OpenClaw)

| File | Purpose |
|------|---------|
| `~/.config/agent/github.env` | `source` → `GH_TOKEN` / `GITHUB_TOKEN` |
| `~/.config/agent/github_pat` | Girish Mahadevan classic PAT for **youtextme** (`chmod 600`) |
| `~/.config/agent/load-github.sh` | Loader for any shell |

Host mirrors: `~/.config/cursor/`, `~/.config/devin/`, `~/.config/openclaw/`

## Agent instructions installed

| Host | Where agents learn about the PAT |
|------|----------------------------------|
| **Cursor** | `.cursor/rules/github-credentials.mdc` (`alwaysApply: true`) |
| **Devin** | `.devin/GITHUB_CREDENTIALS.md` |
| **OpenClaw** | `AGENTS.md` block + `~/.openclaw/github.env` |

Re-install anytime:

```bash
python3 -m runforrestrun --install-github
```

## Usage

```bash
source ~/.config/agent/load-github.sh
gh auth status
```

## Security

- Never commit PAT files. Workspace `.gitignore` blocks `*.pat` patterns.
- This is a **personal access token** — rotate at https://github.com/settings/tokens if exposed.
