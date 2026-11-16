#!/bin/sh
# Mirror .claude/agents and .claude/commands for Codex (AGENTS.md). Claude files stay the single source:
# the generated agents and skills only point back to them.
set -eu
cd "$(dirname "$0")/../.."
mkdir -p .codex/agents
for f in .claude/agents/*.md; do
  n=$(sed -n 's/^name: //p' "$f"); d=$(sed -n 's/^description: //p' "$f" | sed 's/"/\\"/g')
  ro=""; grep -q '^tools: Read, Grep, Glob, Bash$' "$f" && ro='sandbox_mode = "read-only"
'
  cat > ".codex/agents/$n.toml" <<EOF
# Generated from .claude/agents/$n.md by \`make codex-sync\`: edit that file, not this one.
name = "$n"
description = "$d"
${ro}developer_instructions = """
Your role and rules are in .claude/agents/$n.md: read it in full (ignore its YAML frontmatter) and follow it as your instructions.
Also follow AGENTS.md and CLAUDE.md at the repo root.
"""
EOF
done
# Skills keep their hand-written descriptions; only commands without one get a stub.
for f in .claude/commands/*.md; do
  c=$(basename "$f" .md); s=".agents/skills/$c/SKILL.md"
  [ -f "$s" ] && continue
  mkdir -p ".agents/skills/$c"
  printf -- '---\nname: %s\ndescription: %s Use quando o usuário pedir /%s ou $%s.\n---\n\nSingle source: `.claude/commands/%s.md` (the Claude Code command). Read it in full and follow it exactly.\nText after the skill name in the user'"'"'s message is the command argument (`$ARGUMENTS`).\nBefore starting, read AGENTS.md: it maps Claude-only tools (subagents, connectors) to Codex.\n' \
    "$c" "$(head -c 200 "$f" | head -1)" "$c" "$c" "$c" > "$s"
done
echo "codex-sync: $(ls .codex/agents | wc -l) agents, $(ls .agents/skills | wc -l) skills"
