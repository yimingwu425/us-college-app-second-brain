# Upgrade from v2 to v3

## Safety Rule

Never overwrite a filled vault. Copy the existing vault before migrating.

## Steps

1. Back up the existing `美本申请第二大脑/` folder.
2. Copy the new `dist/CLAUDE.md` into the AI workspace.
3. Copy `templates/vault/` to a temporary folder.
4. copy existing filled files from the old vault into the matching v3 paths. Do not move them out of the old vault.
5. Add missing v3-only folders such as `记忆库/强制规则/`, `素材库/关系/`, and `学校研究/学校名/`.
6. When unsure or when files conflict, preserve both versions and resolve manually.
7. Open `本体画像/00-核心身份.md` and add `学制` plus `申请季开始时间` if they are missing.
8. Start a fresh AI conversation and say `启动`.
9. do not delete or modify the old vault until `启动` succeeds in a fresh conversation.

## Do Not Migrate By

- Replacing the whole old vault with `templates/vault/`.
- Deleting old memory files because they look messy.
- Merging unrelated students into one vault.
