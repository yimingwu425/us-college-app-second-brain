# Upgrade from v2 to v3

## Safety Rule

Never overwrite a filled vault. Copy the existing vault before migrating.

## Steps

1. Back up the existing `美本申请第二大脑/` folder.
2. Copy the new `dist/CLAUDE.md` into the AI workspace.
3. Copy `templates/vault/` to a temporary folder.
4. Move existing filled files from the old vault into the matching v3 paths.
5. Add missing v3-only folders such as `记忆库/强制规则/`, `素材库/关系/`, and `学校研究/学校名/`.
6. Open `本体画像/00-核心身份.md` and add `学制` plus `申请季开始时间` if they are missing.
7. Start a fresh AI conversation and say `启动`.

## Do Not Migrate By

- Replacing the whole old vault with `templates/vault/`.
- Deleting old memory files because they look messy.
- Merging unrelated students into one vault.
