# Plano — Etapa 02 (Autenticação)

> **Contém:** sequência técnica, contratos propostos, migrações, validação e riscos da Etapa 02.
> **Origem:** [spec.md](spec.md), [stack](../../arquitetura/stack.md), [modelo](../../dados/modelo.md), [API](../../api/README.md) e documentação oficial do django-allauth consultada em 13/11/2026.

## Execução

Preparação concluída quando os três documentos estiverem revisáveis. **Código só após o ok** do passo 4 do comando `/etapa`, incluindo as decisões visuais da spec.

| Ordem / agente | Responsabilidade |
| --- | --- |
| varal-boletos | Não se aplica |
| varal-backend | Verificar compatibilidade, instalar allauth, modelos/migrações, adapters, sessão, recuperação assíncrona, dados próprios, schema e testes |
| `make types` | Validar contrato composto e gerar tipos antes de integrar o frontend |
| varal-frontend | Ler novamente os dois frames/componentes; formulários, guarda de sessão, shell com dados próprios e saída; testes |
| varal-devops | Variáveis Google/e-mail, geração e CI de tipos, ambiente de E2E com API real |
| varal-qa | Critérios da spec, E2E e comparação visual nas duas resoluções |
| varal-seguranca | Revisão somente leitura de sessão, CSRF, redirecionamentos, recuperação, vínculo Google e isolamento |
| varal-docs | Relatório, progresso, matriz e docs de API/stack/design pertinentes |

## Backend e migrações

1. Conferir a versão efetiva de Django/DRF nos arquivos de lock; escolher e fixar uma versão compatível de `django-allauth` com extras necessários para headless, Google e schema. Conferir rotas/payloads no schema da versão instalada antes de escrever clientes.
2. Manter `AUTH_USER_MODEL`, UUID e usuários existentes. Acrescentar `nome`, `telefone`, `prefs_notificacao` com defaults compatíveis; autenticação por e-mail, sem exigir username na interface. Preservar o username legado, preenchido internamente com valor único pelo allauth, e a compatibilidade do seed (`username="dev"`)/admin. Não desabilitar o campo na configuração sem tratar sua restrição. Testar dois cadastros distintos, usuários migrados e repetição do seed.
3. Criar `Espaco` com UUID e campos do modelo pertinentes ao espaço pessoal. Restrição no banco garante um espaço pessoal por dono. Provisionamento atômico e idempotente nos cadastros e-mail/Google; migração de dados cria espaços para usuários anteriores. Sem modelo/API de membros nesta etapa.
4. Configurar allauth headless browser com sessão Django e CSRF, incluindo rotas do provedor em `/accounts/`. O cadastro abre sessão sem exigir etapa adicional de confirmação de e-mail que não foi pedida; não habilitar vínculo automático inseguro por coincidência de e-mail.
5. Recuperação por link allauth; envio por Celery com backend de e-mail configurável. Usar backend em memória nos testes e saída local de desenvolvimento, sem exigir serviço SMTP para rodar a suíte.

## Contratos propostos

