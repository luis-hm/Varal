# Diagnóstico — Google403 e callback OAuth

> **Contém:** reprodução de COR-12, comparação controlada da política de referrer e próximos testes de correção.
> **Origem:** captura do dono em17/11/2026, navegador anônimo próprio em HMG, matriz HTTP e middleware Django com valores fictícios. Não implementa nem implanta correção.

## Resultado confirmado

Dois bloqueios em sequência: o formulário Google é rejeitado pelo CSRF do Varal; removido esse impedimento apenas no DOM de teste, o Google rejeita a URI de retorno. A aplicação e o cliente OAuth continuam sem alterações.

| Prova | Resultado | Artefato |
| --- | --- | --- |
| Botão real, página/política originais |403; cookie CSRF presente, campo igual ao cookie, `Origin: null`, nenhum `Referer`. | [Browser baseline](browser-baseline.json), [detalhes](browser-baseline-detailed.json) |
| Novo contexto anônimo; somente meta referrer local `strict-origin` | Origem HMG/Referer presente;403 deixa de ocorrer; página Google mostra `redirect_uri_mismatch`. | [Browser contrafactual](browser-counterfactual.json), [detalhes](browser-counterfactual-detailed.json) |
| HTTP com cookie/campo corretos, variando apenas origem/referência |null/sem referência403; origem própria302; ambos ausentes403; referência própria semOrigin302. Redirecionamentos não seguidos. | [Matriz HTTP](http-matrix.json) |
| `CsrfViewMiddleware` isolado, sem banco/rede |9/9 asserts passaram, incluindo nulo/alheio, rotação/ausência do cookie e precedência campo/header. | [Resultado](csrf-offline.json), [probe](probe_csrf_offline.py) |

O header da entrada apareceu duas vezes como `no-referrer`, consistente com Next e edge. O formulário contém um único campo CSRF preenchido. Esses valores foram comparados em memória; os artefatos guardam somente presença/igualdade, nunca valores dos cookies ou tokens.

No browser, o status intermediário após a navegação ao Google não ficou disponível no observador. Não atribuir a ele o302 que foi medido separadamente por HTTP. O contrafactual passar significa **início OAuth liberado**, não login completo: a etapa seguinte ainda falhou no provedor.

## Explicação e correções a planejar

1. `form.submit()` é navegação POST nativa. Sob `no-referrer`, esse pedido leva origem opaca (`null`). Django rejeita a origem antes de conferir o token. O botão de senha usa `fetch`, por outro caminho. [Fetch — Origin](https://fetch.spec.whatwg.org/#append-a-request-origin-header), [Django — retirar Referer](https://docs.djangoproject.com/en/6.1/ref/csrf/#removing-the-referer-header).
2. Proposta: política efetiva `strict-origin` apenas nas páginas de entrada/cadastro, consistente entre [Next](../../../../web/next.config.ts) e [edge](../../../../infra/deploy/edge.conf.template). Preservar `no-referrer` em retorno/ticket/convites/confirmações e impedir vazamento de caminho/query. Não aceitar `Origin: null`, não isentar endpoint e não desligar CSRF.
3. No cliente OAuth efetivamente usado pela HMG, cadastrar exatamente `https://hmgvaral.codehub.systems/accounts/google/login/callback/` como URI autorizada. Conferir Client ID e eventual configuração da origem pública, sem trocar a URI local indiscriminadamente. O Console não foi inspecionado; a rejeição foi observada na página anônima do Google. [Google — correspondência da URI](https://developers.google.com/identity/protocols/oauth2/web-server#uri-mismatch).

## Reprodução

Requer `agent-browser` já instalado e seu conteúdo `skills get core` lido. Se o comando não estiver no PATH, definir `AGENT_BROWSER_JS` para o entrypoint JS de uma instalação existente; o script não instala dependências.

```bash
python docs/produto/evidencias/google-csrf-2026-11-17/reproduce_browser.py --allow-hmg --assert-google-start
# Baseline observado: exit1,403, Origin:null; capta o defeito atual.

python docs/produto/evidencias/google-csrf-2026-11-17/reproduce_browser.py --allow-hmg --policy strict-origin --assert-google-start
# Contrafactual observado: exit0 somente para início OAuth;
# Google ainda mostra redirect_uri_mismatch. Não autentica conta.

python docs/produto/evidencias/google-csrf-2026-11-17/probe_http_matrix.py --allow-hmg
# Matriz de protocolo: mantém origem nula como NEGATIVO403.

api/.venv/bin/python docs/produto/evidencias/google-csrf-2026-11-17/probe_csrf_offline.py
# Sem banco/rede;9 asserts.
```

As reproduções originais foram executadas nos mesmos probes em pastas privadas `/tmp`; a cópia de navegador aqui adapta somente localização do CLI/pasta de saída e exige opt-in explícito para HMG. Sessões são novas/anônimas e encerradas no `finally`. As chamadas de início podem gerar estado OAuth/sessão anônima normal no servidor. Não criam usuário, não entram em conta Google e não usam produção. Resultados do navegador vão para uma pasta privada `/tmp/varal-google-csrf-*` e stdout sanitizado.

O baseline é um sinal vermelho intencional, não teste aprovado da correção. O probe HTTP é diagnóstico positivo/negativo do middleware, não uma expectativa de que o servidor passe a aceitar origem nula. Depois da implementação, o **clique original**, sem override no DOM, deverá iniciar o OAuth com origem própria; todos os negativos CSRF devem continuar recusados.

## Lacunas e aceite posterior

Backend atual fornece Origin correto manualmente nos testes; frontend/E2E cobrem principalmente Google indisponível. Falta teste do botão com provedor configurado e headers reais produtivos. Acrescentar regressão em390×844/1440×900 para entrada/cadastro, localhost/HMG aplicáveis, rotação/ausência do token, origem alheia/nula, cancelamento, retorno/ticket e vínculo de identidade.

Não houve login Google completo, consentimento de conta real, troca real do código por tokens ou prova da sessão final. Depois de corrigir política e registro OAuth, essa validação permanece necessária com autorização apropriada. Nenhum código da aplicação, configuração remota, deploy ou critério de aceite foi alterado/encerrado nesta análise.

Os artefatos públicos excluem cookies, CSRF/OAuthstate, segredos e queries de autorização. O envelope bruto do CLI não é evidência pública: pode conter URL completa do provedor. Os scripts descartam esse envelope e persistem apenas campos permitidos.
