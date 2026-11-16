# Spec — Etapa 06 (PDF do boleto)

> **Contém:** escopo, limites, acesso e critérios de aceite do envio/leitura/download de PDF.
> **Origem:** RF23–RF25, CU05/CU08/CU11, RN01–RN13/RN22/RN25–RN29/RN32, RNF01/RNF03/RNF06/RNF11/RNF12; ADR 0002; entregas/limites da 05; declaração atual do dono de ausência de Ajustes pendentes e delegação para as etapas restantes.

## Estado e escopo

Etapa aberta em 16/11/2026 na branch `etapa/06-pdf-boleto`, após o merge local da 05 em `e5c94e3`. O planejamento antes preparado em `/tmp/varal-06/` foi incorporado ao repositório. Backend, infraestrutura e interface entregues; QA integral, inspeção visual e segurança concluídos em 16/11/2026. Definição de pronto alcançada; evidências no relatório, sem alteração dos critérios e decisões abaixo.

- Enviar PDF privado de até **5 MiB (5×1024×1024 bytes)** no cadastro ou na edição da conta aberta; ler texto com pdfplumber no Celery e apresentar resultado para conferência antes de salvar.
- Procurar linha digitável bancária47/arrecadação48 no texto, com pontuação/espaços permitidos, e validar pelo parser da 05. Extrair emissão, vencimento da arrecadação e beneficiário quando presentes; campos ausentes continuam ausentes.
- Código aplicável prevalece sobre texto divergente, com aviso claro. Ambiguidade de fator da 05 mantém escolha explícita de uma data codificada; data do PDF compatível pode ser sugerida sem inventar vencimento.
- PDF escaneado, criptografado sem senha disponível ou sem código válido continua anexável como PDF válido, com conferência manual e possibilidade de colar código; sem OCR. Arquivo inválido/disfarçado é recusado ou marcado inválido, não vinculado.
- Upload gera documento temporário privado, escopado por usuário/espaço, sem criar conta. Só o save autorizado vincula documento, instrumento, dados da conta e histórico atomicamente. Novas contas continuam pendente e com valor/data completos; nenhum aguardando avulso.
- Recepção faz apenas spool em volume privado: envio ao S3 e extração são tarefas Celery, fora da requisição, conforme [ADR 0010](../../arquitetura/adr/0010-pdf-assincrono-e-conferencia.md). Nenhum caminho de staging é público ou aceito como entrada do usuário.
- Quem vê a conta pode baixar o PDF por URL assinada curta, inclusive pagador/observador autorizado; isso não concede edição. Depois do vínculo, nenhum privilégio residual decorre de ter feito upload.

## Acesso e ciclo do documento

Cada upload é imutável, com UUID e chave de objeto novos. Antes do vínculo, somente o autor atual autorizado no espaço pode consultar/pedir URL do próprio draft. Na edição, `destino` opcional identifica separadamente a conta que será editada; exige permissão atual de edição no polling e no save e só admite vínculo a essa mesma conta. **Upload não preenche `lancamento`: esse OneToOne significa vínculo confirmado apenas no save.** Sem destino, o draft é para criação de conta no espaço. Depois do vínculo, todas as rotas usam exclusivamente o filtro da conta, inclusive polling de leitura e download pelo id do documento.

Troca de PDF cria novo draft/leitura; não reescreve o objeto antigo. No save bem-sucedido, o antigo é eliminado/revogado e sua limpeza é enfileirada após commit. Documento antes vinculado nunca volta a ser draft legível pelo uploader: manter marca irreversível de vínculo quando houver retenção, ou eliminar o registro. Rollback não apaga objeto ainda utilizado. Worker antigo não muda conta nem elimina arquivo novo, pois recebe id/chave imutáveis.

