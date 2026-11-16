# API e OpenAPI

> **Contém:** endpoints, sessão/CSRF e geração do contrato composto e dos tipos do frontend.
> **Origem:** RNF12, seção 9 de `docs/especificacao-varal.md` e implementação das Etapas 00 e 02–08 (08 concluída).

## Fluxo

1. Endpoints próprios usam drf-spectacular (`@extend_schema`); autenticação usa o schema nativo do allauth.
2. `make types` executa `manage.py export_schema --file openapi.yaml`: `CombinedSchemaGenerator` combina ambos, preserva os caminhos e prefixa componentes/referências da biblioteca com `Allauth`. Divergência de versão OpenAPI, colisões e schema inválido fazem a geração falhar.
3. openapi-typescript gera `web/src/types/api.ts` a partir desse contrato único. A exportação é ordenada e tem teste de determinismo.
4. Os dois arquivos são **versionados** e entram no mesmo commit da mudança na API; o job `types` do CI usa o mesmo exportador e falha se houver diff.

O front só usa tipos de `@/types/api` (ex.: `components["schemas"]["Health"]`); nada de tipo da API escrito à mão.

## Onde ver

| URL (dev) | O quê |
| --- | --- |
| http://localhost:8000/api/schema/ | Schema OpenAPI (YAML; JSON com `Accept: application/json`) |
| http://localhost:8000/api/docs/ | Swagger UI |
| http://localhost:3000/api/… | Mesma API, via proxy do Next (é o caminho que o front usa) |

## Convenções

- Rotas próprias sob `/api/`, terminando em `/`. **Exceção:** endpoints nativos allauth em `/api/auth/browser/v1/` preservam os sufixos sem barra final; o proxy Next mantém método, body e cookies, sem redirecionar o POST.
- Autenticação exigida por padrão, **só por sessão** (`SessionAuthentication`; sem HTTP Basic desde a Etapa 03); rota pública declara `AllowAny`.
- Dinheiro em centavos (`int`), ids UUID, datas ISO 8601 em UTC.

## Endpoints

| Método e rota | Etapa | Descrição |
| --- | --- | --- |
| `GET /api/health/` | 00 | `{"status": "ok"}` se a API alcança o banco |
| `GET /api/me/` | 02 | `id`, `nome`, `email`, `espaco_pessoal: {id, tipo, nome}` do solicitante; `Cache-Control: private, no-store` |
| `GET /api/me/` | 03 | acrescenta `grupos: [{id, nome, papel}]` |

## Grupos e convites (Etapa 03)

Toda rota de grupo passa por `api/apps/espacos/acesso.py`: **404** se não participa (sem revelar existência), **403** se o papel não tem a ação. Ids aninhados (membro, casa, convite) são buscados dentro do grupo da URL. **409** quando a RN04 barra (último admin).

