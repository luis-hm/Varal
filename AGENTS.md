# Varal — instruções para o Codex

As regras do projeto são as mesmas do Claude Code e estão em **`CLAUDE.md`**. Leia-o inteiro antes de qualquer tarefa e siga-o como se fosse este arquivo: fontes da verdade, etapas, Doop, regra responsiva, convenções, commits, "sem push".

O estado vive no repositório (`docs/PROGRESSO.md`, `docs/etapas/`, git), não na sessão. Por isso o Claude Code e o Codex podem se revezar na mesma etapa. Ao parar, deixe `PROGRESSO.md` e a etapa atualizados para a outra ferramenta continuar.

## O que muda no Codex

| No `CLAUDE.md` / Claude Code | No Codex |
| --- | --- |
| Comandos `/etapa` e `/status` (`.claude/commands/`) | Skills `$etapa` e `$status` (`.agents/skills/`), que seguem o mesmo arquivo de `.claude/commands/` |
| Subagentes `varal-*` (`.claude/agents/`) | Agentes `.codex/agents/varal-*.toml` com o mesmo papel. Se não puder criar um subagente pelo nome, leia `.claude/agents/<nome>.md` e faça o papel você mesmo, na mesma ordem do fluxo |
| Conector Doop (`k0kB5dc-Vo`) | Servidor MCP `doop` do `~/.codex/config.toml`. Mesmas regras: canvas **somente leitura**, frames pelo nome, `get_guide` uma vez por sessão; use `agent_name "Codex"` |
| Conector Claude Docs ("Varal — Ajustes" e a especificação de origem) | **Não existe no Codex.** Nos passos que leem ou marcam o documento de ajustes, **pare e peça ao dono** que cole o texto atual do documento. Ao fim da etapa, liste no relatório os itens a marcar como " — feito na etapa NN": quem marca é o dono ou o Claude Code. Nunca pule o passo e nunca use uma cópia antiga. A reexportação de `docs/especificacao-varal.md` também fica para o Claude Code |
| Hook RTK e memória do Claude | Não se aplicam |

Se `.claude/agents/` ou `.claude/commands/` mudar, rode `make codex-sync` para regenerar `.codex/agents/` e `.agents/skills/`.