URL assinada vale **60s**, emitida somente após autorização. O bucket permanece privado. Endpoint interno da API/worker e endpoint público do navegador são configurações distintas; assinar já para o endereço público, sem trocar host de URL assinada. URL é credencial temporária: não colocar URL/chave de objeto em histórico, logs ou armazenamento persistente do cliente.

## Fronteira textual e execução

Worker fora do DRF valida NUL, surrogates/Unicode inválido, comprimentos e tipos de **todos os campos estruturados** antes de persistir, inclusive JSONB e resultado do parser. O limite conhecido do parser puro da 05 não pode alcançar PostgreSQL como erro 500. Não persistir texto integral do PDF nem incluí-lo em erro/log/histórico.

**Extração em processo dedicado e limitado:** Celery orquestra, mas não executa o parser de PDF no próprio processo compartilhado. Tempo, memória e saída/logs do processo filho têm limites concretos a definir/testar pelo backend; falha ou estouro encerra esse processo e produz estado controlado, sem afetar API ou outras tarefas. Limite de caracteres depois da extração não basta: uma página pode expandir antes dessa contagem. A fábrica de logs/redação de dependências é global no interpretador e precisa ficar confinada ao processo dedicado.

Limites de extração propostos: até 20 páginas e 200 mil caracteres, com tempo limitado da tarefa. PDF válido acima desses limites fica em conferência manual com aviso, sem fingir que foi lido integralmente nem rejeitar o arquivo só pela complexidade. Limites definitivos devem ser registrados na triagem. Mesma linha repetida é deduplicada; várias linhas distintas válidas exigem escolha/conferência, sem selecionar cobrança arbitrariamente.

**Histórico da preparação:** o extrator isolado começou com 17 testes puros e reauditoria dos vetores de catálogo inválido, logs de dependência protegidos e linha quebrada. Foi integrado à API/worker, com processo limitado, storage e interface; a prova real de Celery/S3 foi complementada pelo QA integral final verde. Resultados e limites efetivos são registrados no relatório da etapa.

## Telas a reler

Canvas `k0kB5dc-Vo` somente leitura:05 · Nova conta/M01 (upload e escolha),06 · Conferir conta/M02 (prévia e campos extraídos),07 · Detalhe/D03 (PDF, emissão, beneficiário e download). Referências não equivalem a leitura nesta etapa. Frontend deve reler HTML/screenshots, guia/tokens/componentes e entregar390×844/1440×900. Usar estados claros de envio, leitura, conferência e falha recuperável; nenhum detalhe de fila/worker aparece no produto.

## Critérios de aceite