Montar as URLs nativas headless em `/api/auth/`. O sufixo da biblioteca é preservado, **sem barra final**; essa exceção à convenção DRF será documentada em `docs/api/README.md`. Os endpoints próprios continuam com barra. Rotas e payloads abaixo devem ser conferidos contra a versão fixada. Cookies e CSRF se aplicam ao cliente browser. [API oficial](https://docs.allauth.org/en/latest/headless/openapi-specification/).

| Método e caminho após `/api/auth/browser/v1/` | Uso / entrada |
| --- | --- |
| `GET config` | Configuração pública e provedores disponíveis |
| `POST auth/signup` | Cadastro: `email`, `password` |
| `POST auth/login` | Entrada: `email`, `password` |
| `GET auth/session` | Estado da sessão |
| `DELETE auth/session` | Saída; 401 ao terminar é resposta esperada |
| `POST auth/password/request` | Solicitação: `email` |
| `GET auth/password/reset` | Validar link pelo header `X-Password-Reset-Key` |
| `POST auth/password/reset` | Trocar senha: `key`, `password` |
| `POST auth/provider/redirect` | Formulário síncrono: `provider=google`, `process=login`, `callback_url` do frontend |

`GET /api/me/`: rota própria DRF autenticada, retorna `id`, `nome`, `email` e `espaco_pessoal: {id, tipo, nome}` do solicitante. Nenhum seletor de usuário/dono aceito do navegador. Campos privados e preferências fora dessa resposta mínima.

## Google, frontend e proxy

- `SOCIALACCOUNT_PROVIDERS["google"]` lê as duas variáveis do ambiente; `infra/.env.example` tem ambas vazias. Não cadastrar `SocialApp` com as mesmas credenciais.
- Retorno OAuth **preservado**: `http://localhost:8000/accounts/google/login/callback/`; origem Google: `http://localhost:3000`. Iniciar o handshake pela API no backend para manter esse host no `redirect_uri`; conferir o redirecionamento real em teste antes de integrar o botão. O `callback_url` headless volta para `http://localhost:3000/entrar/retorno/`, onde a interface consulta a sessão. [Provedor Google](https://docs.allauth.org/en/latest/socialaccount/providers/google.html).
- Proposta de rotas Next: `/entrar`, `/criar-conta`, `/recuperar-senha`, `/recuperar-senha/[key]`, `/entrar/retorno`, todas no mesmo layout e com estados aprovados. `/` e demais páginas do app verificam a sessão no servidor; redirecionamentos só para caminhos locais permitidos.
- Acrescentar rewrite específico de `/api/auth/:path*` preservando o sufixo sem barra, método/body do POST e cookies/`Set-Cookie`; manter `/api/*/` para DRF. Encaminhar cookies na verificação pelo servidor, sem cache compartilhado de dados autenticados. Tratar rotação do CSRF após login.
- Usar tipos gerados em um cliente de autenticação comum. Sem tokens no localStorage. O shell recebe usuário/espaço de `/api/me/`; navegação e placeholders da Etapa 01 continuam, com acesso autenticado nos testes existentes.
- Reutilizar os componentes da Etapa 01; reler HTML e screenshots antes de implementar. Aplicar a decisão de movimento e os estados do formulário somente depois do ok.

## OpenAPI e tipos

O schema do allauth é próprio; drf-spectacular não o incorpora automaticamente. A biblioteca permite servir seu schema dinâmico, com o extra `headless-spec`. [Configuração oficial](https://docs.allauth.org/en/latest/headless/configuration.html).

Proposta: comando de exportação que obtém o schema DRF e o schema renderizado pelo allauth no contexto Django, sem depender de servidor HTTP em execução; compõe ambos em `api/openapi.yaml`. Preservar caminhos montados, prefixar componentes da biblioteca e ajustar suas referências para evitar colisões; alinhar versão OpenAPI suportada pelos dois geradores. Validar o resultado e falhar se houver caminho/componente duplicado ou referência não resolvida. `make types` e CI usam o mesmo comando; `web/src/types/api.ts` segue gerado desse arquivo único. Testar que schema composto inclui login, recuperação, sessão, Google e `/api/me/` e que duas gerações são idênticas. Confirmar a interface de renderização da versão instalada na primeira tarefa; se incompatível, revisar o plano antes de criar contrato manual.

## Validação e riscos

- Testes pytest exercitam endpoints reais allauth, banco, migração, CSRF, Celery/e-mail e falhas de OAuth com respostas externas controladas. Não dependem do Google ou SMTP reais.
- E2E de cadastro, login, recarga e saída usa API/PostgreSQL reais. Testes de apresentação podem simular respostas; isso não substitui a integração. Adaptar fixtures da vitrine e CI à guarda de autenticação. Recuperação é coberta por integração backend e estados do formulário.
- Validar Google real se houver credenciais; registrar separadamente o que foi comprovado por simulação e o que foi verificado com o provedor. Credenciais ausentes não justificam declarar OAuth real validado.
- A spec lista as pendências comprovadas: estados de cadastro/recuperação sem frame próprio, frames draft e divergência de movimento. Não alterar o canvas para resolvê-las.
- No fim, rever os ajustes na fonte disponível, sem alegar marcação remota; atualizar a matriz RF01–RF03/RNF02/RNF12 com testes reais e registrar quaisquer limitações no relatório.
