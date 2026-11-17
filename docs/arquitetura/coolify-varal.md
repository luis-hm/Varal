# Varal no Coolify — homologação e produção

> **Contém:** recursos, branches, deploy por GitHub Actions, isolamento e pendências da primeira implantação.
> **Origem:** pedido explícito do dono em 16/11/2026 para criar `develop`, configurar os dois ambientes e iniciar somente HMG; estado operacional atualizado durante a execução.

## Escopo autorizado e estado

Projeto Coolify **Varal**, UUID `03o0jp5xl2fdlidxrkox9brb`, na VPS existente. A branch `develop` foi criada via `gh api` a partir da `main` `7eb3e567322c2c53ab466609d6b3896f0d890cb9`. O dono confirmou os dois domínios abaixo. O pedido de HMG não encerra os aceites pendentes da etapa11 e não autoriza iniciar produção.

| Ambiente | Recurso | Branch | Domínio | Estado neste checkpoint |
| --- | --- | --- | --- | --- |
| HMG | `hmgvaral` / `kb87a4pykru44pez1jzre6ru` | `develop` | `https://hmgvaral.codehub.systems` | Configuração criada; primeira implantação e smoke pendentes. |
| Produção | `varal` / `gjixenxlbkz1wbvuoimyl8lu` | `main` | `https://varal.codehub.systems` | Preparado e parado; não implantar agora. |

Ambientes Coolify: `hmg` (`csynpigwvzzsmsgs8ox1muns`) e `production` (`pdc5smdh3nbvwlefqazbhw1e`). Destino Docker `coolify` / `gwp0cxywjlral4fgms3lygoo`, servidor `bg4nlylaxjqyw9izakbwaqfy`. O Silo existente permanece no projeto de armazenamento, sem recriação ou reinício para esta implantação.

## Fonte Git e construção

- Aplicações de repositório público `luis-hm/Varal`, build pack Docker Compose, sem vínculo a GitHub App nem webhook direto de push.
- Base Directory: `/infra/deploy`; Docker Compose Location: `/compose.coolify.yml`. Contexto de build `../..` corresponde à raiz do repositório.
- Arquivo: [compose.coolify.yml](../../infra/deploy/compose.coolify.yml). Imagens próprias para Gunicorn, Next produtivo, proxies, PostgreSQL, journal/WAL e inicialização; não usar os Dockerfiles de desenvolvimento.
- **Raw Compose obrigatório:** `is_raw_compose_deployment_enabled=true`. No modo normal, o Coolify pode injetar `.env` em todos os serviços e anular a separação de credenciais. Conferir o Compose efetivo antes da implantação.
- Build serial por aplicação: `docker_compose_custom_build_command=docker compose --parallel 1 build`. Não mudar limites globais ou configurações de outros aplicativos.
- Variáveis secretas somente runtime; Dockerfiles possuem listas restritas de inclusão no contexto. Manter varredura de imagens habilitada.

O Compose mantém bancos/Redis/journal internos, API sem porta pública e somente o edge na rede externa `coolify`. Traefik termina TLS e encaminha à porta interna8080. Routers próprios têm access logs e tracing desativados para não registrar tokens/URLs. O edge recebe o IP original somente do IP exato do Traefik e sobrescreve cabeçalhos antes de chegar à API. SSR usa proxy separado com três GETs autorizados, preservando a regra da11.

As redes HMG são application `172.30.210.0/24` e frontend `172.30.212.0/24`; produção usa211 e213. O inventário enviado pelo dono listou as redes existentes em `10.0.0.0/24` a `10.0.9.0/24` e IPv6 `fdcb:6a54:1776::/64`, sem sobreposição com essas subnets. O Docker também deve abortar na criação se surgir conflito, sem remover redes existentes.

