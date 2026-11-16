# Spec — Etapa 05 (Boleto e Pix)

> **Contém:** escopo vertical, contratos esperados e critérios de aceite de boleto, Pix e cópia do código.
> **Origem:** RF08, RF09, RF14, CU05/CU08, RN01–RN13, RN22, RNF01/RNF11/RNF12; ADR 0005; revisão delegada da Etapa 04 e declaração atual do dono em 15/11/2026: "no varal ajustes n tem nenhum pendente".

## Escopo

- Cadastrar e editar conta com linha digitável bancária (47 dígitos), de arrecadação (48 dígitos), Pix copia e cola ou chave Pix. Cadastro manual da 04 continua funcionando.
- Leitura em função pura do backend: normalizar apresentação do boleto, validar DVs de blocos e geral, extrair valor e vencimento quando presentes; tratar reinício do fator em 22/02/2025 (RN08–RN10).
- Pix copia e cola: estrutura BR Code/TLV e CRC válidos, extração do valor quando presente e beneficiário quando o próprio payload o trouxer. Não consultar a URL de Pix dinâmico nem DICT; chave não é prova de existência ou de titularidade.
- Instrumento separado do lançamento, com vínculo único e acesso herdado da conta. Preview não grava conta; salvar revalida integralmente a entrada.
- Campo de código e conferência no formulário existente, detalhes do instrumento e cópia com um toque. Mesmas rotas e dados nas duas larguras.
- Contas novas nascem `pendente`. Esta etapa não cria `aguardando` avulsa: esse estado nasce da recorrência variável na 08. Código anexado posteriormente a uma aberta aguardando deve transitar para pendente atomicamente, quando esse fluxo existir.

## Ajustes e dependências

O dono declarou não haver ajustes pendentes no documento atual. Isso é conferência pelo chat, sem alegar leitura pelo conector Claude Docs nem reutilizar rev 24 como atual.

**P6 continua externa:** Claude Code reexporta a origem já sem categoria. Não editar `docs/especificacao-varal.md` à mão. A implantação segue sem categoria pelo ADR 0005 já aprovado; a reexportação pendente não autoriza acrescentar campos antigos ao MVP.

## Telas a reler no Doop

Canvas `k0kB5dc-Vo`, somente leitura; localizar pelo nome antes de implementar. Esta lista é referência local, não evidência de leitura nesta etapa.

| Mobile | Desktop | Entrega |
| --- | --- | --- |
| 05 · Nova conta | M01 · Nova conta | Entrada por código/Pix/manual, espaço atual primeiro; PDF permanece para 06 |
| 06 · Conferir conta | M02 · Conferir conta | Código, dados lidos, valor/data faltantes e campos da conta já existentes; sem prévia de PDF |
| 07 · Detalhe da conta | D03 · Contas + Detalhe | Tipo, código/chave, beneficiário disponível e botão de cópia; sem PDF ou pagamento |

Reutilizar Field, Button, Chip, Folha e Icon. Seguir `varal-ui`, tokens e movimento. Campo de código pode ocupar várias linhas; regra de uma linha para nomes de pessoas continua. Pagador/observador com acesso à conta pode copiar, sem ganhar edição. Modo simples completo fica na 10.

## Critérios de aceite

Os nomes abaixo são testes planejados; substituir pelos testes reais no relatório e na matriz.

