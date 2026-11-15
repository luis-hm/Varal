# Relatório — Etapa 02 (Autenticação)

> **Contém:** entregas, evidências, decisões, ajustes e validações finais da Etapa 02.
> **Origem:** implementação na branch `etapa/02-autenticacao`, testes/revisões da equipe e anexo de ajustes do dono, relido em 13/11/2026.

**Estado: concluída em 13/11/2026.** Sem push; a Etapa 03 só começa com novo `/etapa`.

## Entregas

- **RF01 / CU01:** cadastro e login e-mail/senha ou Google com allauth 65.22.0. E-mail normalizado e único sem distinguir maiúsculas; username permanece interno, compatível com seed/admin. Sem vínculo automático entre Google e conta local por coincidência de e-mail.
- **RF02 / RN03:** `Usuario.save()` provisiona espaço pessoal na mesma transação; restrições exigem dono e um único pessoal por usuário. Migração preserva UUID/senha dos usuários anteriores e provisiona espaços; seed repetido não duplica. Não há membros nem endpoints de grupo nesta etapa.
- **RF03:** recuperação por link de uso único/validade limitada, resposta pública genérica, envio de e-mail por Celery após commit; nova senha exige login novamente.
- **Sessão:** cookies HttpOnly/SameSite=Lax, Secure/HTTPS fora de DEBUG, CSRF efetivo e rotacionado no login. `/api/me/` retorna somente usuário e espaço próprios, sem cache compartilhado. Saída invalida a sessão e limpa o estado da interface.
- **Frontend:** `/entrar`, `/criar-conta`, `/recuperar-senha`, `/recuperar-senha/[key]` e `/entrar/retorno`, no layout responsivo dos frames 01 ↔ D01. Shell autenticado com dados reais; Perfil continua “Em breve” com “Sair da conta”.
- O segmento protegido aguarda a sessão real (`instant=false` com Suspense), evitando validação de prefetch anônimo; nome/e-mail longos são truncados no SideNav para preservar o layout.
- **RNF12:** OpenAPI único DRF + allauth, componentes/referências com prefixo `Allauth`, validação e exportação determinística por `export_schema`. Proxy preserva endpoints nativos sem barra e cookies/POST. Tipos gerados, sem contratos de API escritos à mão.
- **Infra/CI:** cache Redis para limites compartilhados, e-mails locais nos logs do worker, `make e2e` com API/PostgreSQL/worker reais; workflow web também reage a mudanças na API. CI remoto não executado: repositório sem remoto.

## Critérios e evidências

| CA | Evidência implementada |
| --- | --- |
| CA01–CA03 | `api/tests/test_autenticacao.py`: cadastro de dois usuários, dados inválidos, duplicação/case, hash, login, senha errada e inativo; `web/e2e/auth.spec.ts` com API real |
| CA04–CA05 | Testes RN03 de restrições/rollback/seed e `api/tests/test_migracao_autenticacao.py` |
| CA06 | Callback allauth exercitado com HTTP externo simulado: Google novo/recorrente, colisão local, cancelamento e state inválido |
| CA07–CA08 | Testes de tarefa/e-mail genérico e tokens válidos, inválidos, expirados e reutilizados; Vitest dos estados de recuperação, incluindo sucesso após consumo da chave; E2E da solicitação e link inválido; troca real de senha e novo login conferidos no build final |
| CA09–CA11 | Invalidação de sessão antiga, isolamento entre usuários, CSRF/origem/rotação, cookies/configuração de produção, rate limit e URLs de retorno malformadas; E2E de recarga/Voltar/saída |
| CA12 | Testes sem credenciais/sem admin, PKCE e callback fixo; retorno acessível sem Google configurado; início real no provedor conferido |
| CA13–CA14 | Comparação com HTML/screenshots do Doop nas duas resoluções; E2E 360px/alvos ≥44px/reduced motion; mensagens e erros associados nos testes Vitest |
| CA15 | Schema composto validado; teste de determinismo e regeneração final de OpenAPI/tipos com hashes idênticos |
| CA16 | Testes, lint, tipos, E2E integral, segurança, build e smoke de produção concluídos |

| Verificação final | Resultado |
| --- | --- |
| `make e2e` | **38/38 passaram**, nos projetos 390×844 e 1440×900, com API/PostgreSQL reais |
| `make types` | **Passou**; hashes de `api/openapi.yaml` e `web/src/types/api.ts` idênticos antes/depois |
| Revisão de segurança | **Sem bloqueantes**, incluindo revisão da correção de callback malformado |
| `make test` | **31/31 API e 39/39 Vitest passaram**; Vitest repetido após os ajustes finais, também 39/39 |
| `make lint` | **Passou**: ruff (39 arquivos), ESLint, Next typegen e TypeScript |
| Build de produção Next | **Passou**: compilação, TypeScript e 14 páginas |
| Smoke após patches finais, em produção | **4/4 passaram**, nas duas resoluções: fluxo autenticado completo e screenshots/360px/reduced motion; sem erros instant/hydration nos logs |
| Regressão HTTP 404 em produção | **2/2 passaram** com sessão válida, após o mesmo teste falhar com HTTP 200 no build anterior; incluídos no CI após build/`next start` |
| Fluxo central após extração da guarda | **2/2 passaram** em produção, incluindo sessão/saída/Voltar |
| Vitrine em desenvolvimento | **12/12 passaram**, preservando guarda, fontes, layout, alvos, navegação e capturas |
| Inicialização dos formulários | **2/2 passaram** em desenvolvimento: HTML SSR desabilitado, controles habilitados após hidratação e fluxo original de cadastro/saída/Voltar/login; sem erros instant/hydration |
| Recuperação real no build final | **Passou** com conta descartável: token local válido, troca, chave consumida retornando 400 sem apagar confirmação e login com a nova senha. Sem envio de e-mail externo ou exposição do token |

