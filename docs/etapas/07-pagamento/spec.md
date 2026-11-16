# Spec — Etapa 07 (Pagamento)

> **Contém:** requisitos, corte delegado do MVP e critérios para registrar/desfazer pagamento e anexar comprovante privado.
> **Origem:** RF15–RF17, CU08, RN05–RN07/RN12/RN14–RN16/RN21/RN22/RN29/RN30/RN32, RNF01/RNF03/RNF06/RNF11/RNF12; modelo de pagamento; Q04-37 e Q21/Q12/Q23 da 04; infraestrutura de arquivos da 06 e delegação vigente do dono.

## Estado e exigências da fonte

Etapa aberta em 16/11/2026 na branch `etapa/07-pagamento`, após a Etapa 06 validada e integrada localmente à main em `b21bd83`. Triagem Q07-1–10 concluída por delegação em `decisoes.md` e ADR 0011; estas escolhas não são regras literais preexistentes da origem. Implementação autorizada pela continuidade solicitada pelo dono.

- **RF15/RN14/CU08:** registrar pagamento de conta pendente, com data civil obrigatória que não pode ser futura em Fortaleza. Quem paga no banco é a pessoa; Varal só registra a declaração.
- **RF16/RN15:** comprovante opcional de foto ou PDF; conta paga com comprovante anexado passa a confirmada. Arquivo exige acesso privado/URL curta, e trabalho pesado é assíncrono. Validação de formato não verifica autenticidade bancária do comprovante.
- **RF17/RN16:** somente quem marcou ou admin pode desfazer; pela Q21 da 04, admin só em conta que já vê. Desfazer devolve pendente, com selo calculado pela data. Autoria não abre conta invisível.
- **RN05–RN07:** dono/admin/membro pagam conforme permissão central; papel pagador só paga conta de que é pagador; observador não marca. Acesso explícito a restrita não equivale a permissão de pagar conta atribuída a outra pessoa.
- **Q12/Q23 da 04:** entregar barra de pagas, contagem paga no varal do Início e progresso HouseCard nesta etapa, com dados visíveis reais. MemberRow ganha informação de contas; métrica exata exige a decisão proposta abaixo.
- **Q04-37:** um filtro coletivo Ex-membro para pagadores de identidade preservada que saíram; não fundir ids históricos. FK nula continua Sem pagador, inclusive após exclusão de usuário; não inferir identidade apagada.

O modelo de origem mantém pagamento separado e menciona capacidade de pagamento parcial. Não há fluxo/status parcial em CU08/RN14–RN16 ou tela listada: **entrega apenas de pagamento integral é o corte delegado Q07-1/ADR0011**, não negação do modelo futuro.

## Corte decidido por delegação

Uma marcação integral ativa por conta; registros desfeitos e histórico permanecem. Conta aguardando/cancelada ou já paga/confirmada não recebe nova marcação; duas tentativas concorrentes criam apenas uma marca ativa, sem histórico duplicado. O serviço captura valor atual em centavos e confere o valor esperado mostrado ao usuário para não marcar valor alterado silenciosamente durante o formulário.

Comprovante tem endpoint próprio com permissão de pagamento, sem reutilizar upload de boleto que exige editar. Primeiro marca com arquivo apenas depois de validado; sem arquivo, registra paga. Worker só valida documento e não promove conta automaticamente. Upload posterior vincula à versão específica do pagamento ativo, sob nova autorização; upload atrasado após undo/nova marcação nunca confirma o pagamento errado.

Todo acesso a comprovante vinculado deriva da conta atual. Antes de vínculo, uploader ainda precisa de permissão atual no destino; carregar preview não cria permissão adicional ao pagador. Documento vinculado/revogado não volta a draft. Undo preserva comprovante como evidência histórica privada acessível pela visibilidade atual da conta, sem reabrir draft. Autor ainda visível pode desfazer mesmo se virou observador, exceção limitada RN16×RN05. Anexação posterior exige autor/admin com permissão atual de pagar; um comprovante imutável por marca, correção por undo e nova marca. Q07-3–6/ADR0011 registram essas escolhas. Originais JPEG/PNG/PDF até5MiB e imagens até20MP são preservados com EXIF, com aviso explícito de compartilhamento do arquivo inteiro/metadados. EventoPagamento único é persistido atomicamente para consumo/aviso na09, sem transporte07.

## Telas e resumos

Reler canvas somente leitura:08 · Marcar como paga/M03,09 · Conta paga/M04 e07/D03 para detalhe;02/D02,10/D04 e componentes HouseCard/MemberRow para progresso. Não criar tela/frame. Mesmas rotas/dados em 390×844 e 1440×900; sheets/modal, movimento `check-draw`/saída do varal e `grow`, respeitando movimento reduzido e alvos≥44px.

Q07-7: progresso por **quantidade** `(paga+confirmada)/não_canceladas` do mês, filtrado pelo usuário. Zero contas produz progresso 0, sem divisão por zero; mês explícito permanece. MemberRow "Paga N contas" conta atribuições visíveis do mês à pessoa, não autoria de quem clicou; essa é a interpretação delegada; frontend consultou os frames atuais e QA comparou a interface integrada em navegador nas duas larguras. O mês é o de vencimento, atribuições excluem canceladas e incluem abertas/pagas/confirmadas. Canceladas nunca entram no denominador. Filtro Ex-membro é dimensão do pagador da conta, não de quem registrou pagamento.

## Critérios de aceite planejados