| CA | Dado / Quando / Então | Verificação planejada |
| --- | --- | --- |
| CA01 | **Dada** linha bancária válida com pontos/espaços, **quando** lida, **então** normaliza para 47 dígitos, valida os três DVs de campos e o geral e devolve tipo e valor em centavos. | `test_rn08_bancario_*`; vetores válidos e mutações inválidas |
| CA02 | **Dado** fator de vencimento bancário, **quando** convertido, **então** respeita reinício 22/02/2025, sugere ciclo atual e expõe a alternativa legada quando ambíguo; fator ausente não inventa data. O save aceita a escolha explícita de qualquer data codificada, sem heurística pelo relógio nem data arbitrária. | `test_rn09_fator_*`, incluindo 1000/1001, ausência e save de boleto legado |
| CA03 | **Dada** arrecadação válida com início 8, **quando** lida, **então** valida DVs com o algoritmo indicado pelo código e devolve valor quando monetário; a data é solicitada ao usuário. | `test_rn08_arrecadacao_*`, `test_rn10_*` |
| CA04 | **Dado** código curto, longo, com letra inesperada ou DV inválido, **quando** lido ou salvo, **então** 400 legível, sem gravação; o front conserva o conteúdo para corrigir. | `test_rn08_codigo_invalido_*`; Vitest/E2E |
| CA05 | **Dado** BR Code válido, **quando** lido, **então** valida comprimentos TLV em bytes UTF-8, CRC nos bytes corretos e BRL, conserva o payload de pagamento e extrai somente dados nele contidos; inválido, truncado ou adulterado é rejeitado. | `test_rf09_brcode_*` |
| CA06 | **Dado** Pix dinâmico ou sem valor, **quando** conferido, **então** a aplicação não faz acesso externo, pede valor/data faltantes e permite salvar apenas dados completos e positivos. | `test_rf09_pix_sem_valor_*`, teste de ausência de rede |
| CA07 | **Dada** chave Pix sintaticamente válida, **quando** cadastrada com valor e vencimento, **então** instrumento Pix persiste e copia exatamente a chave normalizada; chave inválida é rejeitada sem alegar consulta de titularidade. | `test_rf09_chave_pix_*` |
| CA08 | **Dado** preview válido, **quando** salvo com campos manipulados ou código diferente, **então** backend revalida; valor/data codificados não são silenciosamente substituídos por outro valor/data e falha não grava lançamento, instrumento ou histórico parcial. | `test_rn09_rn11_revalidar_salvamento_*` |
| CA09 | **Dado** instrumento ligado a conta pessoal, alheia ou restrita não visível, **quando** outro usuário consulta/copia/tenta trocar, **então** 404 uniforme; quem vê pode ler, só quem edita pode alterar. | `test_rn01_rn02_rn06_instrumento_*`, `test_rn05_instrumento_*` |
| CA10 | **Dada** edição de código/chave de conta aberta, **quando** salva, **então** instrumento e campos derivados mudam atomicamente e histórico registra mudança sem gravar código, chave ou e-mail integrais. Edição sem alteração não duplica histórico. | `test_rn22_instrumento_*` |
| CA11 | **Dada** conta manual antiga ou nova, **quando** criada, listada e aberta, **então** continua com o contrato da 04 e sem botão de copiar fictício; trocar instrumento explicitamente não apaga histórico. | `test_rf10_manual_sem_instrumento_*`; regressão da 04 |
| CA12 | **Dado** detalhe de boleto/Pix autorizado, **quando** copia, **então** área de transferência recebe dígitos do boleto, payload Pix completo ou chave correspondente, com confirmação acessível; falha do clipboard tem alternativa para selecionar/copiar. | Vitest + E2E RF14 nas duas larguras |
| CA13 | **Dadas** telas nas larguras 390×844 e 1440×900, **quando** usadas com teclado e código grande, **então** sem rolagem horizontal, foco correto, alvos ≥44px e composição comparada aos frames atuais. | E2E + screenshots/Doop |
| CA14 | **Dada** implementação final, **quando** executados `make test`, `make lint`, `make types` e E2E, **então** verdes, tipos determinísticos, segurança sem bloqueantes e docs/matriz com evidência real. | QA, segurança e relatório |
| CA15 | **Dado** salvamento ou edição em voo, **quando** a pessoa tenta mudar modo, conteúdo, prévia, fechar a folha ou salvar outra vez, **então** a operação em curso mantém seus controles protegidos e não gera envio duplicado, inclusive antes do próximo render. | Vitest com promessa controlada em criação e edição |
| CA16 | **Dado** código local alterado com sua prévia, **quando** refetch traz outro instrumento remoto para a mesma conta, **então** a sessão do formulário preserva o conteúdo local e sua conferência, sem mostrar dados remotos como se fossem os do código digitado. | Vitest de refetch durante edição local |

## Fora de escopo

PDF/upload/download e data de emissão lida do PDF (06); marcação de pagamento e comprovante (07); geração recorrente (08); envio de lembretes (09); ação de copiar na experiência completa de modo simples (10); iniciação bancária, consulta DICT, execução de pagamento, consulta de URL Pix dinâmica e armazenamento de dados bancários além do instrumento da conta. Categoria permanece fora do MVP.
