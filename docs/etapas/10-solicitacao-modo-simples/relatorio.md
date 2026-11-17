# Relatório — Etapa 10 (concluída)

> **Contém:** entregas, resultados verificados, correções e limites do fechamento da etapa 10.
> **Origem:** ADR 0014, Q10-1–18/T10-A–E/D10-1–2, código integrado e pareceres dos responsáveis em 16/11/2026; resultados do runner integral da orquestração.

A etapa está na branch `etapa/10-solicitacao-modo-simples`, após a etapa 09 (`4e04ddf`) e seu merge local `56337ed`. **Concluída em 16/11/2026:** tipos determinísticos, testes integrais de API/web, lint e `make e2e` aprovados. Os 14 critérios de aceite estão encerrados com os lastros e limites abaixo. Commit e merge locais ainda serão registrados pela orquestração; nenhum hash é antecipado.

## Entregas

A solicitação parte de conta pessoal pendente do dono. Grupo e pagador precisam ser elegíveis no momento da reserva; o usuário confirma a audiência restrita e os campos compartilhados, inclusive o PDF inteiro e seus metadados. A cópia tem identidade própria no grupo, sem revelar referências ou dados exclusivos do pessoal. Opções identificam membros atuais por nome ou e-mail no contexto autorizado (Q04-23/Q10-15), sem reidentificar ex-membro no histórico. A mensagem opcional tem limite explícito de 500 caracteres, sem truncamento silencioso (Q10-18).

O contrato usa `nonce`, confirmação e hash `versao_compartilhamento`. O POST responde 202, inclusive sem PDF; preparação e pedido criado são estados distintos. Recuperação e abandono usam origem própria e nonce; o abandono pode criar tombstone antes de um POST tardio. Fechar não cancela uma reserva aceita. O frontend preserva o corpo confirmado em memória e apenas um marcador opaco por usuário/origem/nonce no armazenamento local.

O coordenador global curto entra antes das travas de domínio nas operações relacionadas e leituras da central. Pagar a cópia registra ambas as marcas atomicamente, com mesmo valor/data; a pessoal aparece como Sistema, sem comprovante replicado ou ator do grupo. Undo usa as marcas exatas e RN16/RN32; no pessoal exige também autorização na cópia. Pagar ou cancelar a original encerra preparação ou cancela a cópia aberta sem conceder leitura do grupo. Os dois eventos de pagamento são preservados; a comunicação da etapa 09 é deduplicada por causa e destinatário, sem reviver contexto revogado.

O PDF usa pin independente de CASCADE antes do 202, fonte imutável e destino novo por tentativa. A cópia verifica bytes, tamanho e SHA antes da publicação. Cleanup de PDF e comprovante usa intenção versionada, comparação da geração e mutex operacional, sem travas de domínio ou da linha de intenção durante S3. PUT ambíguo conserva tombstone para reconciliação; `total_max_attempts=1` impede retry oculto do SDK. A retenção incerta pode exigir revarredura contínua; não houve prova física de conclusão remota tardia de PUT.

O modo simples reutiliza a mesma API, ACL e pagamento da etapa 07. Mostra todas as abertas visíveis por vencimento e ID, contagens completas, valor a definir e aguardando conferência; ações dependem de recurso e permissão atuais. Pagas/confirmadas usam vencimento no mês civil de Fortaleza. Cabeçalho próprio mantém Grupos e logout. Saída reutiliza RF06/CU03/RN04/RN21/RN32. Título do card abre o detalhe existente (RF13/CU06/RF25), com retorno seguro ao grupo e recorte de pagas. Isso não concede casas (RF07) ou edição (RF12).

## Verificação integral

Runner único da orquestração: `/tmp/varal-qa10-runner.py`, estado `/tmp/varal-qa10-integral.json` e log `/tmp/varal-qa10-integral.log`, Node 22.23.5.

| Comando | Resultado verificado | Limite |
| --- | --- | --- |
| `make types`, duas vezes | Exit 0 em ambas; hashes de `api/openapi.yaml` e `web/src/types/api.ts` idênticos | Contrato determinístico; não substitui teste de comportamento |
| `make test` | Exit 0: **506 pytest e 127 Vitest em 33 arquivos** | API registrou 1.022 warnings; não são falhas |
| `make lint` | Exit 0: Ruff, formatação, ESLint e TypeScript; 119 arquivos Python já formatados | Checks estáticos aprovados |
| `make e2e` | Exit 0: **143 aprovados e 3 skips previstos, 146 casos, em 11,0 min**, nas duas larguras | Wrapper, build e Playwright aprovados nesta etapa; skips não são falhas nem provas executadas |

Runner 82968 terminou `passed`, com exit 0 em todas as etapas. O wrapper `make e2e` reconstruiu o ambiente e passou de fato; o bloqueio GHCR/MIME da etapa 09 não se repetiu. Os totais 483 API/111 web e Playwright 131 aprovados/3 skips pertencem ao fechamento da etapa 09. O total intermediário de 122 Vitest da etapa 10 antecede os últimos deltas e foi substituído pela integral atual de 127. Não somar focos ou rodadas dirigidas à integral.

## Evidências complementares