| CA | Dado / Quando / Então | Verificação planejada |
| --- | --- | --- |
| CA01 | **Dado** PDF real até o limite, **quando** enviado por criador autorizado, **então** spool privado recebe arquivo com identificador novo e retorna202 documento de leitura, sem criar lançamento; worker envia o objeto ao S3 privado. | `test_rf23_rn25_upload_*`; integração S3 real |
| CA02 | **Dado** arquivo acima de5 MiB, vazio, MIME inadequado ou conteúdo disfarçado, **quando** enviado, **então** rejeita sem vincular conta e sem objeto abandonado permanente; PDF válido escaneado não é confundido com inválido. | `test_rn25_limites_tipo_conteudo_*` |
| CA03 | **Dado** upload aceito, **quando** requisição termina, **então** nem envio ao S3 nem extração acontecem nela; Celery processa idempotentemente em processo limitado e polling retorna estado/resultados do mesmo documento. | `test_rnf06_pdf_assincrono_*`, tarefa repetida/falha e limites do processo |
| CA04 | **Dado** PDF com linha47/48 formatada válida, **quando** lido, **então** usa parser/DVs da 05, extrai valor/data aplicáveis e metadados opcionais sem gravar texto integral. | `test_rn26_rn27_pdf_*` com fixtures textuais |
| CA05 | **Dado** valor/data no texto divergente do código, **quando** conferido/salvo, **então** código prevalece, aviso é exibido e save rejeita conflito explícito; fator ambíguo conserva escolha codificada explícita. | `test_rn27_rn28_codigo_prevalece_*`; E2E |
| CA06 | **Dado** PDF válido sem texto, sem linha válida, protegido ou acima dos limites de extração, **quando** processado, **então** oferece conferência manual, preserva PDF e permite colar código/digitar dados completos. | `test_rn28_pdf_manual_*`; E2E sem OCR |
| CA07 | **Dado** texto com NUL/surrogate/campo excessivo, **quando** worker tenta extrair/validar, **então** não causa500/erro de PostgreSQL nem persiste JSON inválido; resultado controlado permite conferência manual. | `test_rn26_pdf_texto_adversario_*`, inclusive parser fora DRF |
| CA08 | **Dado** documento de outro autor/espaço ou conta não visível, **quando** consulta polling/URL/vínculo, **então**404 uniforme. Documento vinculado só usa acesso atual da conta, mesmo quando uploader perdeu acesso. | `test_rn01_rn02_rn06_pdf_*`, negativos em todas as rotas |
| CA09 | **Dado** draft válido próprio e dados finais completos, **quando** salva, **então** conta/instrumento/vínculo/histórico acontecem atomicamente; upload de edição mantém destino separado até o save e só vincula à conta indicada. Sem destino é criação; falha ou concorrência não deixa vínculo duplicado/cruzado. | `test_rn22_pdf_vinculo_atomico_*`, destino trocado/dois saves concorrentes |
| CA10 | **Dado** PDF vinculado, **quando** é trocado/removido, **então** documento antigo não vira draft; limpeza ocorre depois de commit e rollback conserva arquivo anterior. Tarefa antiga não sobrescreve/leva embora objeto novo. | `test_rn29_pdf_substituicao_*`, rollback/retry e uploader removido |
| CA11 | **Dado** observador/pagador que vê a conta, **quando** pede download, **então** recebe URL válida pelo endpoint público por 60 s; anônimo/outro usuário não recebe; URL expirada/sem assinatura não lê objeto privado. | `test_rn29_rnf03_download_*`; Silo real e browser |
| CA12 | **Dado** PDF sem código, **quando** salva dados manuais completos, **então** PDF/emissão/beneficiário permanecem disponíveis com instrumento manual; manual antigo sem PDF continua `null`; nenhuma conta aguardando avulsa é criada. | `test_rf10_rn28_pdf_manual_instrumento_*` |
| CA13 | **Dadas** telas nos dois tamanhos, **quando** envia/confere/troca/baixa PDF, **então** status acessível, alvo≥44px, foco correto, sem overflow e comparação com Doop registrada. | E2E390×844/1440×900 + screenshots |
| CA14 | **Dada** fatia final, **quando** fecha etapa, **então** test/lint/types/E2E verdes, segurança sem bloqueantes, storage real verificado e docs/matriz atualizadas. | QA, segurança e relatório |
| CA15 | **Dado** PDF que excede tempo/memória ou provoca logs de dependência, **quando** processado, **então** extração roda em processo dedicado com limites concretos, é encerrada/controlada sem afetar API/outras tarefas e não deixa texto sensível em logs. Contagem de caracteres e timeout do Celery compartilhado não substituem esse isolamento. | Testes de timeout/memória/saída limitada e concorrência com API saudável |

## Ajustes, dependências e fora de escopo

Conferência atual pelo dono no chat: "no varal ajustes n tem nenhum pendente"; não alegar conector nem usar revisão antiga como atual. P6 continua reexportação administrativa externa pelo Claude Code; ADR 0005 já rege sem categoria. P1 resolvida; a 06 também comprovou objeto, processamento e URL assinada reais.

Fora: OCR, pagamento/comprovante07, recorrência08, avisos09, modo simples completo10, storage/deploy de produção11. PDF não executa boleto nem valida identidade do beneficiário.