## Segurança e correções

Uma URL Google malformada provocava `ValueError` e resposta 500. O problema foi reproduzido no endpoint real com três entradas; `AccountAdapter.is_safe_url()` agora rejeita a URL e volta ao frontend. Os mesmos três casos passaram após a correção. Segredos não entram no schema, configuração pública ou bundle; credenciais Google são exclusivamente do ambiente, inclusive quando existe `SocialApp` no banco.

A guarda em streaming fazia a vitrine mostrar a página 404 com HTTP 200 em produção. O teste autenticado reproduziu o erro nas duas resoluções. A vitrine manteve `/dev/componentes`, mas passou a decidir `notFound()` antes do `ProtectedShell` compartilhado; desenvolvimento continua autenticado. O mesmo teste passou com HTTP 404 e agora roda no CI em produção.

Após trocar a senha, remover a consulta da chave podia revalidá-la já consumida e substituir o sucesso por erro. A consulta e o estado de chave inválida agora respeitam a conclusão do fluxo. Um teste reproduziu essa troca indevida e passou após a correção; a conferência real confirmou a nova senha e o uso único da chave.

O teste de Voltar também reproduziu perda do primeiro campo preenchido antes da hidratação, sem chegar a enviar o login. Os controles agora só habilitam quando os handlers estão ativos, com `useSyncExternalStore`, sem alterar layout ou copy. O teste central verifica HTML SSR e navegador real. O opt-out `instant=false` das páginas protegidas segue a migração documentada do Next, sem cache compartilhado de sessão.

## Design e decisões aprovadas

O dono aprovou cadastro/recuperação como estados do mesmo layout e o movimento da folha conforme `varal-ui` (`translateY(100%)`, `0,5s`), em vez do trecho divergente do frame. Os frames 01 · Entrar (`GJDSPaQbio`) e D01 · Entrar (`7JTmWMAJup`) foram lidos em HTML/screenshots e permanecem `draft`; o canvas não foi alterado.

Comparação em 390×844 e 1440×900: composição, tipografia, cores, campos, raios e curva SVG do varal correspondem. Diferença deliberada: senha começa vazia com placeholder cinza; os bullets preenchidos do exemplo do Doop não são senha fictícia. Quatro medidas adicionais de tipografia do login ficam no bloco “fora do Doop” de `tokens.css`, documentadas em [tokens](../../design/tokens.md#fora-do-doop).

## Ajustes aplicados

Cópia local de conclusão do único item pendente do anexo, sem alterar seu texto:

- [x] Variáveis do Google (Etapa 02): usar GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET no .env da API (e no .env.example sem valores), lidas no SOCIALACCOUNT_PROVIDERS do allauth, nunca pelo admin nem no código. URL de retorno: http://localhost:8000/accounts/google/login/callback/; origem: http://localhost:3000. Se a URL mudar, me avisar no resumo da etapa antes de codar. — feito na etapa 02

O anexo fornecido pelo dono foi relido no fim. Não houve leitura ao vivo nem marcação do Claude Docs remoto: conector indisponível. O anexo original também não foi alterado. Retorno OAuth em 8000 e origem em 3000 preservados.

## Ajustes pendentes e limites

- Nenhum outro item desmarcado na cópia fornecida. A marcação no documento remoto permanece pendente de acesso.
  - *Nota de 14/11/2026:* o item foi marcado no documento remoto (" — feito na etapa 02") ao abrir a Etapa 03.
- Google real verificado até a tela oficial de entrada “continue to Varal”, sem autenticar conta externa. Cadastro/retorno completo do provedor foi testado com respostas HTTP simuladas; não foi declarado login externo completo.
- **P3 / Etapa 11:** configurar proxies confiáveis e testar spoofing antes do deploy. `trusted_proxy_count=0` preservado enquanto API 8000 estiver exposta; limite por IP vê o Next como origem. Não bloqueia esta etapa.
- **P1 / Etapa 06:** validação do armazenamento local permanece como antes.
- Avisos não bloqueantes: configurações `EMAIL_*` depreciadas pelo Django para 2028 e aviso Vite sobre carregamento futuro de configuração. Não afetaram as verificações já concluídas.