`COOLIFY_PROXY_TRUST=coolify-proxy` permite ao Nginx resolver o endereço exato do Traefik pelo DNS Docker ao iniciar, sem confiar em toda a rede compartilhada. Aceitar somente esse hostname literal ou um IP numérico `/32`/`/128`; sem resolução, a inicialização falha. O edge precisa ser recarregado após recriação/mudança de IP do proxy. [Suporte oficial a hostname](https://nginx.org/en/docs/http/ngx_http_realip_module.html#set_real_ip_from).

Essa alternativa foi revisada quanto à segurança. Posteriormente, a inspeção enviada pelo dono confirmou o proxy em `10.0.1.3`/`fdcb:6a54:1776::3` na rede `coolify`, com o nome DNS `coolify-proxy`. Nenhum helper com Docker socket foi instalado; sua criação foi rejeitada pela revisão automática e abandonada.

## Deploy por push

| Workflow | Disparo | Condições |
| --- | --- | --- |
| [deploy-hmg.yml](../../.github/workflows/deploy-hmg.yml) | Push na `develop` ou execução manual nessa branch | CI API/web reutilizado e aprovado; testes do assinador; HEAD ainda corresponde ao commit testado. |
| [deploy-prod.yml](../../.github/workflows/deploy-prod.yml) | Push na `main` ou execução manual nessa branch | Todos os jobs bloqueados enquanto `VARAL_PROD_DEPLOY_ENABLED` não for `true`; mesmos gates de HMG após habilitação futura. |

As workflows `api.yml` e `web.yml` preservam seus testes e também aceitam `workflow_call`. Os disparos diretos já existentes podem gerar verificações duplicadas; não foram retirados para implantar HMG. Uma falha do CI não autoriza afrouxar testes nem chamar a homologação de integralmente aprovada.

O [assinador](../../.github/scripts/deploy-coolify.py) envia um payload GitHub mínimo com `ref`, `repository.full_name` e `after` (SHA testado) para `/webhooks/source/github/events/manual`. Usa HMAC-SHA256 e segredo exclusivo por recurso, sem token administrativo do Coolify no Actions. Não há retry automático de POST ambíguo. O receptor verifica repo/branch/assinatura e enfileira o SHA explícito. [Controller oficial](https://github.com/coollabsio/coolify/blob/v4.x/app/Http/Controllers/Webhook/Github.php).

**Workflow verde prova enfileiramento, não disponibilidade do aplicativo.** Conferir deploy UUID, commit efetivo e smoke HTTPS no Coolify após o disparo. O script não apresenta uma resposta de saúde da versão anterior como prova da versão nova.

Configuração GitHub aplicada:

| Tipo | Nome | Conteúdo não secreto / finalidade |
| --- | --- | --- |
| Variável do repositório | `COOLIFY_URL` | `https://painel.codehub.systems` |
| Variável do repositório | `COOLIFY_HMG_UUID` | `kb87a4pykru44pez1jzre6ru` |
| Variável do repositório | `COOLIFY_PROD_UUID` | `gjixenxlbkz1wbvuoimyl8lu` |
| Variável do repositório | `VARAL_PROD_DEPLOY_ENABLED` | **`false`** |
| Secret do ambiente GitHub `hmg` | `COOLIFY_HMG_WEBHOOK_SECRET` | Segredo HMAC exclusivo de HMG. |
| Secret do ambiente GitHub `production` | `COOLIFY_PROD_WEBHOOK_SECRET` | Segredo HMAC exclusivo de produção. |

No Coolify, cada aplicação tem seu `manual_webhook_secret_github`. HMG tem `is_auto_deploy_enabled=true` para aceitar somente a chamada manual assinada; não cadastrar um webhook direto de push que contorne o CI. Produção mantém **auto-deploy falso**, previews desativados e nenhuma implantação inicial. No futuro, ativar produção exige decisão do dono e alterar tanto a variável GitHub quanto o auto-deploy desse recurso. Não tratar merge/push na `main` como autorização implícita para remover essas travas.

## Persistência, chaves e arquivos

HMG tem banco, senhas de admin/migrador/runtime, Redis, spool, epoch e volumes próprios, prefixados `hmgvaral-`. Produção terá prefixo `varal-` e segredos diferentes. Bootstrap gera chaves em volumes separados, sela a identidade inicial e falha diante de inicialização parcial ou perda inconsistente de volumes. Não copiar chaves/fixtures/dumps do laboratório, não reinicializar volumes perdidos para fazer o serviço parecer saudável.

Runtime recebe apenas as capacidades necessárias; migração roda por role separada e uma trava de migração. PostgreSQL preserva arquivamento WAL e journal permanece habilitado. Redis usa persistência e limite de memória sem expulsão silenciosa de chaves. Esses mecanismos não substituem backup/recovery testado do novo conjunto.

| Armazenamento | Bucket | Credencial |
| --- | --- | --- |
| HMG | `varal-hmg-arquivos` | Nova chave limitada a esse bucket; PUT/GET/DELETE sintético passou, ACL e bucket de produção negados403. |
| Produção | `varal-arquivos` | Chave restrita de produção já existente, sem administração Silo. |

Ambos usam `https://arquivos.codehub.systems`, porém não compartilham bucket/credencial. Bucket HMG foi pré-provisionado como privado com administração fora do runtime. Não executar `preparar_storage` administrativo com chave restrita durante startup. Não tornar objetos públicos para resolver erro de download.

Inventário privado em `infra/.env`: `VARAL_HMG_*` e `VARAL_PROD_*`, além do inventário Silo anterior. Esses nomes não mudam o ambiente local automaticamente. Não enviar `API_KEY_GOOGLE`, chave de outro provedor de IA ou `COOLIFY_TOKEN` para os containers do Varal. Não publicar segredos, arquivo `.env`, respostas administrativas brutas ou URLs assinadas no Git/Actions/documentação.

## Primeiro acesso e serviços externos

Criar o primeiro usuário pelo cadastro normal da interface após HMG saudável; não executar `seed`, que recusa `DEBUG=0`. Não criar dados de demonstração ou senha pública no ambiente remoto.

Google OAuth usa as credenciais privadas existentes, mas o Console Google precisa autorizar a origem `https://hmgvaral.codehub.systems` e o callback **`https://hmgvaral.codehub.systems/accounts/google/login/callback/`**. O callback de desenvolvimento localhost permanece separado. Produção terá sua própria origem/callback quando autorizada. Não declarar login Google real validado só porque as variáveis foram preenchidas.

Não havia configuração SMTP no inventário local. HMG inicia com backend SMTP apontando para conexão indisponível, timeout curto e falha controlada; **e-mails não serão entregues** até configurar um servidor real. Não usar backend console (vaza corpos/códigos) nem dummy (retorna sucesso sem entrega). Push permanece desativado até configurar VAPID/entrega. Essas limitações afetam os testes de recuperação e reautenticação por e-mail, avisos e push.

## Verificações e operação

Antes da primeira implantação: Compose parse sem erro, Dockerfiles/contextos sem segredos, inicialização idempotente e falha em estado parcial, Nginx válido, rede sem colisão, confiança do proxy exata, Raw Compose/segregação de envs, produção parada/gate falso.

Depois de HMG implantado: confirmar SHA e status no Coolify, TLS válido, `/entrar`, health e readiness; cadastrar conta sintética, validar sessão/SSR/CSRF, arquivo sintético e URL privada; testar cabeçalhos forjados sem alterar a origem efetiva. Evitar cadastrar o dono automaticamente ou autenticar uma conta Google pessoal sem sua participação.

```sh
curl --fail --show-error https://hmgvaral.codehub.systems/api/health/
curl --fail --show-error https://hmgvaral.codehub.systems/api/ready/
curl --fail --show-error --output /dev/null https://hmgvaral.codehub.systems/entrar
gh run list --repo luis-hm/Varal --branch develop
```

Falha de implantação: consultar logs restritos no Coolify sem copiar dados de requisições. Voltar ao commit/imagem conhecido preservando banco/volumes; migrations podem exigir plano próprio de compatibilidade. Não usar `down -v`, prune de volumes ou limpar bucket/banco para corrigir configuração. Não reiniciar proxy global ou serviços de outros projetos.

Backup local do Silo já existente inclui o volume do Silo; isso não comprova recuperação de PostgreSQL/journal/WAL desta stack. O conjunto novo precisa de backup consistente, retenção e ensaio de recuperação próprios. VPS e disco continuam únicos. HMG não é aprovação de RNF05/CA13, CA16/18, resiliência ou implantação final de produção.
