# Plano — Etapa 05 (Boleto e Pix)

> **Contém:** responsabilidades, modelo e contrato recomendado para implementar RF08/RF09/RF14.
> **Origem:** spec da Etapa 05, modelo de dados e API existentes da Etapa 04; decisões delegadas em `decisoes.md`.

## Ordem e responsabilidades

1. `varal-boletos`: funções puras de parsing/normalização em `api/apps/boletos/`, vetores independentes e pesquisa dos padrões oficiais FEBRABAN/BCB quando necessária. Validar bancário47, arrecadação48 e Pix/chaves sem rede e sem dependência Django para a lógica dos códigos.
2. `varal-backend`: Instrumento, migração, validação de entrada, preview autenticado e integração atômica com criar/editar/detalhe/histórico. Todo acesso a instrumento persistido começa pela conta autorizada, sem endpoint por id isolado.
3. Orquestrador: `make types`, conferir contrato e tipos gerados antes da integração web.
4. `varal-frontend`: reler Doop e integrar entrada/conferência/detalhe/cópia; reutilizar componentes e hooks existentes com tipos gerados.
5. `varal-devops`: apenas se dependência/ambiente exigir; parser e preview não precisam de serviço externo.
6. `varal-qa` → `varal-seguranca` → `varal-decisor` → `varal-docs`: testar, revisar, auditar decisões e fechar evidência/docs. Sem push.

## Modelo

`boletos.Instrumento`: vínculo único `lancamento` (PK UUID da conta ou UUID próprio + OneToOne), `tipo` (`boleto_bancario|boleto_arrecadacao|pix|manual` conforme fonte), `codigo` e `chave_pix` opcionais mutuamente coerentes, `beneficiario` quando disponível no payload. Campos de PDF/emissão entram na 06, sem fingir extração agora.

Conta manual legada pode continuar sem relação (`instrumento: null`), sem migração de dados massiva. Para instrumento válido, banco impede duplicidade por conta e o serviço controla consistência entre tipo e conteúdo. Não copiar código/chave para `Historico.dados`: registrar só tipo antes/depois e indicação de troca, resolvendo pessoas por id como na 04. Não criar índices globais ou unicidade sobre códigos: a mesma conta pode ter sido cadastrada legitimamente por pessoas distintas.

## Contrato recomendado

Contrato final deve ser confirmado entre backend/boletos e declarado no OpenAPI; todos os nomes aqui são proposta de implementação, não API já existente.

| Operação | Entrada | Saída/comportamento |
| --- | --- | --- |
| `POST /api/boletos/ler/` | Exatamente um de `{codigo: string}` ou `{chave_pix: string}`; código com no máximo4096 caracteres, chave com limite próprio explícito | 200 `{instrumento: {tipo, codigo, chave_pix, beneficiario}, valor_centavos: int\|null, vencimento: date\|null, vencimentos_possiveis: date[], avisos: string[]}`; 400 erro de código/chave; exige só autenticação; não grava nem consulta contas |
| `POST /api/espacos/{id}/lancamentos/` | Campos da 04 + `instrumento?: {codigo?: string, chave_pix?: string}\|null` | Backend deriva tipo e dados novamente, valida valor/data e cria conta+instrumento+histórico na mesma transação; sem instrumento = manual |
| `PATCH /api/lancamentos/{id}/` | Campos da 04 + `instrumento` opcional; ausente preserva, `null` troca explicitamente para manual | Só edição autorizada; troca em conta aberta; conflito entre valor/data informados e extraídos dá400; sem gravação parcial |
| `GET /api/lancamentos/{id}/` e respostas de mutação | Sem mudança de entrada | `ContaDetalhe` + `instrumento: {tipo, codigo, chave_pix, beneficiario}\|null`; só a conta já autorizada fornece dados do instrumento |

Não acrescentar código completo aos cards/listagens/resumos, onde não há ação de cópia. Front usa `instrumento.codigo` para boleto/BR Code ou `chave_pix` para chave; não recompõe payload de Pix. Limpar apenas pontuação/espaços permitidos da linha digitável; rejeitar caracteres inesperados em vez de apagar qualquer caractere que não seja dígito. Não remover caracteres internos do BR Code. Comprimentos TLV são medidos nos bytes UTF-8 e o CRC é calculado sobre os bytes originais corretos do payload, não sobre uma reconstrução dos campos.

## Preenchimento e conflitos

- Boleto com valor/data presentes: mostrar dados lidos; na gravação o backend impede divergência. Campo zerado/ausente no código não representa cobrança zero: pedir valor positivo (RN11).
- Arrecadação: data obrigatória pelo usuário; quando o identificador denota referência em vez de valor monetário, pedir também o valor.
- Pix estático com valor presente: usar centavos inteiros sem `float`; sem valor ou sem vencimento: pedir os campos faltantes. Pix dinâmico ignora ID54 conforme manual BCB2.10 §2.7, retorna valor ausente e pede preenchimento, sem buscar URL. Não deduzir vencimento do Pix sem informação definida pelo padrão.
- Fator bancário: zero não sugere data; 1–999 segue base legada; 1000–9999 sugere ciclo atual e expõe alternativa legada em `vencimentos_possiveis`. A interface avisa a ambiguidade e permite escolher data antiga; o save aceita apenas uma das datas da lista quando houver fator. Nunca escolher por aproximação com a data atual. Fontes: manuais oficiais Itaú/Banrisul, registrados no documento do especialista.
- Alteração de instrumento de paga/confirmada: recusar nesta etapa, preservando comprovabilidade até o fluxo da 07. Cancelada já não edita. Anotar essa restrição como decisão delegada.

## Verificações

Regressões de DV/CRC usam vetores conhecidos ou gerados por implementação independente, não só o mesmo cálculo da função testada. Cobrir entrada adversária limitada, unicode/dígitos não ASCII, payload truncado/duplicado e campos monetários inválidos. Para privacidade, inspecionar payload de detalhe, admin, logs e histórico. Preview nunca usa rede, nem quando encontra URL dinâmica.

Ao concluir: aplicar migrações sem apagar dados; `make test`, `make lint`, `make types` determinístico, E2E das entradas e cópia nas duas larguras; revisão de ajustes conforme declaração atual do dono e registro de eventual atualização que ele enviar. P6 permanece explicitamente externa até a reexportação pelo Claude Code.
