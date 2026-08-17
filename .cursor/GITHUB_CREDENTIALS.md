# GitHub credentials for Cloud Agents on this machine

Agents read credentials from **machine-local files** (never committed):

| File | Purpose |
|------|---------|
| `~/.config/cursor/github.env` | `source` this for `GH_TOKEN` / `GITHUB_TOKEN` |
| `~/.config/cursor/github_pat` | Raw PAT (chmod 600) |
| `~/.config/gh/hosts.yml` | `gh` CLI auth as `youtextme` |
| `~/.git-credentials` | `git push` / `git clone` over HTTPS |

## Usage

```bash
source ~/.config/cursor/github.env
gh auth status
git push origin main
```

Also mirrored under `/home/ubuntu/` and `/tmp/rfr-home/` when both homes exist.

**Current auth:** classic PAT for `youtextme` with full repo access (stored locally only).

## Security

- Never commit PAT files. Workspace `.gitignore` blocks `*.pat` patterns.
- Rotate the token if it was pasted in chat or shared broadly.
