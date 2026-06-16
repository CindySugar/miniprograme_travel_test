# AGENTS.md

## 基本原则
开始前先查看 `codegraph` 状态；如果没有创建索引，先运行 `codegraph init`。
完成代码后，更新 `codegraph` 索引。

开始任何代码编辑前，先读取并遵守 `~/.codex/skills/karpathy-guidelines/SKILL.md`。
修改时优先最小改动，先理解再动手。

## 工作方式
- 先读代码和现有约定，再决定怎么改。
- 不做无关重构，不顺手优化旁边代码。
- 如果需求不清楚，先说明不确定点，再继续。
- 优先沿用项目现有风格、结构和工具链。
- 本仓库已启用本地 Git 版本管理，并已连接 GitHub 线上仓库（`origin`）；后续改动优先以提交历史来追踪和回溯，必要时同步到该远端。
- Codex 在本项目中承担本地版本管理员角色，负责维护工作区改动、提交前检查和变更说明；GitHub 联动直接沿用现有 `origin`。

## 变更要求
- 每个改动都要能对应到用户需求。
- 只删除因本次修改而变成无用的代码。
- 发现相关但未请求的缺陷时，先提示，不要擅自扩大范围。

## 验证要求
- 改完后尽量跑最小必要验证。
- 如果有测试，优先补测试或跑相关测试。
- 如果无法验证，明确说明原因和残留风险。

## 前端验证
- 前端界面完成后，优先用 Playwright 做页面级检查，重点看布局、字号、换行、按钮状态和截图对照。
- 微信小程序页面再用微信开发者工具做真实环境验证，优先通过 `miniprogram-automator` 配合 `mcp__node_repl` 连接并驱动当前项目。
- 我这里成功连接微信开发者工具的方法是：确认桌面端微信开发者工具已打开，且 CLI 路径可用，然后执行
  `automator.launch({ cliPath: '/Applications/wechatwebdevtools.app/Contents/MacOS/cli', projectPath: '/Users/boluobao/WeChatProjects/miniprogram-1', trustProject: true, timeout: 60000 })`
  再用 `miniProgram.currentPage()`、`miniProgram.screenshot()` 做检查。若已有可用自动化窗口，也可以尝试 `connect({ wsEndpoint: 'ws://127.0.0.1:<port>' })`。
- 如果验证失败，先区分是页面代码问题还是 DevTools/自动化连接问题，再决定是否改代码。

## 交付要求
- 给出简短结论，说明改了什么、是否验证、是否还有风险。
- 如果项目里还有更深层级的 `AGENTS.md`，优先遵守更近的那份。
