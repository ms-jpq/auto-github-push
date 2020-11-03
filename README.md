# [Auto Github Push](https://github.com/ms-jpq/auto-github-push)

This Docker image will automatically push a file called `.agp` under `.github/` for every public repo you own.

This will refresh various Github inactivity countdowns.

## How to use

0. Create an empty repo

1. Create a token with repo access.

2. Add `CI_TOKEN` to repo's secrets

3. Add `.github/workflows/agp.yml` to the repo. [Example here](https://github.com/ms-jpq/auto-github-push/blob/agp/.github/workflows/agp.yml).

And you are good!

## Disable for single repo

Add `.noagp` under `.github/`
