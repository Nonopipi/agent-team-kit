# Codex Agent Team

一套可复用的 Codex 多代理协作模板：一个主会话协调九个专业代理，按顺序完成设计、规划、测试、实现和审查。适合希望使用明确角色分工的软件项目。

A reusable Codex agent-team template: one orchestrator coordinates nine specialist agents through design, planning, tests, implementation and review. It contains instructions and configuration, with no application code or external-service credentials.

## 文件结构 / Files

```text
codex-agent-team/
├── README.md
├── LICENSE
├── .gitignore
├── AGENTS.md
└── .codex/
    ├── config.toml
    └── agents/
        ├── architect.toml
        ├── planner.toml
        ├── tdd_test_writer.toml
        ├── frontend_dev.toml
        ├── backend_dev.toml
        ├── database_dev.toml
        ├── code_reviewer.toml
        ├── security_auditor.toml
        └── git_committer.toml
```

`.codex/` 是隐藏目录，也是模板的必要部分；复制或上传时请一并保留。

## 快速开始

1. 下载或克隆本仓库。在 Codex 中把仓库目录设为项目主文件夹，并在其中新建会话。也可以在仓库根目录打开终端，运行：

   ```sh
   codex -C .
   ```

2. 检查 `AGENTS.md`、`.codex/config.toml` 和各代理定义。如果客户端提示信任项目，由你决定是否信任；项目级配置仅在受信任的项目中加载。
3. 说明你要做的产品、使用者和首版功能，例如：

   ```text
   按 AGENTS.md 的流程及九个代理的分工工作。
   我想做一个……，面向……，首版需要……。
   先检查本项目的代理是否可用，再确认需求并由 architect 提出设计。
   需要我决定的取舍先说明，已有明确授权的常规步骤继续执行。
   ```

4. 采用模板后，将 `AGENTS.md` 中待确认的产品信息替换为项目事实，包括技术栈、开发命令、测试命令及测试数据库。只记录已核实的信息。

用于已有项目时，先检查其现有 `AGENTS.md`、配置、设计文档和任务记录，再合并适用部分。不要直接覆盖原有规范，也不要覆盖已有的 `.codex/config.toml`。从目标项目根目录开启新会话，以便发现项目规则和代理定义。

桌面应用的项目设置可能随版本变化。主文件夹与新会话的规则见[官方项目说明](https://learn.chatgpt.com/docs/projects)。

## 角色与流程 / Roles and workflow

| 代理 | 职责 |
| --- | --- |
| `architect` | 系统设计与 `architecture/` 文档 |
| `planner` | 任务拆分与 `tasks/` 记录 |
| `tdd_test_writer` | 编写行为测试并验证预期失败（RED） |
| `frontend_dev` | 前端实现与界面验证 |
| `backend_dev` | 后端实现及首次测试框架初始化 |
| `database_dev` | 数据模型、迁移和测试数据 |
| `code_reviewer` | 只读审查，报告问题及检查范围 |
| `security_auditor` | 按任务范围执行只读安全审查 |
| `git_committer` | 检查指定文件并创建本地提交 |

```text
确认需求 → architect → 设计决策确认 → planner
→ tdd_test_writer（RED）→ 实现代理（GREEN）
→ code_reviewer → 必要时修复和安全审查 → git_committer
```

每次只委派一个代理。若项目尚无测试框架，先由 `backend_dev` 初始化框架、留下通过的冒烟测试并记录可用命令，再进入正常 RED/GREEN 流程。配置或文档整理采用相关检查，无需虚构应用测试。

Git 未初始化时，按明确的文件列表核对并报告“未提交”；本模板不会把配置或规划视为初始化 Git、上传、发布或部署的授权。

## 默认配置与限制

```toml
[agents]
enabled = true
max_concurrent_threads_per_session = 1
```

- 九个角色定义位于 `.codex/agents/`。模型与推理设置沿用主会话，不预设某个付费模型或第三方服务。
- 子代理继承主会话权限。角色中的“只读”和安全规则是行为指引，不会创建独立的权限锁或保证执行结果。
- 主会话等待代理完成后收回报告，并在客户端支持时关闭或释放其槽位。若客户端限制阻止继续，报告限制，避免重复尝试。
- 本模板包含委派指令；实际发现与调度仍取决于所用 Codex 客户端、版本和权限。静态检查通过不等于运行验证通过。
- `.gitignore` 排除常见本机文件、密钥文件和会话输出；它不会清除已经提交到 Git 历史中的内容。

## 本地检查 / Local checks

安装 Python 3.11 或以上版本时，可在仓库根目录解析配置文件：

```sh
python3 - <<'PYTHON'
from pathlib import Path
import tomllib

files = [Path('.codex/config.toml'), *sorted(Path('.codex/agents').glob('*.toml'))]
for path in files:
    with path.open('rb') as stream:
        tomllib.load(stream)
    print('OK', path)
PYTHON
```

支持以下选项的 Codex CLI 可执行启动配置检查：

```sh
codex --strict-config -C . app-server --print-startup-config
```

这两项检查分别核对 TOML 语法和 CLI 启动配置，不证明九个代理已在新会话中实际发现或成功派发。应在自己的项目会话中另外核实，并按实际结果更新项目记录。

官方参考：[Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference)。

## English quick start

1. Open the repository as the primary project folder and start a new Codex conversation, or run `codex -C .` from its root.
2. Review the instructions and configuration before trusting the project. Provide your product brief and ask Codex to verify the nine agents are available.
3. Replace the pending project facts in `AGENTS.md` with verified requirements and commands. When adopting into an existing project, merge with its existing instructions and configuration.
4. Follow the sequential workflow above. Bootstrap the test runner first if absent. Confirm actual agent dispatch separately from configuration parsing.

The `.codex/` directory is required even though it is hidden. Reviewers are read-only by instruction and inherit the parent's permissions. Sending, uploading, publishing and deployment require the user's authorization for the specific action.

## 许可 / License

MIT — see [LICENSE](LICENSE). The copyright notice uses the project contributor name rather than a personal name. Preserve applicable upstream notices when incorporating third-party material.
