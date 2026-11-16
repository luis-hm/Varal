# Plano — Etapa 06 (PDF do boleto)

> **Contém:** responsabilidades, modelo, contratos sugeridos e verificações da fatia PDF.
> **Origem:** spec da 06, RF23–RF25/RN25–RN29, ADR 0002/0010, contratos da 05 e auditoria preparatória de infraestrutura em `/tmp/varal-infra-auditoria.md`.

Etapa aberta e concluída em 16/11/2026, com implementação e validação final entregues. Este plano preserva o desenho aprovado; contrato/modelo efetivos e evidências são reconciliados em API/modelo/relatório, sem tratar planejamento como execução concluída.

## Ordem de execução e propriedade

1. `varal-docs`/`varal-decisor`: triagem deste planejamento e registro das decisões sob delegação, antes da execução.
2. `varal-boletos`: extrator puro de PDF/texto em `api/apps/boletos/`, reutilizando parser da 05. Deduplicação/candidatos, divergência texto/código, emissão/beneficiário, limites/erro recuperável e validação de Unicode fora DRF. Fixtures independentes de banco.
3. `varal-backend`: documento temporário, tarefas Celery e execução da extração em **processo dedicado com limites de tempo/memória/logs**, permissões, upload/polling/vínculo/download e integração com transações/travas da conta. Migrações sem backfill destrutivo.
4. Orquestrador: gerar/revisar OpenAPI e tipos antes do frontend.
5. `varal-frontend`: ler Doop05/M01,06/M02,07/D03 e integrar upload, polling, prévia/conferência, substituição e download nas duas larguras.
6. `varal-devops`: dependências/lock, django-storages e Silo privado, bucket/bootstrap, endpoints interno/público, Makefile/CI. Pode preparar infraestrutura em paralelo com o backend somente com arquivos de propriedade separados e contrato acordado.
7. QA → segurança → decisor → docs → commits/relatório; merge local e próxima etapa seguem autorização vigente, sem push.

Preparação anterior: extrator puro com 17 testes verdes e reauditoria de catálogo inválido, logs de dependência protegidos e linha quebrada. A biblioteca já está integrada; implementação e prova real de worker/S3 são registradas separadamente do QA integral, ainda em andamento.

## Modelo recomendado

`boletos.DocumentoBoleto` com UUID, `espaco` CASCADE, `criado_por` SET_NULL, **`destino` FK opcional à conta da edição** (CASCADE), **`lancamento` OneToOne opcional CASCADE somente para vínculo confirmado**, arquivo privado/chave imutável, `estado` (`pendente|lendo|lido|conferencia_manual|invalido|falhou`), tamanho, nome seguro de exibição, `resultado` JSON estruturado sanitizado, avisos, datas de criação/leitura e **marca irreversível `vinculado_em`**. Upload em edição grava destino, não lancamento; polling/save revalidam permissão de edição e o vínculo só pode ser feito à mesma conta. Sem destino, o draft é para criação no espaço. Enquanto não vinculado exige autor; após vínculo não usar propriedade do uploader para acesso. O arquivo e resultados são imutáveis por upload; troca cria documento novo.

Documento antigo é eliminado/revogado na substituição; nenhuma operação limpa `vinculado_em` para reabrir acesso de draft. Se mantido para controle de limpeza, estado revogado é terminal e nunca assinável por uploader. Excluir conta pessoal apaga registros e enfileira limpeza dos arquivos após commit; excluir uploader não apaga PDF de conta do grupo (SET_NULL preserva registro vinculado).

`Instrumento` ganha `TipoInstrumento.MANUAL` para PDF válido sem código, `data_emissao` opcional e suporte a beneficiário extraído (ampliar limite atual25, sugerido200). Payload de manual é nulo; manual legado sem PDF continua sem relação. O PDF pertence ao DocumentoBoleto vinculado à conta, não a uma URL pública gravada em `Instrumento`. Ajustar restrição estrutural para o tipo manual sem enfraquecer boleto/Pix.

Resultado do worker contém candidatos de código válidos, valores/datas aplicáveis, metadados opcionais sanitizados, avisos e estado; não texto integral, URL assinada ou traceback. Múltiplos candidatos distintos requerem escolha explícita. Worker nunca atualiza lançamento/instrumento/histórico automaticamente.

## Contrato recomendado

Nomes são proposta para alinhamento backend/frontend antes do código; os serializers finais definem o contrato gerado.

