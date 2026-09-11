# Evidence-Bound Execution

Keep AI agents accountable to actual requirements. A Codex and Claude Code skill for mapping corrections to deliverables and checking evidence before claiming completion.

[View on skills.sh](https://skills.sh/ShiYuPro/evidence-bound-execution/evidence-bound-execution)

## Install

With [Skills CLI](https://skills.sh/docs) (Node.js and npm required):

```sh
npx skills add ShiYuPro/evidence-bound-execution --skill evidence-bound-execution
```

Choose Codex or Claude Code when prompted. This installs into the current project;
review the destination if you already have this skill installed.

Or install directly with Git:

From your project directory, choose the command for your agent. Existing destinations
are not overwritten by `git clone`.

**Codex:**

```sh
git clone https://github.com/ShiYuPro/evidence-bound-execution.git .agents/skills/evidence-bound-execution
```

**Claude Code:**

```sh
git clone https://github.com/ShiYuPro/evidence-bound-execution.git .claude/skills/evidence-bound-execution
```

Invoke `$evidence-bound-execution` in a new task. Discovery depends on your host's support for
`SKILL.md`; installation does not change project policy or grant external permissions.

## First use

> Use $evidence-bound-execution to fix the mobile purchase button. Keep it visible at 390 px wide without covering the terms or changing the price.

Run helper commands from the installed skill directory or this repository root.
See [setup and examples](references/example.md) and the [full skill](SKILL.md).

## Requirements

Python 3.9+, standard library only. Ordinary tasks use a short execution card; JSON gates are optional for traceability-heavy work.

## Verify locally

```sh
python3 scripts/check.py
```

Tests use temporary fixtures and mocked responses. They do not clean your project,
call paid model APIs, or deploy a production service.

## Boundaries

The script checks recorded evidence mappings and revisions, not the truth of an uploaded screenshot or a reviewer statement. Use outcome-level review for qualitative requirements and never impersonate an independent reviewer.

## Sources and license

See [SOURCES.md](SOURCES.md) for reviewed alternatives and adaptation decisions,
and [LICENSE](LICENSE) for terms. This standalone repository was split from
[Agent Workflow Skills](https://github.com/ShiYuPro/agent-workflow-skills).
Future changes for this skill belong here.

## Creator

Built by [Shiyu Yang](https://github.com/ShiYuPro). Explore [my apps and open-source work](https://shiu.pro/). For job opportunities, cofounder conversations, or app and website projects, [get in touch](https://shiu.pro/contact/).
