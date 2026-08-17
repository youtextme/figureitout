# Publish this folder as its own GitHub repository

This token cannot create `youtextme/run-forrest-run` from the cloud agent
(integration scope is the current repo only). Publish from a machine that
can create repos:

```bash
cd run-forrest-run
git init
git add .
git commit -m "Run, Forrest, Run! — objective-runner platform."
gh repo create youtextme/run-forrest-run --public --source=. --remote=origin --push
```

Then point the homepage in `pyproject.toml` at that URL.

Until then, this folder is the complete platform and ships inside
`youtextme/figureitout` so nothing is lost.
