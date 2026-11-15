# Relatório — Etapa 03 (Espaços e grupos)

> **Contém:** entregas, evidências, segurança, decisões a confirmar, diferenças visuais e ajustes da Etapa 03.
> **Origem:** branch `etapa/03-espacos-grupos` (commits 1453a6b, 091c048, 242d916, 28c73f1, c305f27), QA, revisão `varal-seguranca` e "Varal — Ajustes" rev 24 relido ao vivo em 15/11/2026.

**Estado: concluída em 15/11/2026.** Sem push; a Etapa 04 só começa com novo `/etapa`.

## Entregas

- **Modelo (RF04, RN03, RN04):** grupo sem dono (restrição `espaco_grupo_sem_dono`; admin só por `Membro`); `Membro`, `Convite` (`token_hash`, `revogado_em`) e `Subgrupo` (casa). Migrações `espacos.0003`–`0005`, a 0004 de dados: dono legado de grupo vira `Membro` admin, sem perda de dados. Admin do Django só leitura, sem mostrar `token_hash`.
- **Filtro central (RN01, RN02, RN05, RN07, RNF01):** `api/apps/espacos/acesso.py`. Fora do espaço → 404, sem revelar existência; participante sem a ação → 403. `PERMISSOES` traz a RN05 inteira, já com as ações de conta (`criar_conta`, `editar_conta`, `pagar_qualquer`, `pagar_propria`) para a Etapa 04; pagador sem `ver_grupo`.
- **Serviços (RF04–RF07, RN04, RN21):** `api/apps/espacos/servicos.py`, tudo em transação. Invariante "≥ 1 admin" com `select_for_update` em ordem fixa (sem deadlock entre dois admins). Guarda `pre_delete` na exclusão de `Usuario` (ORM, queryset e admin do Django, com mensagem).
- **Convite (RN24, RN31):** `secrets.token_urlsafe(32)`; banco só com SHA-256; link inteiro só na resposta da criação; uso único sob concorrência; 7 dias; revogável; mesma resposta 410 para expirado, usado, revogado ou inexistente; throttle `convite_aceite` 10/h por usuário; filtro no log do Django para não gravar o token.
- **API:** rotas de grupos, membros, casas e convites ([api/README](../../api/README.md#grupos-e-convites-etapa-03)); `/api/me/` com `grupos: [{id, nome, papel}]`. Seed com um usuário por papel.
- **Web:** `/grupos` (lista e criar); `/grupos/[id]` (10 ↔ D04) em três níveis (admin; membro; observador sem ações); `/grupos/[id]/simples` ("Em breve" do pagador, com sair); `/c/[token]` (aceite no layout do login); `?proximo=` aceita só caminho local, inclusive no retorno do Google.
- **Componentes:** folha/modal `<dialog>` reutilizável (`sheet-up` < 1024px, `modal-pop` ≥ 1024px); convite 11 ↔ M05 com link encurtado e `shine` 2×; seletor de espaço no SideNav; RadioCard, MemberRow, HouseCard; JetBrains Mono via `next/font` para o link.
- **Variáveis fora do Doop** (`tokens.css`/`globals.css`): `--text-invite-link` 14px, `--leading-radio-text` 18px, `--tracking-display` -0.02em, `--tracking-label` 0.04em, `--shadow-modal` (ink 25%), `--shine-invite` (amber 18%), `--scrim-sheet` (ink 60%), `--modal-width` 560px, `--modal-height-invite` 480px, `--font-mono`. Nenhuma cor nova (`color-mix`). Ver [tokens](../../design/tokens.md#fora-do-doop).

## Critérios e evidências

Todos os 22 CAs passam. Testes em `api/tests/test_grupos.py`, `web/src/**/*.test.ts(x)` e `web/e2e/grupos.spec.ts`; nomes completos na [matriz](../../matriz-rastreabilidade.md).

| CA | Evidência |
| --- | --- |
| CA01 | `test_rf04_rn04_criar_grupo_criador_unico_admin_e_casas`, `test_rf04_criar_grupo_nome_invalido_nao_grava`, `test_rf04_rn04_criar_grupo_falha_no_meio_nao_grava`; E2E `ca01/ca04/ca05/ca17…` |
| CA02 | `test_rn03_espaco_pessoal_recusa_convite_pela_api`, `test_rn03_servico_recusa_convite_e_aceite_no_pessoal` |
| CA03 | `test_rf05_rn24_rn31_link_inteiro_uma_vez_e_banco_so_com_hash`, `test_rn31_log_do_servidor_sem_token`, `test_rn31_admin_django_nao_mostra_token_hash` |
| CA04 | `test_rf05_link_aberto_sem_sessao_e_aceito_depois_de_entrar`, `test_rnf02_retorno_google_preserva_proximo_local`; Vitest `ca04`; E2E com dois usuários e API real |
| CA05 | `test_rn24_rn31_convite_invalido_mesma_resposta_e_nada_muda` (4 estados), `test_rn24_rn31_dois_aceites_simultaneos_geram_um_membro`; E2E (reuso → 410) |
| CA06 | `test_rf05_quem_ja_e_membro_nao_muda_papel_nem_consome_convite` |
| CA07 | `test_rn31_revogar_convite_pendente`, `test_rn31_revogar_so_vale_para_pendente_usado_da_404_e_membro_fica`, `test_rn31_revogar_e_listar_convites_sem_ser_admin_403`; E2E (fechar sem usar revoga) |
| CA08 | `test_rn31_limite_aceite_11a_tentativa_429_por_usuario` |
| CA09 | `test_rn05_gestao_negada_a_quem_nao_e_admin` (3 papéis × 8 ações), `test_rn05_admin_gerencia` |
| CA10 | `test_rn05_tabela_papel_acao` (5 papéis × 6 ações) |
| CA11 | `test_rn05_rn07_detalhe_grupo_por_papel`; Vitest `ca11`; E2E com os quatro papéis |
| CA12 | `test_rn04_ultimo_admin_nao_se_rebaixa_remove_nem_sai`, `test_rn04_com_outro_admin_pode_rebaixar_e_sair`, `test_rn04_concorrencia_dois_admins_sobra_um` (3 casos, threads); E2E `ca12/ca14…` |
| CA13 | `test_rn04_exclusao_usuario_ultimo_admin_orm_e_queryset`, `test_rn04_exclusao_usuario_ultimo_admin_admin_django` |
| CA14 | `test_rn21_removido_e_quem_sai_perde_acesso_na_hora`, `test_rn21_rn31_saida_do_admin_revoga_convites_que_ele_gerou` (3 casos); E2E `ca12/ca14…` |
| CA15 | `test_rnf01_rn01_fora_do_grupo_recebe_404_em_todas_as_rotas`, `test_rnf01_ids_de_outro_grupo_na_url_do_meu_grupo_404`, `test_rn02_espaco_pessoal_de_outro_nunca_aparece` |
| CA16 | `test_rf07_criar_renomear_arquivar_casa` |
| CA17 | `test_rf05_me_e_lista_trazem_so_os_grupos_do_usuario`; Vitest `ca17` (`nav.test.tsx`); E2E |
| CA18 | Screenshots `web/e2e/__screens__/grupo-*`, `grupos-*` comparados com 10/D04; passa com as [diferenças](#diferenças-visuais-ca18) |
| CA19 | Vitest `ca19/rn31` (`grupo-pagina.test.tsx`, `papeis.test.ts`); E2E `ca19/ca20 rn31…` (folha/modal, Pagador marcado, link encurtado, cópia inteira, Esc, foco, reduced motion); screenshots `convite-*` vs 11/M05 |
| CA20 | Vitest `ca20` (`componentes.test.tsx`); E2E `ca20 rnf08/rnf09: 360px…` (alvos ≥ 44px, sem rolagem horizontal) |
| CA21 | `make types` sincronizado; regenerado após a correção M3 (`email` anulável) |
| CA22 | Verificação abaixo; segurança sem bloqueantes abertos; docs e matriz atualizadas |

| Verificação final | Resultado |
| --- | --- |
| `make test` | **143 pytest e 57 Vitest passaram** |
| `make lint` | **Passou** (ruff, ESLint, `tsc`) |
| `make types` | **Sincronizado**; OpenAPI e `web/src/types/api.ts` regenerados após a correção M3, sem diff depois |
| `make e2e` | **51 passaram, 1 ignorado de propósito** (360px só no projeto mobile) |

**Registro honesto do E2E:** uma execução logo depois de outra suíte completa teve 3 falhas `toHaveURL`. Causa atribuída ao limite de cadastro do allauth (20/min por IP), porque o E2E cria cerca de 40 contas. A reexecução passou 51/51. Proposta do QA para tornar determinístico: `ACCOUNT_RATE_LIMITS` com `signup` configurável por env só no ambiente de E2E/CI (P5). Não é bug de produção. A tarefa 12 (devops) não foi necessária: o fixture do E2E espera e tenta de novo em 429.

## Segurança e correções

Revisão `varal-seguranca`: 1 bloqueante e 1 importante, ambos corrigidos em c305f27 com testes.

- **B1 (vinha da Etapa 02):** o DRF aceitava HTTP Basic por padrão, contornando o limite de login do allauth e o CSRF. Reproduzido: `POST /api/grupos/` com Basic e sem CSRF → 201. Corrigido: `DEFAULT_AUTHENTICATION_CLASSES` só `SessionAuthentication`. Teste `test_rnf01_basic_auth_nao_autentica`.
- **I1:** admin removido ou rebaixado voltava como admin com um convite que ele mesmo gerou. Corrigido: `_desligar` e `alterar_papel` (ao deixar de ser admin) revogam os convites pendentes criados por ele. Teste `test_rn21_rn31_saida_do_admin_revoga_convites_que_ele_gerou` (remover, rebaixar, sair).
- **Menores corrigidos:** M1 `X-Frame-Options: DENY` em tudo e `Referrer-Policy: no-referrer` em `/c/`, `/entrar` e `/criar-conta`; M2 token fora do log de requisições do `next dev`; M3 e-mail dos membros só para admin ou quando o membro não tem nome (`test_rnf04_email_de_membros_so_para_admin_ou_sem_nome`).
- **Menores pendentes:**
  - **M4:** corrida rara no admin do Django registra `LogEntry` de uma exclusão que não aconteceu (só se a guarda barrar depois da confirmação; `get_deleted_objects` já barra antes). Baixo impacto; fica registrado.
  - **M5 (Etapa 11, LGPD):** o único admin de um grupo onde só ele está não consegue excluir a conta enquanto não houver "excluir grupo". O endpoint da 11 precisa tratar isso, e a exportação deve incluir `Membro` e os convites criados/usados.
  - **M6:** sem throttle na criação de grupos/convites e no GET público do convite. Sem risco de enumeração (256 bits); só volume. Aceito por ora; o limite por IP vem com a P3. O access log de produção (gunicorn/proxy) também precisa omitir o token: acrescentado à P4.

## Decisões para o dono confirmar

Implementadas com o padrão abaixo; nada bloqueia.

| # | Assunto | Padrão adotado |
| --- | --- | --- |
| 1 | Limite de aceite (RN31) | 10/h **por usuário**; por IP só com a P3 |
| 2 | Rota do pagador | `/grupos/[id]/simples` ("Em breve" até a Etapa 10) |
| Q1 | Entropia do token | `token_urlsafe(32)` = 256 bits; os "128 bits" do pedido são o mínimo |
| Q2 | "Gerenciar papéis" (D04) | Escondido; o admin toca na linha do membro para gerir |
| Q3 | Sair do grupo | Vale para todo papel; "Sair do grupo" é acréscimo sem frame, inclusive para o observador e na página do pagador |
| Q4 | Grupo de um membro só | O único admin fica bloqueado de sair, com mensagem |
| Q5 | Layout das telas sem frame | Composições do [plano](plano.md#telas-sem-frame) com os componentes do `varal-ui` |
| 3 | Fundo atrás da folha | `--scrim-sheet` ink 60%; o frame 11 pinta sólido |
| 4 | Detalhe do seletor | `Grupo · <papel>`; D04 mostra "Grupo · 4 membros", mas `/api/me/` não tem contagem |
| 5 | Confirmação de remover/arquivar/sair | `window.confirm` nativo; não há frame de confirmação |
| 6 | Foco no `<dialog>` | O nativo passa pela UI do navegador antes de voltar; ciclo estrito exigiria laço em JS |
| 7 | Nomes longos de casa | Quebram no meio da palavra no mobile |
| 8 | Membro sem nome | Aparece pelo e-mail; não há como definir nome fora do Google |

## Diferenças visuais (CA18)

Comparação de `web/e2e/__screens__/` com 10/D04 e 11/M05 em 390×844 e 1440×900. Composição, componentes, cores, fontes e espaçamentos correspondem, com estas diferenças:

- **Esperadas pela spec (decisão 4):** casas com "Sem contas ainda" e sem barra; MemberRow só com o papel (sem "Paga N contas", "modo simples", "Só acompanha"); sem "Contas que se repetem", "+ Nova recorrente", "Ver todas"; sem "Configurações" (botão em D04, ícone em 10); sem "Gerenciar papéis"; cabeçalho sem "N contas que se repetem"; dados reais no lugar de "Família Martins".
  - _Nota de 15/11/2026:_ na Etapa 04 o dono decidiu (Q10) que "Configurações" volta no D04 (e no ícone do 10), só para admin, com "Avisar N dias antes" (1–7, RN13). Isso substitui só a parte da decisão 4 que mandava esconder "Configurações". Ver [spec da Etapa 04](../04-contas/spec.md#decisões-resolvidas-ok-do-dono-15112026).
- **Acréscimos sem frame:** "Convites pendentes" abaixo de Membros (só admin, só quando há); "Sair do grupo" (Q3).
- **Listadas por QA e frontend:** fundo da folha translúcido (`--scrim-sheet`) em vez do sólido do frame 11; detalhe do seletor `Grupo · <papel>`; confirmações por `window.confirm`; nomes longos de casa quebrando no mobile; membros sem nome exibidos pelo e-mail. Detalhes em [decisões](#decisões-para-o-dono-confirmar).

Frames lidos em HTML e screenshot (10 e 11 draft; D04 e M05 `ready_for_dev`). Canvas não alterado.

## Dados de desenvolvimento

Testes manuais deixaram no banco de dev 3 grupos "Teste UI …", contas `ui-*@varal.test` e o grupo `x` (`eae65caf-c92c-4233-b9f4-27fdfdcff677`, criado pela revisão de segurança ao reproduzir o B1). Não há rota para apagar grupo; o dono pode limpar pelo shell do Django ou recriar o volume.

## Ajustes aplicados

Nenhum item novo. "Varal — Ajustes" relido ao vivo no fim (rev 24). O item "Variáveis do Google" foi marcado no documento remoto como feito na etapa 02, no início desta etapa.

## Ajustes pendentes e limites

- Nenhum ajuste pendente.
- **P5 (nova, não bloqueia):** limite de cadastro configurável só no E2E/CI.
- **P3 / Etapa 11:** limite por IP (aceite de convite e M6) depois dos proxies confiáveis.
- **P4 / Etapa 11:** agora inclui omitir o token de convite do access log de produção.
- **M4** registrado; **M5** vai para o endpoint de exclusão e a exportação da Etapa 11.