| Método/rota | Entrada | Permissão e resultado |
| --- | --- | --- |
| `POST /api/espacos/{espaco_id}/boletos/pdf/` | multipart `arquivo` e `lancamento_id?` de destino para edição | Criar no espaço, ou editar a conta de destino no mesmo espaço; `lancamento_id` preenche apenas `destino`, não o vínculo confirmado. Valida tipo/tamanho/conteúdo básico, salva privado, enfileira `on_commit`;202 `{id,estado,avisos}` sem conta nova nem substituição imediata |
| `GET /api/boletos/pdfs/{id}/` | — | Draft: somente autor com permissão atual no espaço/destino. Vinculado: somente filtro atual da conta.200 `{id,estado,resultado,avisos}`;404 uniforme fora do acesso |
| `GET /api/boletos/pdfs/{id}/arquivo/` | — | Mesma autorização acima, com documento ativo;200 `{url,expira_em}`, assinado por 60 s no endpoint público; sem redirecionar para URL derivada de entrada do usuário |
| `GET /api/lancamentos/{id}/pdf/` | — | Quem vê a conta recebe `{url,expira_em}` do PDF ativo; sem PDF/invisível →404; pagador/observador não ganham edição |
| `POST/PATCH` da conta | Campos05 + `documento_pdf?: UUID\|null`; metadados confirmáveis `data_emissao?`, `beneficiario?` no contexto do PDF | Ausente preserva; UUID vincula draft próprio/do mesmo espaço pronto, uma vez. Draft com destino só no PATCH da mesma conta; sem destino só no POST de criação. Null remove explicitamente. Revalida permissão, código, campos completos e vínculo sob travas. Conta/instrumento/documento/histórico na mesma transação |
| `GET` detalhe da conta | — | Acrescenta referência segura de PDF ativo, nome/tamanho e metadados; sem URL permanente/chave de objeto. Pedir URL somente quando necessário |

Para código extraído escolhido, front envia também a entrada de instrumento já suportada na 05 e os valores/datas conferidos. Backend não confia no preview, reusa parser da 05 e a política de datas codificadas. Para PDF sem código, permite instrumento manual com dados completos. Campo de emissão/beneficiário pode receber sugestão extraída; edições permitidas devem ficar explícitas nos serializers/tela. PDF de boleto não transforma o campo de nome Pix em identidade verificada.

## Estados, idempotência e limpeza

- API recebe o multipart e grava spool em volume privado compartilhado; não chama S3 ou extrator. Enfileirar somente após commit do draft. Tarefa recebe id do documento, não bytes/código/URL em argumentos. Envio ao S3 e extração limitada em processo dedicado acontecem no worker, fora da requisição e de uma transação longa ([ADR 0010](../../arquitetura/adr/0010-pdf-assincrono-e-conferencia.md)).
- Tomar/revalidar estado com trava curta; duplicatas retornam resultado existente ou não concorrem na mesma leitura. No fim, atualizar somente documento ainda ativo/da versão esperada. Tarefa de documento removido/revogado é no-op; nenhuma tarefa altera conta salva.
- Celery baixa o objeto autorizado para arquivo temporário com limite de bytes e orquestra um processo dedicado para extração. Backend define limites concretos de tempo, memória e saída/logs, encerra o filho ao excedê-los e valida/sanitiza a resposta antes de persistir. Não executar PDFplumber no processo Celery compartilhado: expansão de página antecede a contagem de caracteres, e a fábrica global de logs de dependências pode interferir em outras tarefas. Testar timeout/memória e preservação da saúde da API, não apenas mocks do parser.
- Erro transitório de storage/fila tem retry limitado e estado recuperável; PDF válido não legível vai para conferência manual com aviso simples. PDF inválido não pode ser anexado, embora o tratamento assíncrono possa detectar a invalidade após202.
- Limpeza de substituído/removido usa chave imutável em `on_commit`; rollback não dispara delete. Preferir registro transacional de limpeza pendente para retry se broker/storage falhar, com comando idempotente de recuperação. Nunca reutilizar chave entre uploads.
- Drafts não vinculados expiram após24 h e recebem limpeza idempotente; implementar comando/tarefa de manutenção que não apaga documentos vinculados. A agenda diária definitiva pode ser integrada ao beat na08; a06 precisa demonstrar o comando e o caminho de retry, não fingir cron inexistente.

## Storage e verificação

Adicionar pdfplumber, django-storages e backend S3/cliente ao lock; ambiente em `.env.example` somente com valores locais. Usar imagem/tag Silo do ADR 0002, bucket privado e bootstrap repetível. P1 já atestou serviço/autenticação; ainda testar PUT/GET/DELETE, link público válido/expirado e ausência de acesso anônimo.

API/worker usam endpoint interno S3; cliente de assinatura usa endpoint público configurado. Não reescrever URL já assinada. Nome original é só exibição sanitizada; chave de objeto é opaca, sem nome/e-mail/descrição. Download define `application/pdf`, nome seguro e disposição apropriada; prévia deve tratar arquivo como conteúdo não confiável, sem injetar HTML/texto cru na página.

`make dev` deve iniciar storage agora necessário, com prontidão/bucket; CI/testes isolam objetos de fixtures e nunca limpam dados reais. Rodar Silo real ao menos no caminho integrado; mocks não substituem a prova de assinatura pelo endpoint acessível ao navegador. Não escolher storage de produção nem implantar VPS nesta etapa.
