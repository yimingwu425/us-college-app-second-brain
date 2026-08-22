# ZCode optional integration

核心流程依赖学生 vault 中的 `AGENTS.md`，不依赖 hook。这个示例只在 ZCode `SessionStart` 时运行安装后的 `brain hook session-context`，把当前时间、checkpoint 和开放任务注入会话。

将 `config.example.json` 中的 `hooks` 内容合并到学生 vault 的 `.zcode/config.json`。配置文件 hook 必须保留 `enabled: true`，并确保 `brain` 已安装且在 PATH 中。

hook 只读上下文，不写学生资料。写入、任务完成和知识检索仍由 agent 按 `AGENTS.md` 显式调用 `brain`。没有 hook 的 Codex 或其他客户端仍可依靠 `AGENTS.md` 在会话开始调用 `brain context --json`。