| Origem | Evidência | Limite |
| --- | --- | --- |
| Backend | Rodadas dirigidas: 127 solicitações/grupos; dois testes de undo projetado; 54 solicitações/pagamentos/recorrências; 46 solicitações/notificações; sete de cleanup de comprovante. Ruff e verificação de migrações passaram | Rodadas sobrepostas, sem soma; a integral API atual é 506 |
| Boletos | 106 regressões e, separadamente, sete de pin/cópia | Não somar à integral |
| Storage/fila reais isolados | Silo, Postgres, Redis e Celery confirmaram fonte pinada após CASCADE de usuário/origem/documento, fonte preservada por cleanup, cópia distinta por tarefa real, bytes/tamanho/SHA corretos, acesso anônimo negado e limpeza final | Dados sintéticos e recursos próprios removidos; não prova PUT físico tardio, LGPD completa ou produção |
| Segurança | Parecer integrado e delta final somente por leitura, sem bloqueantes após B10-pre1/B10-final1; conferidos autoria, identificação, saída e retorno | Não equivale a execução de testes ou aprovação visual |
| Decisor | Q10-15–18 e D10-1–2 auditadas, sem perguntas novas ou bloqueantes de autorização | Decisões delegadas; não alegar resposta literal ou aprovação do canvas |
| QA visual | Capturas do pedido topo/fundo e modo simples em 390×844 e 1440×900 comparadas com 12/M06 e 13/D05; chips, ações, alvos e retorno ao recorte de pagas verificados | Focos separados; comparação de composição, sem equivalência pixel a pixel |

Frontend leu guia, HTML e capturas dos frames, que continuam draft. As diferenças de composição foram delegadas; o canvas não foi alterado. Capturas reais: `web/e2e/__screens__/pedido-{topo,fundo}-{mobile,desktop}.png` e `modo-simples-{mobile,desktop}.png`. QA confirmou cleanup final, matriz CA01–14 e rastreabilidade RF21/RF22/RF25/RF06/RF13 estáveis após a integral. Parecer detalhado: `/tmp/varal-qa10.md`.

## Rastreabilidade da validação

A [matriz](../../matriz-rastreabilidade.md) registra os testes por requisito. Os 14 CAs foram encerrados por combinação da integral, testes dirigidos, provas reais isoladas e comparação visual. A evidência de cada camada conserva seus limites:

| Critérios | Lastro verificado |
| --- | --- |
| CA01–03 | API: `test_rn20_solicitacao_copia_privada_pagamento_e_undo`, `test_q10_2_versao_revisada_impede_compartilhar_alteracao`, `test_q10_3_nonce_tombstone_impede_post_tardio` e identificação de candidatos atuais; Vitest de consentimento/refetch B10-final1 |
| CA04/05/14 | `test_ca04_pin_sobrevive_exclusao_e_copia_integra`, `test_ca05_cancelamento_durante_put_conserva_tombstone`, `test_ca05_rollback_e_token_abandonado_nao_publica`; prova isolada real de storage/fila, com os limites acima |
| CA06–11 | Integração de pagamento/undo, concorrência real das pontas, ACL, notificações e cleanup na integral API; rodadas dirigidas dos responsáveis e revisão de segurança |
| CA12/13 | `test_q10_10_modo_simples_abertas_de_todos_meses`, flags atuais e Vitest `contas-simples.test.tsx`; comparação visual e navegação nas duas larguras. E2E global aprovado: 143 testes e três skips previstos |

## Falhas e correções

Os focos anteriores registraram 8 aprovados/4 falhas, depois 9/3 e 2/1. Houve falhas reais e ajustes de teste; essas rodadas continuam reprovadas no histórico. Após correções, pedido desktop e oito baselines passaram em etapas separadas. O último foco de duas larguras aprovou desktop e falhou no mobile por procurar o nome desktop do retorno: o trace mostrou **Voltar** no mobile e **Fechar detalhe** no desktop. A retentativa somente mobile, com seletor responsivo corrigido, passou 1/1. Nenhuma dessas rodadas é somada ou convertida em aprovação da integral.

Keys React distintas `pedido:<id>` e `pagamento:<id>` corrigiram duplicação e perda da folha após refetch. O controlador simples permanece fora dos cards. O alvo real de Editar conta passou de 42 px para 44×44. Saída e detalhe/retorno reutilizam fluxos autorizados existentes. CSS limita fieldset/chips e empilha ações quando necessário, corrigindo corte de e-mails e sobreposição de Copiar Pix em 390 px. Q04-29/Q10-17 preserva uma linha com reticências, texto integral no `title` e nome acessível.

B10-pre1 corrigiu retry adicional do SDK com `total_max_attempts=1`. B10-final1 impediu que refetch de grupo único A para B trocasse o destino consentido: seleção inicial é fixa; perda de elegibilidade limpa pagador/confirmação e exige nova escolha. Undo projetado no pessoal usa autor NULL e marcador automático, mantendo autoria real somente no contexto local autorizado. Segurança releu os patches.

## Fechamento e pendências externas

Os 14 CAs, a matriz, os pareceres e o fechamento documental foram consolidados. Na abertura da etapa 11 em 16/11/2026, a orquestração realizou o commit local `062258c` e o merge `--no-ff` na main `5cd29ba`, sem push. Preparação/cancelamento 202 sem corrida controlada de worker não foi demonstrada em UI; há testes de API/unidade e protocolo de nonce/tombstone, sem transformar essa cobertura em prova de navegador. A prova real de CASCADE/preservação não entrega exportação/exclusão LGPD ou Perfil da etapa 11. Contenção global não foi medida.

O dono atestou Ajustes sem pendentes no chat; não houve leitura ou marcação remota, nem reexportação pelo Codex. **Itens a marcar remotamente: nenhum novo conhecido.** P10 está resolvida por delegação para composição do Perfil na etapa 11; P6 é externa, P11 depende do destino de implantação, P3/P4 pertencem à produção e P9 ao próximo push. Sem push, deploy ou envio externo. Commit e merge locais confirmados na abertura da 11: `062258c` e `5cd29ba`.
