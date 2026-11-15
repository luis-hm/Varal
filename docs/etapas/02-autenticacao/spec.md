# Spec — Etapa 02 (Autenticação)

> **Contém:** escopo, requisitos, ajustes, critérios de aceite e decisões pendentes da Etapa 02.
> **Origem:** [etapas](../README.md), [CU01](../../casos-de-uso/CU01-cadastrar-se-e-entrar.md), RF01–RF03, RN03, [modelo](../../dados/modelo.md), [design](../../design/README.md) e “Varal — Ajustes”, texto fornecido pelo dono em 13/11/2026 nesta conversa.

## Escopo

- Cadastro e login por e-mail/senha e Google com django-allauth headless; recuperação de senha por e-mail, consulta da sessão e saída.
- Um espaço pessoal por usuário, criado junto com o cadastro, sem membros (RN03). Preparar os usuários já existentes por migração de dados.
- Campos de domínio do usuário (`nome`, `telefone`, `prefs_notificacao`) e retorno dos dados próprios para o shell. Sem formulário de Perfil nesta etapa.
- Sessão Django por cookie, API acessada pela mesma origem via `/api`; páginas do app exigem sessão válida. Após autenticação, abrir `/`, ainda com o conteúdo “Em breve” da Etapa 01.
- Login nos dois tamanhos; propor cadastro e recuperação como estados do mesmo formulário, sujeitos ao ok abaixo.

| Requisito | Entrega nesta etapa |
| --- | --- |
| RF01 / CU01 | Cadastro e entrada por e-mail/senha ou Google; erros recuperáveis |
| RF02 / RN03 | Espaço pessoal único, automático, sem participação de terceiros |
| RF03 / CU01 | Solicitar e concluir troca de senha pelo link recebido |
| RNF01 / RNF02 | Dados próprios, hash de senha, sessão e CSRF; HTTPS e cookie Secure fora do desenvolvimento HTTP |
| RNF06 | Envio dos e-mails fora da requisição, por Celery |
| RNF08 / RNF09 | Formulários acessíveis a partir de 360px, botões 52px e alvos de 44px |
| RNF12 | Contrato OpenAPI incluindo autenticação, com tipos gerados |

## Fontes e ajuste incluído

O anexo “Texto colado.txt” desta conversa foi fornecido em resposta à indisponibilidade do conector Claude Docs. Esta preparação usa essa cópia; **não houve leitura ao vivo nem marcação do documento remoto**. O único item desmarcado é “Variáveis do Google (Etapa 02)”.

- `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` só no ambiente da API; entradas vazias em `infra/.env.example`.
- Carregar em `SOCIALACCOUNT_PROVIDERS`, sem credenciais em `SocialApp` no admin ou valores embutidos no código.
- Retorno OAuth cadastrado no Google: **`http://localhost:8000/accounts/google/login/callback/`**. Origem autorizada: **`http://localhost:3000`**. A proposta preserva ambos.
- O retorno final à interface (`callback_url` do fluxo headless) é diferente do retorno OAuth: aponta para a página de tratamento no frontend.

## Telas do Doop

Canvas `k0kB5dc-Vo`, confirmado por nome e lido em HTML e screenshot em 13/11/2026:

| Mobile | Desktop | Referência |
| --- | --- | --- |
| 01 · Entrar (`GJDSPaQbio`), 390×844 | D01 · Entrar (`7JTmWMAJup`), 1440×900 | Mobile: marca no topo e folha branca; desktop: duas metades, formulário de 400px |

Ambos estão como **draft**, sem atribuição de aprovação no Doop. O canvas permanece somente leitura. Reutilizar Field, Button, Icon, tokens e fontes; mesmas rotas e lógica com troca de layout em 1024px.

## Decisões para o resumo antes do código

**Aprovação em 13/11/2026:** o dono respondeu “ok” ao resumo, autorizando os estados do formulário, uso dos frames apresentados e a recomendação de movimento abaixo. O canvas permanece somente leitura; seu status remoto não foi alterado.

1. **Cadastro e recuperação:** os frames têm os links “Criar conta” e “Esqueci”, mas não têm os estados de destino. Proposta: reutilizar o mesmo layout, trocando título, campos e mensagens para cadastro, solicitação, nova senha e retorno do Google. Confirmar essa proposta no ok; não inventar frames nem alterar o Doop.
2. **Movimento:** a folha mobile no HTML do frame entra com `translateY(40px)` em `.6s`; o guia `varal-ui` define `sheet-up` de `translateY(100%)` em `.5s`. Recomendação para aprovação: seguir o guia (`100%`, `0,5s`). A escolha depende do ok do dono antes dessa implementação. As animações sempre respeitam movimento reduzido.
3. **Aprovação visual:** os dois frames continuam draft; o resumo deve explicitar esse estado antes da implementação.

## Critérios de aceite

