# Relatório — Etapa 06 (PDF do boleto)

> **Contém:** entregas, limites e evidências da validação do PDF privado.
> **Origem:** branch `etapa/06-pdf-boleto`, spec/decisões da etapa, ADR 0002/0010 e relatos backend/frontend/DevOps/QA/segurança em 16/11/2026.

**Estado: concluída em 16/11/2026, pronta para commit e merge local.** **390 pytest, 89 Vitest e 97 E2E passaram, com 3 skips previstos**; lint e tipos determinísticos verdes. Prova real S3/Celery, inspeção headed e segurança sem bloqueantes concluídas. Definição de pronto alcançada. Sem push.

## Entregas

- **RF23/RNF06:** recepção valida PDF de até 5 MiB e faz somente spool privado; resposta 202 não espera S3 nem extração. Celery envia via django-storages e chama pdfplumber em processo dedicado, sem aceitar caminhos do usuário ou servir staging por HTTP.
- **RF24/RN26–RN28:** linhas de 47/48 dígitos validadas pelo parser da 05, metadados opcionais, deduplicação e conferência de candidatos. Código prevalece sobre texto divergente e datas ambíguas conservam a escolha codificada. PDF válido sem leitura/código admite conferência manual, sem OCR. Havendo candidatos válidos, é obrigatório escolher um deles; a interface informa que o arquivo inteiro permanece compartilhado.
- **Modelo:** DocumentoBoleto tem UUID, destino de edição separado do vínculo confirmado e marca irreversível. Instrumento ganha manual, emissão e beneficiário até 200 caracteres; legado sem PDF continua nulo. Save vincula conta/instrumento/documento/histórico atomicamente; worker nunca altera conta salva. PDF/metadados só mudam em conta aberta.
- **Acesso:** draft exige uploader e permissão atual no espaço/destino; após vínculo vale exclusivamente a conta atual. Uploader removido não mantém backdoor. Polling/assinatura/vínculo recusam draft expirado; invisível mantém 404. URL dura 60 s, assinada para o endpoint público, com bucket privado e sem reescrever host.
- **Concorrência/limpeza:** UUID de tentativa impede resultado antigo após recuperação; mutex operacional serializa PUT e limpeza. Intenção persistida no banco se recupera mesmo se fila/storage falharem. Delete físico só após commit, com chave imutável; rollback conserva arquivo ativo. Draft expira em 24 h, sem renovação por polling.
- **RN22:** metadados idênticos normalizados não atualizam conta/histórico; alteração real registra indicador e a precedência do beneficiário Pix não gera falso histórico.
- **UI:** envio/troca/remoção, leitura, candidatos/conferência manual, emissão/beneficiário e prévia/download nas telas existentes. Prévia HTTP(S) S3 cross-origin e abertura alternativa não injetam PDF como HTML do app. Emissão é data civil, sem deslocar o dia por fuso.

Contrato e modelo em [API](../../api/README.md#pdf-do-boleto-etapa-06) e [dados](../../dados/modelo.md#implementação-da-etapa-06); escolhas em [decisoes.md](decisoes.md). O app não executa pagamento bancário.

## Limites e armazenamento

Arquivo até 5×1024×1024 bytes; leitura até 20 páginas/200 mil caracteres; subprocesso com timeout padrão de 20 s, memória de 512 MiB, CPU de 20/21 s e saída de 128 KiB. Celery tem limite operacional de 90 s e retries limitados. Resultado excedido/inseguro vira conferência controlada; JSON tipado, NUL/Unicode, datas/valores e candidatos são validados antes de persistir fora do DRF. Texto integral não vai ao banco, log ou histórico.

API/worker compartilham spool privado. django-storages faz I/O S3; bucket/bootstrap, dependências, volume e CI foram integrados. `recuperar_pdfs` recupera processamento/limpeza e expira drafts; a agenda diária definitiva fica na 08. Revogação impede novas assinaturas; URL já entregue pode valer até expirar ou o objeto ser eliminado, sem promessa de revogação instantânea.

## Verificação

| Verificação | Resultado atual |
| --- | --- |
| `make types` e determinismo | Passaram, exit 0 |
| Pytest integral | **390 passaram** |
| Vitest integral | **89 passaram**; 16 testes pertinentes repetidos após o ajuste de interface também verdes |
| Lint/typecheck | Verdes; conferidos novamente no escopo do ajuste final |
| Prova real DevOps | Celery processou PDF, S3 recebeu objeto privado, spool foi removido; exclusão/cleanup e URL pública/anônima/expirada verificados |
| Inspeção headed | PDF real, iframe e fallback confirmados em mobile/desktop com agent-browser; capturas em `/tmp/varal06-headed-*.png` |
| E2E integral final | **97 passaram, 3 skips previstos, 6,4 min; exit 0** |
| Segurança final | Astra sem bloqueantes por leitura após mutex/tentativas/intenção; nenhuma nova suíte atribuída à revisão |
| Auditoria de decisões | Sem pergunta aberta, interpretação de fonte ou decisão pendente no escopo da 06 |

**Correções preliminares:** no-op de metadados foi reproduzido/corrigido com regressões. Esperas de popup e validação do controle de arquivo foram ajustadas; navegação por Tab real passou, sem usar `.focus()` isolado ou captura headless branca como diagnóstico de falha do visualizador. A rodada integral anterior com falha CA32 não foi contada como verde. A repetição integral final passou; evidências em `/tmp/varal-qa06-final.md`, `/tmp/varal-qa06-e2e-final.json` e na [matriz](../../matriz-rastreabilidade.md). Nenhum servidor Next próprio permaneceu ativo.

Regressões cobrem acesso/expiração, perda de acesso do uploader, candidato incompatível, rollback/cleanup, tentativa antiga, limites reais de memória/saída e upload concorrente com desligamento. CA01–CA15 validados; matriz atualizada e definição de pronto alcançada.

## Doop

Referências 05/M01, 06/M02 e 07/D03, canvas preservado. Mesmas rotas/componentes nas duas larguras. Inspeção headed confirmou PDF/fallback reais em mobile/desktop; capturas e comparação registradas pelo QA, sem comparação pixel a pixel. Nenhuma aprovação ou alteração do canvas foi feita.

## Ajustes e pendências

**Ajustes aplicados:** nenhum item remoto novo. Dono informou no chat: "no varal ajustes n tem nenhum pendente". Conferência fornecida por ele, sem leitura/marcação pelo conector ou reutilização de revisão antiga como atual.

**Ajustes pendentes / itens a marcar como " — feito na etapa 06":** nenhum conforme essa declaração.

- P6 externa: Claude Code reexporta a origem sem categoria; Codex não edita a especificação à mão. ADR 0005 segue vigente.
- Commit e merge local ficam com o orquestrador; não foram executados neste fechamento documental.
- Pagamento/comprovante ficam na 07, agendador na 08, notificações na 09. Perfil/deploy P10/P11 são específicos da 11 e seguem sem resposta, sem bloquear as etapas 06–10 nem autorizar VPS por silêncio.
