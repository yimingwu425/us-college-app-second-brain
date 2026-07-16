# Setup

## Install

1. Create an empty folder.
2. For Claude, copy `dist/CLAUDE.md` into that folder and name it `CLAUDE.md`.
3. For Codex/general agents, copy `dist/AGENTS.md` into that folder and name it `AGENTS.md`.
4. Start a new AI conversation in that folder and say `启动`.
5. The assistant creates the workspace, including material and artifact folders.

End users only need one runtime file from `dist/`.

## Useful Fields

- `姓名/称呼`
- `性别`
- `申请身份`
- `年级`
- `学制`
- `申请季开始时间`
- `所在城市/家乡`

Fill them in `本体画像/` if you like. You can also just talk; the assistant keeps facts and judgments in the right places.

## Daily Use

Talk about experiences, schools, deadlines, drafts, and doubts in plain language.

The assistant:

- keeps understanding in `用户画像.md`
- keeps facts in `本体画像/`
- stores raw material in `素材库/`
- tracks schools and deadlines under `学校研究/` and `申请追踪/`
- puts submit-oriented drafts under `文书/`, `活动列表/`, `推荐信/` when needed

## Demo

See `examples/demo-vault/` for a fictional filled workspace (林夏舟). Not a real student, not an admissions template.