| Método e rota | Permissão | Entrada / resultado |
| --- | --- | --- |
| `GET /api/grupos/` | autenticado | `id, nome, papel, membros_qtd, casas_qtd` (contagens `null` para pagador) |
| `POST /api/grupos/` | autenticado | `{nome, casas?}` → 201; criador único admin |
| `GET /api/grupos/{id}/` | `ver_grupo` (pagador 403) | `meu_papel`, `janela_alerta_dias` (04), `membros [{id, usuario, nome, email, papel, sou_eu}]`, `casas` não arquivadas. `usuario` (id do usuário, Etapa 04) alimenta "Quem paga" e "Quem vê". `email` é `null` para não admin quando o membro tem nome (RNF04) |
| `PATCH /api/grupos/{id}/` | `gerenciar_grupo` | Etapa 04: `{janela_alerta_dias}` 1–7 (RN13) → grupo; fora do intervalo 400 |
| `POST /api/grupos/{id}/sair/` | participante | 204; 409 (RN04 ou RN32). Etapa 04: ver [saída e RN32](#saída-e-rn32-etapa-04) |
| `POST /api/grupos/{id}/convites/` | `gerenciar_grupo` | `{papel}` → `{id, url, expira_em, papel}`; `url` com o token **só aqui** |
| `GET /api/grupos/{id}/convites/` | `gerenciar_grupo` | pendentes `[{id, papel, criado_em, expira_em, criado_por_nome}]` |
| `DELETE /api/grupos/{id}/convites/{cid}/` | `gerenciar_grupo` | 204 (revoga) |
| `PATCH` / `DELETE /api/grupos/{id}/membros/{mid}/` | `gerenciar_grupo` | `{papel}` / remove; 409. Admin que deixa de ser admin perde os convites pendentes que gerou |
| `POST /api/grupos/{id}/subgrupos/` | `gerenciar_grupo` | `{nome}` → 201 |
| `PATCH /api/grupos/{id}/subgrupos/{sid}/` | `gerenciar_grupo` | `{nome?, arquivado?}` |
| `GET /api/convites/{token}/` | público | `{grupo_nome, papel, expira_em}`; 410 igual para expirado, usado, revogado ou inexistente |
| `POST /api/convites/{token}/aceitar/` | autenticado; throttle `convite_aceite` 10/h por usuário | 201 `{grupo_id, papel}`; 410; 409 já membro; 429 |

O token de convite não aparece em log do Django nem do `next dev`; o access log de produção fica na P4.

## Contas (Etapa 04)

Toda consulta passa pelo filtro central de `acesso.py`: `lancamentos_visiveis` dentro de um espaço e `lancamentos_do_usuario` no detalhe e no admin. Ambos usam as mesmas regras de papel e visibilidade. **404** para conta que o usuário não vê (inexistente, de outro espaço ou restrita sem acesso; nunca 403); **403** só se ele vê e o papel não tem `editar_conta`/`criar_conta` (RN05). Inexistente e invisível percorrem o mesmo caminho estrutural de consultas, sem garantia de tempo constante. Totais, contagens, `atencao`, `por_casa` e `opcoes` saem só do visível. Totais, `atencao` e `por_casa` nunca somam canceladas (D2); elas só entram em `contagens.canceladas` e em `status=canceladas`.

**Prazo e selo ([ADR 0009](../arquitetura/adr/0009-filtro-temporal-contas-abertas.md)):** `status=vencidas` e `contagens.vencidas` incluem abertas `pendente` ou `aguardando` com vencimento anterior a hoje em Fortaleza, dentro do mês/filtros da lista. O resumo usa esse mesmo critério temporal em `atencao`, que pode reunir vários meses. Aguardando mantém `status_exibido=aguardando`; só pendente recebe o selo calculado `vence`/`vencida`. A data é resolvida a cada requisição, inclusive após a virada do dia.

| Método e rota | Permissão | Entrada / resultado |
| --- | --- | --- |
| `GET /api/espacos/{id}/lancamentos/` | participante | `?mes=AAAA-MM` (padrão: mês atual em Fortaleza) `&status=todas\|a_pagar\|vencidas\|pagas\|canceladas` `&subgrupo=<id>` `&pagador=<id>\|nenhum\|ex_membro` → `{mes, total_centavos, contagens: {todas, a_pagar, vencidas, pagas, canceladas}, opcoes: {casas, pagadores, sem_pagador, ex_membro}, itens: [Conta]}`. `opcoes` alimenta os chips "Casa" e "Quem paga" com o visível do mês |
| `POST /api/espacos/{id}/lancamentos/` | `criar_conta` | `{descricao, valor_centavos, vencimento, subgrupo?, pagador?, visibilidade?, acesso?: [usuario_id] (≤ 50)}` → 201 `ContaDetalhe`; nasce `pendente`; sem categoria |
| `GET /api/espacos/{id}/resumo/` | participante | `{mes, janela_alerta_dias, total_centavos, qtd, pagas_qtd, vencidas_qtd, vence_qtd, atencao: [Conta], por_casa: [{id, nome, total_centavos, qtd, pagas_qtd}]}`. `atencao` = vencidas de qualquer mês + vence na janela; `por_casa` vazio no pessoal; `pagas_qtd` na 07 conta paga/confirmada do mês atual em Fortaleza |
| `GET /api/lancamentos/{id}/` | quem vê | `ContaDetalhe` |
| `PATCH /api/lancamentos/{id}/` | `editar_conta` | campos do POST, opcionais (espaço não muda) → `ContaDetalhe`; 400 (inclui a Q19b: ninguém mais veria), 409 cancelada |
| `POST /api/lancamentos/{id}/cancelar/` | `editar_conta` | → `ContaDetalhe`; 409 se não `aguardando`/`pendente` |

- **Conta:** `id, espaco {id, nome, tipo}, descricao, valor_centavos, vencimento, status, status_exibido (+ vence, vencida), dias_para_vencer, subgrupo {id, nome}|null, pagador {id, nome, sou_eu}|null, visibilidade, criado_em`.
- **ContaDetalhe:** Conta + `criador {nome, sou_eu}`, `acesso [{id, nome}]` (seleção editável), **`quem_ve [{id, nome}]`** (somente leitura: audiência efetiva da restrita pelo filtro RN06/RN07, considerando criador, pagador, escolhidos e papéis atuais, sem duplicatas; vazio nas demais contas), `historico [{acao, automatica, autor, sou_eu, dados, criado_em}]`, `pode_editar`.
- **Nomes:** em `pagador`, `criador`, `acesso`, `quem_ve` e `opcoes`, membro atual aparece pelo nome ou, se vazio, pelo e-mail; quem saiu ou excluiu a conta aparece como "Ex-membro", nunca pelo e-mail. Vale também para o pagador que já pode ver a conta, sem criar uma listagem geral de membros para ele. No `historico`, `autor` e as pessoas de `dados` vêm resolvidos dos ids gravados: nome, "Pessoa sem nome" ou "Ex-membro", **nunca e-mail**; ação automática tem `autor: null`. Ações em [modelo](../dados/modelo.md#implementação-da-etapa-04).

**Concorrência:** criar revalida vínculo e permissão sob travas compatíveis com saída, remoção, troca de papel e exclusão de usuário. Essas operações travam todas as contas abertas do grupo, inclusive as ainda públicas, antes de avaliar a RN32; uma conversão concorrente para restrita não pode deixá-la órfã. O detalhe segue a ordem admins → membro → conta, revalida a autorização e mantém as travas até carregar relações e serializar, inclusive contas fechadas (correção B07-1 da 07). POST/PATCH/cancelar mantêm a própria transação até construir a resposta; a exceção de responder a quem acabou de retirar seu próprio acesso reconhece somente a própria operação, sem reler edição posterior de outra pessoa.

### Saída e RN32 (Etapa 04)

`POST /api/grupos/{id}/sair/` aceita corpo opcional `{resolucoes: [...]}` (no máximo 50; ADR 0007), cada item `{lancamento, acao: "acesso", usuarios: [id] (≤ 50)}` ou `{lancamento, acao: "cancelar"}`.

- **409 `conta_restrita_orfa`:** a saída deixaria restrita aberta sem ninguém que a veja. Corpo `{detail, code, contas: [{id, descricao}], pessoas: [{id, nome}]}`; `pessoas` contém somente candidatos atuais elegíveis (admin, membro, observador), excluindo quem sai. `nome` segue a regra de nome/e-mail de membro atual, inclusive para saída do pagador; não é acesso permanente à lista do grupo. Nada muda, nem as resoluções enviadas.
- **400:** resolução de conta que não bloqueia a saída, ou `usuarios` fora de admin/membro/observador do grupo.
- Resoluções e saída na mesma transação; histórico com `motivo: "saida_rn32"`. Nenhum outro endpoint aceita `resolucoes`.
- `DELETE` e `PATCH /api/grupos/{id}/membros/{mid}/`: contrato e respostas **sem mudança**. A remoção cancela as órfãs (`cancelada_automaticamente`) e a troca para pagador preserva o acesso (`acesso_preservado`) sem sinal nenhum ao admin.

**Admin do Django:** lançamentos e históricos continuam somente leitura e obedecem ao filtro central, inclusive para superusuário. A confirmação de exclusão de usuário omite a árvore/contagens de contas e históricos; o bloqueio RN32 usa mensagem genérica. Isso limita a aplicação administrativa, não o acesso direto do operador da infraestrutura ao banco.

## Boleto e Pix (Etapa 05)

| Método e rota | Permissão | Entrada / resultado |
| --- | --- | --- |
| `POST /api/boletos/ler/` | sessão autenticada e CSRF; nenhum acesso a contas | Exatamente um de `{codigo: string}` (até 4096 caracteres) ou `{chave_pix: string}` (até 77). Retorna `{instrumento: {tipo, codigo, chave_pix, beneficiario}, valor_centavos: int\|null, vencimento: date\|null, vencimentos_possiveis: date[], avisos: string[]}`. Preview sem gravação; inválido → 400; sem sessão/CSRF → 403 |
| `POST /api/espacos/{id}/lancamentos/` | `criar_conta`, com as guardas da 04 | Além dos campos já obrigatórios da conta, aceita `instrumento: {codigo}` ou `{chave_pix}`, opcional/nulo. Revalida no backend e grava conta/instrumento/histórico atomicamente; ausente ou nulo = manual |
| `PATCH /api/lancamentos/{id}/` | `editar_conta` | `instrumento` omitido preserva a relação; `{codigo}`/`{chave_pix}` troca e `null` remove explicitamente para manual. Mesmo omitido, instrumento persistido é revalidado contra valor/data finais. Conflito → 400 sem gravação parcial; troca/remoção em paga ou confirmada → 409 |
| `GET /api/lancamentos/{id}/` e respostas de mutação | acesso autorizado à conta | `ContaDetalhe` acrescenta `instrumento: {tipo, codigo, chave_pix, beneficiario}\|null`. Tipo é `boleto_bancario\|boleto_arrecadacao\|pix`. Manual não tem relação e retorna `null` |

O tipo é inferido pela leitura, não confiado à entrada. Não há rota de instrumento por id nem acesso próprio no Django admin; o acesso vem exclusivamente da conta e mantém as guardas de concorrência da 04. Código/chave não são enviados em listas/resumos nem registrados no histórico; a alteração registra apenas tipos antes/depois e `codigo_alterado: true`. Reenvio idêntico não duplica histórico. Na Etapa 08, conta aguardando exige `confirmar_chegada: true` e valor/data completos para passar a pendente na mesma transação; instrumento/upload isolado não confirma; esta etapa não cria aguardando avulsa nem aceita PATCH livre de status.

**Vencimento bancário (Q05-4):** fator 0000 não sugere data; 0001–0999 usa a base legada; 1000–9999 sugere o ciclo reiniciado em 22/02/2025 e também retorna a alternativa legada em `vencimentos_possiveis`. O usuário escolhe explicitamente uma data codificada; ao adicionar/trocar instrumento ambíguo, omitir a data dá 400. Não há escolha por proximidade com o relógio. Arrecadação/Pix/fator zero requerem data informada pelo usuário. Valor aplicável no código prevalece e conflito explícito é rejeitado; zero monetário do boleto significa ausência a preencher, não conta de valor zero. Avisos legíveis usam dd/mm/aaaa, enquanto campos de data do DTO mantêm ISO 8601.

**Pix:** valida TLV/CRC por bytes UTF-8, preserva BR Code completo e não consulta URL dinâmica, DICT ou titularidade. Em QR estático, ID54 ausente pede valor; presente com zero é inválido. No dinâmico, ID54 e txid são ignorados e o valor é informado pelo usuário. Chave avulsa normaliza apresentação; a chave já embutida deve ser canônica para não reescrever o payload. Beneficiário extraído é dado declarado no código, não identidade verificada. [Fontes e limites](../etapas/05-boleto-pix/fontes.md).

**Fronteira textual:** serializers HTTP rejeitam NUL antes da leitura/gravação. A biblioteca pura tem limite conhecido de NUL em campos textuais com CRC recalculado; a Etapa 06 deve validar NUL e Unicode inválido também no worker, que extrai dados fora do DRF. Não registrar o texto integral do PDF ou códigos em erros/logs.

## PDF do boleto (Etapa 06)

| Método e rota | Entrada / resultado | Autorização |
| --- | --- | --- |
| `POST /api/espacos/{id}/boletos/pdf/` | Multipart `arquivo` PDF, não vazio e até 5 MiB, MIME `application/pdf` e assinatura `%PDF-`; `lancamento_id?` indica destino de edição.202 `DocumentoPDF` após spool privado, sem esperar S3/extração ou criar conta | Criar no espaço ou editar a conta aberta de destino no mesmo espaço; revalida permissão sob travas antes de gravar/enfileirar; sessão/CSRF |
| `GET /api/boletos/pdfs/{id}/` |200 `DocumentoPDF` com `id,estado,nome,tamanho,resultado,avisos`; polling enquanto lê | Draft: uploader e permissão atual de criação/edição no destino, com prazo de 24 h. Vinculado: acesso atual à conta, sem privilégio residual do uploader. Fora do acesso/expirado →404 |
| `GET /api/boletos/pdfs/{id}/arquivo/` | `{url,expira_em}` para documento `lido`/`conferencia_manual`; demais estados →404 | Mesma autorização do polling, revalidada antes de assinar |
| `GET /api/lancamentos/{id}/pdf/` | URL do PDF ativo da conta; sem PDF →404 | Quem vê a conta; observador/pagador autorizado pode baixar sem ganhar edição |

**Documento e leitura:** `resultado` contém candidatos válidos (`tipo,codigo,valor_centavos,vencimento,vencimentos_possiveis,avisos`), metadados opcionais `data_emissao,beneficiario` e valores/datas sugeridos/textuais. Não contém texto integral, staging ou chave S3. O arquivo é enviado ao S3 e lido no Celery, em processo dedicado limitado; o worker atualiza somente documento/resultados, nunca conta salva. Arquivo inválido não pode vincular; PDF válido sem código/leitura vai para conferência manual, sem OCR.

**POST/PATCH da conta:** acrescenta `documento_pdf?: UUID|null`, `data_emissao?: date|null`, `beneficiario?: string|null` (até 200). Campo de PDF ausente preserva, UUID confirma vínculo e `null` remove explicitamente. Draft para criação não vincula a conta existente; draft com destino de edição só vincula à mesma conta. Somente documentos válidos, ativos, prontos e do próprio uploader/espaço são aceitos na confirmação. Metadados exigem PDF e podem ser conferidos por quem edita conta aberta; o beneficiário declarado no Pix não é reescrito por metadado do PDF. Paga/confirmada não trocam PDF/metadados e cancelada não edita.

Quando o PDF tem candidatos válidos, o instrumento confirmado deve corresponder a um deles; múltiplos exigem escolha explícita. Não é permitido ignorar cobrança válida escolhendo manual ou associar código de outro documento. Sem candidatos válidos, permite colar código ou salvar manual com campos completos. Código prevalece sobre texto divergente e datas codificadas conservam a política da 05. Escolher um candidato **não recorta o PDF**: quem vê a conta recebe o arquivo inteiro, com aviso na conferência.

`ContaDetalhe` acrescenta `documento_pdf: DocumentoPDF|null`; instrumento passa a admitir tipo `manual` com código/chave nulos e campo opcional `data_emissao`. Manual antigo sem PDF continua `instrumento:null`; PDF manual cria relação somente para seus metadados. Vínculo/instrumento/campos/histórico são atômicos; histórico usa indicadores `pdf_alterado`/`metadados_pdf_alterados`, sem nome do arquivo, URL, chave de objeto ou conteúdo integral. Metadados idênticos após normalização são no-op; a precedência do beneficiário Pix não gera alteração/histórico fictícios.

**URLs e ciclo:** assinatura dura 60 s e já usa o endpoint público configurado, sem reescrever host. Bucket privado; URL não é persistida no cliente/histórico/log. Revogação impede nova assinatura, mas uma URL já entregue pode continuar válida até expirar ou o objeto ser apagado. Troca/remoção elimina/revoga o documento antigo, que nunca volta a draft; limpeza de S3/spool ocorre após commit com intenção persistida, retry e identificador imutável. Rollback preserva o arquivo usado; tentativas antigas não atingem objeto novo. `recuperar_pdfs` recupera leituras/limpeza e expira drafts sem renovar 24 h por polling. [ADR 0010](../arquitetura/adr/0010-pdf-assincrono-e-conferencia.md), [modelo](../dados/modelo.md#implementação-da-etapa-06).

## Autenticação (Etapa 02)

Base **`/api/auth/browser/v1/`**, acessada pela origem web `http://localhost:3000`:

| Método e sufixo | Entrada / resultado |
| --- | --- |
| `GET config` | Configuração pública/provedores disponíveis; inicializa cookie CSRF |
| `POST auth/signup` | JSON `email`, `password`; cria usuário, espaço pessoal e sessão |
| `POST auth/login` | JSON `email`, `password`; cria sessão e rotaciona CSRF |
| `GET auth/session` | Sessão autenticada (200) ou anônima (401) |
| `DELETE auth/session` | Invalida sessão; 401 com `meta.is_authenticated=false` confirma saída |
| `POST auth/password/request` | JSON `email`; resposta genérica, envio assíncrono quando há conta |
| `GET auth/password/reset` | Valida o header `X-Password-Reset-Key` |
| `POST auth/password/reset` | JSON `key`, `password`; troca senha e retorna 401 sem login automático |
| `POST auth/provider/redirect` | Formulário síncrono com `provider=google`, `process=login`, `callback_url` e `csrfmiddlewaretoken` |

Mutações browser exigem CSRF válido (`X-CSRFToken` no JSON). Ler o cookie atual a cada chamada, pois ele muda no login. Sessão usa cookie HttpOnly/SameSite=Lax; Secure e redirecionamento HTTPS com DEBUG desligado. Sem token no localStorage/sessionStorage. Consultas autenticadas no servidor Next encaminham cookies e não usam cache compartilhado.

Google: o `redirect_uri` OAuth continua **`http://localhost:8000/accounts/google/login/callback/`** (`API_PUBLIC_URL`); a origem autorizada é **`http://localhost:3000`**. Depois do handshake, `callback_url` volta a `/entrar/retorno` no frontend, que consulta a sessão. Credenciais vêm exclusivamente do ambiente da API; `SocialApp` não é administrável nem fonte alternativa de credenciais. Cancelamento ou URL de retorno inválida volta à interface sem autenticar.


## Pagamento e comprovante (Etapa 07, em validação)

Contrato presente no OpenAPI/tipos; resultados finais de QA no [relatório07](../etapas/07-pagamento/relatorio.md). Sessão e CSRF nas escritas; invisível/inexistente →404, visível sem autorização da ação →403, conflito de estado/valor/alvo →409 após autorizar o contexto. Declaração integral, sem operação bancária ou pagamento parcial ([ADR 0011](../arquitetura/adr/0011-pagamento-e-evidencia.md)).

| Método e rota | Entrada / resultado | Guarda |
| --- | --- | --- |
| `POST /api/lancamentos/{id}/pagamentos/` | `{pago_em,valor_centavos_esperado,comprovante_id?}` →201 ContaDetalhe | Pendente e permissão atual de pagar; data civil não futura em Fortaleza; valor integral esperado conferido sob trava; arquivo opcional próprio, válido e do ciclo atual |
| `POST /api/lancamentos/{id}/comprovantes/` | Multipart `arquivo`, `pagamento_id?` →202 Documento | Permissão própria de pagar, sem exigir editar boleto. Sem alvo: pendente; com alvo: marca ativa exata do autor/admin e ainda sem comprovante |
| `GET /api/comprovantes/{id}/` | Documento `{id,estado,nome,tamanho,mime,criado_em}` | Draft: uploader autorizado no contexto/ciclo, até24h; vinculado ativo/histórico: acesso atual à conta |
| `GET /api/comprovantes/{id}/arquivo/` | `{url,expira_em}`; só estado `valido` | Mesma autorização atual; assinatura de60s para o endpoint público configurado |
| `POST /api/lancamentos/{id}/pagamentos/{pid}/comprovante/` | `{comprovante_id}` →200 ContaDetalhe confirmada | Autor/admin visível com permissão atual de pagar; marca ativa exata sem arquivo; vínculo e promoção atômicos |
| `POST /api/lancamentos/{id}/pagamentos/{pid}/desfazer/` | Sem corpo →200 ContaDetalhe pendente | Autor/admin visível; autor agora observador conserva só undo. Alvo desfeito/antigo →409 sem afetar nova marca |

`Documento.estado` é enum `pendente|lendo|valido|invalido|erro`, não status de conta. Aceita JPEG/PNG/PDF até5MiB, imagem até20MP sem animação; subprocesso limitado valida formato, sem atestar autenticidade. Preserva bytes originais/EXIF no storage privado com MIME validado; não expõe metadados pessoais extraídos. Worker só altera documento. O vínculo exige validação pronta e nova autorização; upload tardio não muda a conta.

`ContaDetalhe` acrescenta `pagamento_ativo: Pagamento|null`, `pagamentos: Pagamento[]`, `pode_pagar`, `pode_desfazer_pagamento`, `pode_anexar_comprovante`. Pagamento: `{id,pago_em,valor_pago_centavos,criado_em,desfeito_em,marcado_por,comprovante_id}`; autor é rótulo histórico sem e-mail. A lista histórica conserva a referência de comprovantes das marcas desfeitas. Flags não dispensam autorização no backend. Undo conserva evidência e evento; não há troca/remoção isolada de comprovante nem retorno a draft. Alteração efetiva de valor com marca ativa →409; mesmo valor é no-op. Reabertura limpa pagador sem vínculo atual e recusa RN32 órfã atomicamente.

**Resumos e Ex-membro:** resumo/PorCasa incluem `pagas_qtd`; progresso = paga+confirmada sobre não canceladas do mês de vencimento, só do visível, zero contas →0. Início/resumo e `membros[].contas_atribuidas_qtd` do grupo usam o mês atual em Fortaleza; MemberRow mede atribuição, não autor da marca. A lista aceita `pagador=ex_membro` e expõe `opcoes.ex_membro` apenas se houver FK preservada sem membro atual no conjunto visível do mês; `nenhum` continua separado para FK nula, e opções UUID representam membros atuais.

**Retenção e manutenção:** undo preserva arquivo privado ligado à conta/pagamento histórico; qualquer espectador atual pode baixá-lo. Novas assinaturas revalidam acesso, mas URL já emitida pode valer até expirar. Draft expira em24h; exclusão física gera intenção durável de limpeza após commit. `recuperar_comprovantes` roda pelo beat a cada5min (D07-1), sem implementar recorrência mensal08. Alias `comprovantes` preserva MIME validado, separado do MIME fixoPDF do boleto.

**Evento07→09:** EventoPagamento único é gravado na transação da marca, sem transporte nesta etapa. Anexo não duplica evento e undo não o apaga. A09 deve revalidar destinatário, acesso e marca ativa, consumir/descartar quando inaplicável e evitar entrega duplicada. A interface07 confirma apenas “Pagamento registrado.”

## Recorrências e valores desconhecidos (Etapa 08)

Contrato implementado no OpenAPI e nos tipos gerados, conforme [ADR 0012](../arquitetura/adr/0012-recorrencias-e-valores-desconhecidos.md). Validação final concluída no [relatório](../etapas/08-recorrencia-agendador/relatorio.md).

| Método e rota | Entrada / resultado |
| --- | --- |
| `GET /api/espacos/{id}/recorrencias/` | Lista de `Recorrencia` somente visíveis, inclusive pausadas/encerradas; autorização própria do modelo |
| `POST /api/espacos/{id}/recorrencias/` | `CriarRecorrencia`: descrição, `dia_vencimento` 1–31, `valor_tipo: fixo\|variavel`, `valor_centavos?`, `subgrupo?`, `pagador?`, `visibilidade?`, `acesso?`, `chave_idempotencia` UUID obrigatória e `ocorrencia_inicial?`; 201 `{recorrencia, ocorrencia}` ou 200 no retry idêntico |
| `GET /api/recorrencias/{id}/` | Modelo autorizado; invisível/inexistente retorna 404 |
| `PATCH /api/recorrencias/{id}/` | Campos opcionais de `RecorrenciaEntrada`; sem trocar espaço, competência ou estado livremente |
| `POST /api/recorrencias/{id}/pausar/`, `/retomar/`, `/encerrar/` | Sem corpo; retorna modelo atualizado. Pausar/encerrar não cancelam contas geradas; encerramento terminal |
| `PATCH /api/lancamentos/{id}/` | Acrescenta `escopo: mes\|proximos` e `confirmar_chegada: boolean`; confirmação exige valor/data completos e as guardas de instrumento/PDF |
| `POST /api/lancamentos/{id}/cancelar/` | Corpo opcional `{escopo: mes\|proximos}`; próximos encerra futuro e cancela só abertas visíveis/editáveis desde a competência |
| `GET /api/grupos/{id}/subgrupos/{sid}/arquivamento/` | Preview autorizado `{contas_qtd, recorrencias_qtd}`, sem sinal de itens invisíveis |
| `PATCH /api/grupos/{id}/subgrupos/{sid}/` | Arquivar requer `{arquivado: true, destino_subgrupo: UUID\|null}` explícito; renomear junto é recusado. Move só abertas/modelos autorizados; finais/invisíveis conservam referência histórica |

`Recorrencia` contém `id`, `espaco_id`, descrição, dia, tipo/valor, ids opcionais de casa/pagador, visibilidade/acesso, `estado: ativa|pausada|encerrada`, `motivo_pausa`, criação e flags `pode_editar`, `pode_pausar`, `pode_retomar`, `pode_encerrar`. As flags orientam a UI; cada escrita revalida autorização/estado no backend. Fixo exige positivo e variável exige NULL no modelo.

`OcorrenciaInicial` contém valor positivo e vencimento obrigatórios, mais `instrumento?`, `documento_pdf?`, `data_emissao?` e `beneficiario?`. A criação confirma somente o mês atual em Fortaleza, com as mesmas validações da 05/06; fixa deve coincidir com o valor conferido. Template nunca armazena documento/instrumento reutilizável. A primeira variável pode sair pendente na mesma transação; futuras nascem aguardando/NULL. Falha reverte modelo/conta/vínculo/histórico sem excluir draft válido. A chave é única por ator e assinatura da entrada/espaço; reuso divergente retorna 409. Não há deduplicação por descrição/valor.

`ContaDetalhe` acrescenta `recorrente`, `competencia`, `recorrencia_id` e `pode_ver_recorrencia`; o id é null quando o modelo não é visível, mesmo vendo a ocorrência. Competência é imutável e independente do vencimento editado. `valor_centavos` é nullable, inclusive em cancelada; positivo legado em aguardando é preservado (D08-1). Lista, resumo e `por_casa` acrescentam `valores_indefinidos_qtd` no mesmo universo da soma conhecida; canceladas continuam fora dos totais padrão. Nunca substituir NULL por zero. Progresso permanece por quantidade.

Reingresso usa UUID do criador e papel/vínculo atuais (Q08-10); não restaura pagador ou escolhidos removidos, inclusive via revisão antiga. Ver uma ocorrência não concede gestão do modelo. Rotina/comando revalidam audiência atual, mantêm competência bloqueada em pausa sem audiência e não dão acesso ao admin invisível. Não há envio de push/e-mail nesta etapa.

## Notificações (Etapa 09)

Sessão autenticada e CSRF nas escritas; [ADR 0013](../arquitetura/adr/0013-notificacoes-privadas-e-entrega.md). O mesmo filtro atual serve central, recentes, contador e leitura; revogação de aviso comum é terminal, não retorna por reingresso/undo. P7 é exceção privada sem acesso à conta/PDF. Ver [relatório](../etapas/09-notificacoes/relatorio.md) para provas parciais e limites.

| Método e rota | Entrada / resultado |
| --- | --- |
| `GET /api/notificacoes/` | `cursor?`, `limite?` (1–50, padrão 20); `{resultados, proximo, nao_lidas}`, ordem `criado_em,id` decrescente; cursor assinado |
| `GET /api/notificacoes/resumo/` | `{nao_lidas, recentes}` até três avisos autorizados |
| `POST /api/notificacoes/{id}/ler/` | Sem corpo; `{lido_em}` estável; 404 alheio/revogado/invisível |
| `POST /api/notificacoes/ler-todas/` | Sem corpo; `{nao_lidas}`; todos próprios autorizados inclusive fora da página, sem regravar lidos |
| `GET/PATCH /api/notificacoes/preferencias/` | `{versao:1, email, push}`; PATCH só aceita booleanos conhecidos email/push. Desligar descarta canais pendentes/reservados, sem remover central |
| `GET /api/notificacoes/push/configuracao/` | `{habilitado, chave_publica}`; nenhuma chave privada |
| `POST /api/notificacoes/push/inscricoes/` | `{endpoint, keys:{p256dh,auth}, instalacao:UUID}`; 201 criação/200 retry válido, `{id, ativo}`. Configuração indisponível 503, conflito causal/proprietário 409 |
| `DELETE /api/notificacoes/push/instalacoes/{instalacao}/` | 204; UUID gerado pelo cliente, revogação terminal com tombstone mesmo sem POST prévio. Não existe DELETE por id de inscrição |

Aviso contém `id`, `tipo`, `titulo`, `texto`, `criado_em`, `lido_em` e `destino` opcional. Tipos: `boleto_ausente`, `vence_3`, `vence_hoje`, `venceu_1`, `pagamento`, `pagador_removido`, `cancelada_rn32`. Destino comum é `/contas/{uuid}` autorizado; P7 retorna null e texto mínimo de data/referência/descrição capturada quando existente, motivo fixo, sem enriquecimento pela conta atual. Endpoint/chaves de inscrição são write-only, cifrados no banco e ausentes das respostas.

UUID de instalação fica ligado à origem por fingerprint; aliases equivalentes de endpoint compartilham identidade normalizada (host/porta padrão/percent-encoding), sem reescrever caminho/query opacos no envio, cuja origem é canonicalizada em HTTPS/host minúsculo/443 implícita. Tombstone ou sessão revogada não reativa por retry; novo ciclo exige novo UUID. Fingerprint da sessão é HMAC, não a chave de sessão gravada. Logout nativo allauth também revoga sessão/instalações/inscrições no servidor; cliente cancela epoch, revoga antes de destruir sessão e tenta desinscrever navegador, mostrando falha parcial. Troca de usuário não transfere origem conhecida automaticamente.

Não há endpoint cliente para disparar avisos. Rotina/dispatcher consomem outbox e revalidam acesso; transporte genérico abre central autenticada. Prova local não constitui aprovação E2E, provedor público ou recebimento físico.