Todos os testes abaixo são planejados; o relatório final registrará nomes e resultados reais.

| CA | Dado / Quando / Então | Verificação planejada |
| --- | --- | --- |
| CA01 | **Dado** e-mail novo e senha válida, **quando** cadastro, **então** recebo sessão autenticada, senha com hash e um espaço pessoal; o frontend abre o Início. Dois cadastros com e-mails distintos funcionam sem colisão de username interno. | pytest RF01/RF02; E2E com API real |
| CA02 | **Dado** e-mail inválido ou já usado, ou senha fraca, **quando** cadastro, **então** recebo orientação, posso entrar/recuperar e nenhum usuário ou espaço duplicado é criado. | pytest RF01; testes do formulário |
| CA03 | **Dado** usuário existente, **quando** entra com a senha certa, **então** a sessão persiste após recarregar; senha errada e usuário inativo não autenticam. | pytest RF01; E2E |
| CA04 | **Dado** cadastro por qualquer provedor e tentativas repetidas, **quando** o fluxo conclui, **então** existe exatamente um espaço pessoal daquele dono; falha na criação não deixa cadastro parcial. | pytest RN03, incluindo integridade no banco e rollback |
| CA05 | **Dado** usuário anterior a esta etapa, **quando** aplico migrações e executo o seed novamente, **então** ele mantém identidade/senha e tem somente um espaço pessoal. Não existe vínculo de membro nesse espaço. | pytest de migração e RN03 |
| CA06 | **Dado** Google configurado, **quando** autentico um perfil novo ou já vinculado, **então** cadastro/entro sem duplicar usuário ou espaço; cancelamento/falha volta com mensagem. Colisão com e-mail local não vincula contas automaticamente sem prova de identidade. | integração allauth com respostas externas simuladas; conferir fluxo real com credenciais disponíveis |
| CA07 | **Dado** e-mail cadastrado ou desconhecido, **quando** solicito recuperação, **então** a resposta pública é genérica; para o cadastrado, uma tarefa envia o link correto sem bloquear a requisição. | pytest RF03 com fila e backend de e-mail de teste |
| CA08 | **Dado** link de recuperação, **quando** envio nova senha, **então** token válido troca a senha; token expirado, inválido ou reutilizado não troca; senha antiga deixa de autenticar e nova funciona. | pytest RF03; testes dos estados do formulário |
| CA09 | **Dado** sessão válida, **quando** saio, **então** ela é invalidada e páginas protegidas voltam para Entrar; visitante anônimo não recebe dados privados. | pytest de sessão; E2E |
| CA10 | **Dado** dois usuários, **quando** consulto os dados próprios, **então** recebo apenas meu perfil público e meu espaço pessoal, sem hashes, tokens ou dados do outro usuário. | pytest RNF01/RN03 |
| CA11 | **Dado** fluxo browser, **quando** mutações chegam sem CSRF válido, **então** são bloqueadas; sessão usa cookie HttpOnly, SameSite adequado e Secure fora de DEBUG; senhas/tokens não vão ao armazenamento do navegador. | pytest com CSRF efetivo; E2E; revisão RNF02 |
| CA12 | **Dado** configuração Google, **quando** inicio o fluxo, **então** uso valores do ambiente e o retorno OAuth fixado acima; segredo não aparece em resposta/schema/bundle. Sem credenciais, o fluxo informa indisponibilidade sem erro 500. | pytest de configuração e redirecionamento; inspeção de bundle/configuração |
| CA13 | **Dado** tela Entrar nos dois tamanhos, **quando** comparo com os frames, **então** composição, campos, fontes, cores e espaçamentos correspondem; cadastro/recuperação seguem os estados aprovados. | Playwright 390×844 e 1440×900; comparação com Doop |
| CA14 | **Dado** teclado, leitor de tela, viewport 360px ou movimento reduzido, **quando** uso os formulários, **então** campos/erros têm nomes e associações, foco visível, mensagens anunciadas, alvos ≥44px, sem corte horizontal ou animação indevida. | Vitest + Playwright RNF08/RNF09 |
| CA15 | **Dado** contrato de autenticação e dados próprios, **quando** executo `make types`, **então** OpenAPI válido e tipos gerados cobrem as rotas usadas; regenerar não produz diff. | validação de schema e job types |
| CA16 | **Dado** a etapa implementada, **quando** encerro, **então** `make test`, `make lint` e E2E passam, há comparação visual nas duas resoluções, revisão de segurança sem bloqueantes e docs/rastreabilidade/ajustes revisados. | QA, segurança e relatório |

## Fora de escopo

Grupos, membros, convites e seu aceite (Etapa 03), lançamentos e tela real do Início (04), notificações de contas (09), Perfil/LGPD/PWA/deploy (11), MFA, senha por código e provedores além de Google. Não criar endpoints de membros nem aceitação fictícia de convite nesta etapa.