| CA | Dado / Quando / Então | Verificação planejada |
| --- | --- | --- |
| CA01 | **Dada** conta pendente e ator autorizado, **quando** marca com data válida, **então** cria Pagamento UUID/centavos com autoria/data, muda a paga e registra histórico atomicamente; não executa operação bancária. | `test_rf15_rn14_pagamento_*` |
| CA02 | **Dada** data ausente/futura ou valor esperado divergente, **quando** marca, **então**400/409 sem pagamento/status/histórico parcial; hoje é data civil de Fortaleza inclusive perto da virada UTC. | `test_rn14_data_*`, `test_rnf11_pagamento_*` |
| CA03 | **Dado** ator sem acesso, **quando** usa qualquer rota, **então**404; ator visível sem permissão de escrita recebe403. Leitura de comprovante vinculado ativo/histórico é permitida a todo espectador, inclusive observador; autor visível pode undo conforme exceçãoQ07-3; admin não vê por privilégio. | `test_rn01_rn05_rn06_pagamento_*` em todas as rotas |
| CA04 | **Dadas** duas marcações simultâneas ou submit repetido, **quando** confirmam, **então** só uma ativa, uma transição e um histórico; outra tentativa não duplica. Papel/visibilidade são revalidados sob travas. | `test_rf15_rn22_concorrencia_*` |
| CA05 | **Dado** comprovante foto/PDF permitido, **quando** enviado, **então** spool/S3/validação assíncrona privados; só arquivo validado, próprio e do contexto certo pode vincular; inválido conserva data/campos para corrigir ou remover arquivo opcional. | `test_rf16_comprovante_*`, processo limitado |
| CA06 | **Dada** marcação com comprovante válido ou anexação posterior autorizada, **quando** salva, **então** vincula arquivo e promove a confirmada atomicamente; worker sozinho não muda conta. | `test_rn15_confirmada_*` |
| CA07 | **Dado** upload em voo e undo/nova marcação/alteração de papel ou visibilidade, **quando** worker termina ou tenta anexar, **então** não ressuscita status, não confirma outro pagamento e não mantém preview/assinatura indevidos ao uploader. | `test_rn06_rn15_upload_tardio_*` |
| CA08 | **Dada** paga/confirmada, **quando** autor ou admin visível desfaz, **então** registro histórico permanece, apenas a marca alvo é desfeita e selo volta a ser calculado. Outra pessoa/admin invisível não desfaz; um undo atrasado deA não desfaz novoB. | `test_rn16_desfazer_*`, concorrência com alvo UUID |
| CA09 | **Dado** comprovante vinculado, **quando** desfaz a marca, **então** conserva vínculo histórico e arquivo privado legível só pelo acesso atual à conta, sem draft/reuso/cleanup. Correção requer nova marca. Draft expirado e exclusão física têm cleanup após commit; rollback conserva objeto e chave antiga não afeta arquivo novo. | `test_rf16_comprovante_limpeza_*` |
| CA10 | **Dado** documento vinculado e mudanças posteriores de acesso, **quando** pede URL, **então** autorização atual da conta prevalece, anônimo não lê e URL expira; não há URL/chave/conteúdo integral em histórico/log. | `test_rnf03_comprovante_url_*` com S3 real |
| CA11 | **Dadas** contas pagas/confirmadas/canceladas em vários espaços/meses, **quando** vê Início/HouseCard/MemberRow/lista, **então** contagens/barra usam só contas visíveis, mês explícito e canceladas fora; desfazer atualiza coerentemente. | `test_rf13_rf15_resumos_*`; UI/E2E |
| CA12 | **Dados** dois ex-membros e pagador nulo, **quando** filtra, **então** uma opção Ex-membro reúne identidades preservadas; Sem pagador continua separado; contas invisíveis não criam opção ou contagem. | `test_q04_37_ex_membro_*` |
| CA13 | **Dadas** telas de pagamento/confirmação nos dois tamanhos, **quando** usa data/upload/desfazer, **então** fluxo, foco, feedback e animação correspondem aos frames/guia, sem overflow e com movimento reduzido. | E2E390×844/1440×900, screenshots/Doop |
| CA14 | **Dada** etapa final, **quando** fecha, **então** test/lint/types/E2E verdes, storage real, segurança sem bloqueantes e docs/matriz com resultados reais. | QA/segurança/relatório |

## Ajustes, dependências e fora de escopo

Conferência atual pelo dono: "no varal ajustes n tem nenhum pendente", recebida pelo chat, sem conector/marcação remota. P6 é reexportação externa sem categoria pelo ADR 0005. Arquivos reutilizam storage/spool/limpeza da 06, com autorização própria do comprovante e confirmação de pagamento.

Sem iniciação bancária, prova automática de autenticidade, leitura/OCR de comprovante, pagamento parcial no corte decidido, notificações reais antes da 09, sincronização de solicitação/origem RN20 antes da 10 ou nova exceção de visibilidade. P10/P11 (Perfil/deploy) continuam específicos da 11, sem bloquear07.

## Rastro da triagem de16/11/2026

Q07-1–9/ADR0011 consolidaram integral, exceção estrita de undo, original/EXIF, retenção histórica, anexação, métricas, reabertura e evento durável para09. CA03 eCA09 corrigidos para não negar leitura de observador nem eliminar evidência no undo. CA01 inclui unicidade/transação do evento de pagamento; CA07 inclui invalidar draft inicial atravessando outro ciclo de marcação/undo. CA08 inclui autor agora observador, pagador ausente e RN32; edição efetiva de valor com marca ativa deve resultar409. A triagem não declarou implementação ou leitura de canvas. O estado posterior da implementação e validação fica no relatório, sem transformar os critérios em resultados verdes.
