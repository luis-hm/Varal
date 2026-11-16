# Varal — Documento de Projeto de Software

Nov 12, 2026 · @RENATO MARTINS

## 1. Objetivo do sistema

O Varal é um app web mobile-first para cadastrar e acompanhar contas (boletos e Pix) no espaço pessoal e em grupos familiares, para que nenhuma conta vença sem que alguém saiba.

**Problema.** Um estudante que trabalha como estagiário paga as próprias contas pequenas e repassa as maiores (aluguel, fatura, luz) para os pais pagarem. O pai administra 3 casas, com muitos boletos. Às vezes um deles fica esquecido, vence, e ninguém sabe se foi pago.

**Solução.** Cada conta tem um espaço, um responsável pelo pagamento, um vencimento e um status sempre visível. O sistema lê os dados do boleto ou do Pix, gera as contas recorrentes todo mês, avisa antes e depois do vencimento e registra o comprovante.

**Objetivos mensuráveis do MVP**

- Nenhuma conta da família vence sem aviso ao pagador e ao criador.
- Cadastrar uma conta a partir da linha digitável em menos de 30 segundos.
- Todo mês, saber quais contas recorrentes ainda não tiveram o boleto cadastrado.

**Visão de longo prazo.** Evoluir para um gestor financeiro pessoal, com receitas, carteiras, orçamento por categoria e relatórios. O modelo de dados já nasce baseado em lançamentos financeiros para permitir essa evolução.

## 2. Atores e personas

O sistema tem quatro atores humanos e um ator de sistema; o papel vale por grupo, então a mesma pessoa pode ser admin num grupo e pagador em outro.

| Ator | Quem é no cenário | O que faz |
| --- | --- | --- |
| Usuário | Qualquer pessoa com conta no Varal | Gerencia o espaço pessoal, cria grupos e aceita convites |
| Admin do grupo | O estudante ou o pai | Configura o grupo, subgrupos, membros e papéis; faz tudo que o membro faz |
| Membro | Alguém que ajuda a organizar | Cria, edita e paga contas do grupo |
| Pagador | A mãe ou o pai | Vê só as contas atribuídas a ele e as marca como pagas |
| Observador | Alguém que só acompanha | Vê as contas, sem alterar nada |
| Sistema (agendador) | Tarefas automáticas do backend | Gera recorrências, calcula lembretes e envia avisos |

**Personas**

- **Estudante e estagiário:** mora longe dos pais, organiza as contas da família pelo celular. Quer ver de longe se algo venceu.
- **Pai, administra 3 casas:** recebe muitos boletos. Precisa saber o que vence e marcar o que pagou com pouco esforço.
- **Mãe, pagadora:** paga parte das contas. Usa o modo simples: copiar o código e tocar em "Já paguei".

## 3. Escopo do MVP

O MVP resolve o acompanhamento das contas da família com o mínimo de digitação possível sem OCR: PDF do boleto, linha digitável, Pix copia e cola, recorrência e lembretes por push e e-mail.

**Dentro do MVP**

- Cadastro, login (e-mail e senha ou Google) e espaço pessoal criado automaticamente.
- Grupos com convite por link, papéis e subgrupos (casas).
- Contas pelo PDF do boleto, com leitura automática de código, valor, data de emissão e vencimento; pela linha digitável; por Pix (chave ou copia e cola); ou manual.
- Status, recorrência mensal e aviso de boleto que não chegou.
- Lembretes por push (PWA) e e-mail.
- Baixar o PDF do boleto ou copiar o código; marcar como paga, comprovante e histórico.
- Solicitação de pagamento do espaço pessoal para um grupo.
- Modo simples para pagadores.

**Fora do MVP**

| Item | Quando entra |
| --- | --- |
| Leitura de foto do boleto e de PDF escaneado (OCR) | v2 |
| Lembretes e "Já paguei" pelo WhatsApp | v2 |
| Leitura automática do comprovante | v2 |
| Resumo mensal por casa | v2 |
| Receitas, carteiras, orçamento e relatórios | v3 |
| Importação de extrato bancário | v3 |
| Pagamento de contas pelo próprio app | Sem previsão |
| App nativo nas lojas | Sem previsão; o MVP é PWA |

## 4. Requisitos funcionais

Vinte e cinco requisitos, agrupados por módulo; "Essencial" é obrigatório para o lançamento do MVP, e "Importante" pode ficar para uma versão 1.1.

| ID | Módulo | Requisito | Prioridade | Caso de uso |
| --- | --- | --- | --- | --- |
| RF01 | Conta de usuário | Cadastrar com e-mail e senha ou Google | Essencial | CU01 |
| RF02 | Conta de usuário | Criar o espaço pessoal no cadastro | Essencial | CU01 |
| RF03 | Conta de usuário | Recuperar senha por e-mail | Essencial | CU01 |
| RF04 | Grupos | Criar grupo; o criador vira admin | Essencial | CU02 |
| RF05 | Grupos | Convidar por link com papel definido | Essencial | CU03 |
| RF06 | Grupos | Alterar papel e remover membro | Essencial | CU03 |
| RF07 | Grupos | Criar, renomear e arquivar subgrupos | Essencial | CU04 |
| RF08 | Contas | Cadastrar conta pela linha digitável, com leitura de valor e vencimento | Essencial | CU05 |
| RF09 | Contas | Cadastrar conta Pix por chave ou copia e cola | Essencial | CU05 |
| RF10 | Contas | Cadastrar conta manual | Essencial | CU05 |
| RF11 | Contas | Definir espaço, subgrupo, pagador e visibilidade | Essencial | CU05 |
| RF12 | Contas | Editar e cancelar conta, com histórico | Essencial | CU07 |
| RF13 | Contas | Listar e filtrar por status, subgrupo, pagador e mês | Essencial | CU06 |
| RF14 | Contas | Copiar o código de pagamento com um toque | Essencial | CU08 |
| RF15 | Pagamento | Marcar como paga, com data | Essencial | CU08 |
| RF16 | Pagamento | Anexar comprovante (foto ou PDF) | Essencial | CU08 |
| RF17 | Pagamento | Desfazer pagamento | Importante | CU08 |
| RF18 | Recorrência | Criar conta recorrente mensal, de valor fixo ou variável | Essencial | CU09 |
| RF19 | Recorrência | Gerar as ocorrências do mês automaticamente | Essencial | CU12 |
| RF20 | Notificações | Enviar lembretes por push e e-mail | Essencial | CU12 |
| RF21 | Solicitação | Enviar conta pessoal para um grupo pagar | Importante | CU10 |
| RF22 | Pagador | Modo simples com "Copiar código" e "Já paguei" | Essencial | CU11 |
| RF23 | Contas | Enviar o PDF do boleto (até 5 MB) ao cadastrar a conta | Essencial | CU05 |
| RF24 | Contas | Ler do PDF o código de barras, o valor, a data de emissão, o vencimento e o beneficiário, e preenchê-los automaticamente | Essencial | CU05 |
| RF25 | Pagamento | Baixar o PDF do boleto anexado à conta | Essencial | CU08, CU11 |

## 5. Requisitos não funcionais

Privacidade entre espaços é o requisito mais crítico: um vazamento de conta pessoal para o grupo quebra a promessa do produto.

| ID | Categoria | Requisito |
| --- | --- | --- |
| RNF01 | Segurança | Toda consulta é filtrada por espaço, papel e visibilidade no backend; o front nunca recebe uma conta que o usuário não pode ver |
| RNF02 | Segurança | Senhas com hash (Argon2 ou PBKDF2), HTTPS em tudo, cookies `HttpOnly` e `Secure` |
| RNF03 | Segurança | Comprovantes e boletos servidos por URL assinada com validade curta |
| RNF04 | Privacidade | Exclusão da conta do usuário e exportação dos dados dele, conforme a LGPD |
| RNF05 | Desempenho | Tela inicial carregada em até 2 s numa rede 4G |
| RNF06 | Desempenho | Leitura e envio de PDF e de avisos sempre assíncronos, fora da requisição |
| RNF07 | Confiabilidade | Lembrete enviado no máximo 1 vez por evento, mesmo com reprocessamento (idempotência) |
| RNF08 | Usabilidade | Mobile-first, a partir de 360 px de largura; áreas de toque de no mínimo 44 px |
| RNF09 | Acessibilidade | Contraste mínimo de 4,5:1 no texto; status nunca indicado só por cor, sempre com ícone e texto |
| RNF10 | Instalação | PWA instalável, com notificações push |
| RNF11 | Dados | Valores em centavos (inteiro); datas no fuso America/Fortaleza na exibição e em UTC no banco |
| RNF12 | Manutenção | Contrato da API em OpenAPI, com tipos do front gerados a partir dele |

## 6. Casos de uso

Doze casos de uso cobrem o MVP; o Membro concentra o trabalho do dia a dia, e o Sistema garante os avisos sem depender de ninguém.

&#91;embedded content: atores e casos de uso · 5 atores, 12 casos de uso\]

No espaço pessoal, o dono tem as permissões de Membro e Admin ao mesmo tempo. As regras citadas (RN) estão na seção 7.

### CU01 — Cadastrar-se e entrar

- **Ator:** Usuário. **Pré-condição:** nenhuma.
- **Fluxo principal:**
  1. O usuário escolhe e-mail e senha ou Google.
  2. O sistema valida os dados e cria a conta.
  3. O sistema cria o espaço pessoal e abre o Início.
- **Alternativos:** e-mail já cadastrado → oferece entrar ou recuperar a senha. Chegou por convite → após o cadastro, entra direto no grupo (CU03).
- **Pós-condição:** usuário autenticado com espaço pessoal. **RN:** RN03.

### CU02 — Criar grupo

- **Ator:** Usuário. **Pré-condição:** autenticado.
- **Fluxo principal:**
  1. O usuário informa o nome do grupo.
  2. Opcionalmente, cria os primeiros subgrupos (ex.: Casa 1, Casa 2, Casa 3).
  3. O sistema cria o grupo com o usuário como admin e oferece o link de convite.
- **Pós-condição:** grupo ativo com um admin. **RN:** RN04.

### CU03 — Gerenciar membros

- **Ator:** Admin. **Pré-condição:** grupo existente.
- **Fluxo principal:**
  1. O admin gera um convite escolhendo o papel (Admin, Membro, Pagador ou Observador).
  2. O convidado abre o link, entra ou se cadastra e aceita.
  3. O sistema adiciona o membro com o papel do convite.
- **Alternativos:** convite expirado ou já usado → pede um novo. Alterar papel ou remover membro → o sistema bloqueia se o grupo ficaria sem admin.
- **Pós-condição:** membro no grupo com papel definido. **RN:** RN04, RN05, RN21, RN24.

### CU04 — Gerenciar subgrupos

- **Ator:** Admin. **Pré-condição:** grupo existente.
- **Fluxo principal:** criar, renomear ou arquivar um subgrupo.
- **Alternativos:** arquivar subgrupo com contas pendentes → o sistema pede para mover as contas ou confirmar que elas ficam sem subgrupo.
- **Pós-condição:** subgrupos disponíveis no filtro e no cadastro de contas.

### CU05 — Cadastrar conta

- **Ator:** Membro (ou dono, no pessoal). **Pré-condição:** espaço selecionado.
- **Fluxo principal:**
  1. O usuário escolhe: enviar o PDF do boleto, colar o código, Pix ou digitar.
  2. O sistema lê o PDF ou o código, valida e preenche código, valor, data de emissão, vencimento e beneficiário.
  3. O usuário confere e informa descrição, subgrupo, pagador, categoria e visibilidade.
  4. Opcionalmente, marca "Repetir todo mês" (segue para CU09).
  5. O sistema salva e agenda os lembretes.
- **Alternativos:** código inválido → mostra o erro e mantém o campo. Boleto de concessionária → pede o vencimento. Pix dinâmico sem valor → pede o valor. PDF sem texto ou sem código válido → guarda o arquivo e pede para colar o código.
- **Pós-condição:** conta Pendente no espaço. **RN:** RN01, RN06, RN08 a RN11, RN25 a RN28.

### CU06 — Consultar contas

- **Ator:** Membro, Admin, Observador ou Pagador. **Pré-condição:** autenticado.
- **Fluxo principal:**
  1. O usuário escolhe o espaço no topo.
  2. O Início mostra vencidas, que vencem em até 3 dias e aguardando boleto, com o total do mês.
  3. Na lista, filtra por status, subgrupo, pagador e mês.
- **Pós-condição:** nenhuma alteração. **RN:** RN02, RN06, RN07, RN12, RN13.

### CU07 — Editar ou cancelar conta

- **Ator:** Membro ou Admin (o Pagador não edita). **Pré-condição:** conta não cancelada.
- **Fluxo principal:**
  1. O usuário abre o detalhe e toca em Editar.
  2. Altera os campos e salva.
  3. O sistema registra a mudança no histórico e reagenda os lembretes se o vencimento mudou.
- **Alternativos:** Cancelar → pede confirmação e marca como Cancelada. Conta de recorrência → pergunta se a mudança vale só para este mês ou para os próximos.
- **Pós-condição:** conta atualizada ou cancelada. **RN:** RN22.

### CU08 — Pagar conta

- **Ator:** Pagador, Membro ou Admin. **Pré-condição:** conta Pendente (inclui vence em breve e vencida).
- **Fluxo principal:**
  1. O usuário toca em "Copiar código" ou "Baixar PDF" e paga no app do banco, fora do Varal.
  2. Volta e toca em "Marcar como paga", informando a data.
  3. Opcionalmente, anexa a foto ou o PDF do comprovante.
  4. O sistema muda o status e avisa o criador da conta.
- **Alternativos:** desfazer pagamento → só quem marcou ou um admin; o status volta a ser calculado pela data.
- **Pós-condição:** conta Paga, ou Confirmada se houver comprovante. **RN:** RN14 a RN16, RN29.

### CU09 — Configurar recorrência

- **Ator:** Membro ou Admin. **Pré-condição:** espaço selecionado.
- **Fluxo principal:**
  1. O usuário informa descrição, dia de vencimento, subgrupo e pagador.
  2. Escolhe valor fixo (ex.: aluguel) ou variável (ex.: luz).
  3. O sistema salva o modelo e gera a ocorrência do mês atual.
- **Alternativos:** pausar ou encerrar a recorrência → as ocorrências já geradas continuam.
- **Pós-condição:** modelo ativo. **RN:** RN17, RN18, RN23.

### CU10 — Solicitar pagamento

- **Ator:** Usuário (dono do espaço pessoal). **Pré-condição:** conta pessoal pendente e participação em pelo menos um grupo.
- **Fluxo principal:**
  1. No detalhe da conta pessoal, toca em "Pedir para alguém pagar".
  2. Escolhe o grupo e o pagador, e pode deixar uma mensagem.
  3. O sistema cria a solicitação no grupo e avisa o pagador.
- **Pós-condição:** a conta aparece no grupo; quando paga lá, a original fica Paga no pessoal. **RN:** RN20.

### CU11 — Usar o modo simples

- **Ator:** Pagador. **Pré-condição:** papel de Pagador em algum grupo.
- **Fluxo principal:**
  1. Ao entrar, o pagador vê só a lista do que pagar, ordenada por vencimento.
  2. Toca em "Copiar código" ou "Baixar PDF" e paga no banco.
  3. Toca em "Já paguei" e, se quiser, tira foto do comprovante.
- **Pós-condição:** igual ao CU08. **RN:** RN07, RN14, RN15.

### CU12 — Gerar recorrências e lembretes

- **Ator:** Sistema (agendador). **Gatilho:** execução diária às 7h (America/Fortaleza).
- **Fluxo principal:**
  1. Gera as ocorrências das recorrências que entram no mês.
  2. Identifica recorrências variáveis ainda sem boleto a 5 dias do vencimento.
  3. Calcula os lembretes do dia (3 dias antes, no dia e 1 dia depois).
  4. Envia por push e e-mail e registra cada envio.
- **Alternativos:** falha no envio → tenta de novo até 3 vezes, sem duplicar o aviso.
- **Pós-condição:** ocorrências criadas e lembretes enviados uma única vez. **RN:** RN17 a RN19.

## 7. Regras de negócio

Vinte e nove regras; as de espaço e visibilidade (RN01 a RN07) valem para toda consulta e toda escrita da API.

### Espaços, grupos e permissões

| ID | Regra |
| --- | --- |
| RN01 | Toda conta pertence a exatamente um espaço (pessoal ou grupo) e nunca aparece em outro. |
| RN02 | Uma conta do espaço pessoal só é vista pelo dono do espaço. |
| RN03 | Cada usuário tem um único espaço pessoal, criado no cadastro, que não aceita membros. |
| RN04 | Todo grupo tem pelo menos um admin; a última remoção ou rebaixamento de admin é bloqueada. |
| RN05 | Permissões por papel: Admin faz tudo; Membro cria, edita e paga; Pagador só paga as dele; Observador só vê. |
| RN06 | Conta com visibilidade restrita só é vista pelo criador, pelo pagador e pelos membros escolhidos. |
| RN07 | O Pagador só vê as contas em que é o pagador. |

### Cadastro de contas

| ID | Regra |
| --- | --- |
| RN08 | A linha digitável só é aceita se os dígitos verificadores (módulo 10 e 11) forem válidos. |
| RN09 | Boleto bancário (47 dígitos): valor e vencimento vêm do código; o fator de vencimento reiniciou em 22/02/2025 e o cálculo trata o ciclo novo. |
| RN10 | Boleto de concessionária (48 dígitos, começa com 8): o valor vem do código e o vencimento é informado pelo usuário. |
| RN11 | O valor deve ser maior que zero e é guardado em centavos. |

### Leitura do PDF do boleto

| ID | Regra |
| --- | --- |
| RN25 | Só arquivos PDF de até 5 MB. O PDF fica guardado e ligado à conta; trocar o arquivo refaz a leitura. |
| RN26 | A leitura usa o texto do PDF e procura a linha digitável (47 ou 48 dígitos, com ou sem pontos e espaços), validada pela RN08. |
| RN27 | Valor e vencimento vêm do código quando ele os traz (RN09). Do texto do PDF vêm a data de emissão ("Data do documento"), o vencimento de boletos de concessionária e o beneficiário. |
| RN28 | Se o texto do PDF divergir do código, vale o código e o usuário é avisado na conferência. PDF escaneado ou sem código válido é aceito e o usuário cola o código; leitura por OCR fica para a v2. |
| RN29 | Quem vê a conta pode baixar o PDF e copiar o código; o download usa link assinado de curta validade (RNF03). |

### Status e pagamento

&#91;embedded content: ciclo de status da conta · 6 estados + Cancelada\]

| ID | Regra |
| --- | --- |
| RN12 | Ficam gravados Aguardando boleto, Pendente, Paga, Confirmada e Cancelada; "Vence em breve" e "Vencida" são calculados pela data na consulta. |
| RN13 | "Vence em breve" vale nos 3 dias antes do vencimento; o admin pode mudar para 1 a 7 dias no grupo. |
| RN14 | Marcar como paga exige a data do pagamento, que não pode ser futura. |
| RN15 | Uma conta Paga com comprovante anexado passa a Confirmada. |
| RN16 | Só quem marcou o pagamento ou um admin pode desfazê-lo. |

### Recorrência e lembretes

| ID | Regra |
| --- | --- |
| RN17 | A recorrência gera a ocorrência no primeiro dia do mês: de valor fixo nasce Pendente, de valor variável nasce Aguardando boleto. |
| RN18 | Se faltarem 5 dias para o vencimento e o boleto não tiver chegado, o criador e o pagador são avisados. |
| RN19 | Lembretes ao pagador 3 dias antes e no dia; 1 dia depois, sem pagamento, também ao criador e aos admins. Cada lembrete é enviado no máximo uma vez. |
| RN23 | Dia de vencimento 29, 30 ou 31 em um mês mais curto passa para o último dia desse mês. |

### Solicitação, saída e histórico

| ID | Regra |
| --- | --- |
| RN20 | A solicitação cria uma cópia no grupo ligada à original; pagar no grupo marca a original como Paga, e cancelar a original cancela a cópia. |
| RN21 | Quem sai do grupo deixa as contas que criou; as contas em que era pagador ficam sem pagador e o admin é avisado. |
| RN22 | Cancelar não apaga: a conta fica Cancelada, e toda alteração vai para o histórico com autor e data. |
| RN24 | O convite expira em 7 dias e pode ser usado uma vez. |

## 8. Modelo de dados

A entidade central é o **lançamento**: no MVP todo lançamento é uma despesa, e a v3 passa a usar receitas sem mudar a estrutura.

```
usuario            id, nome, email, telefone, prefs_notificacao
espaco             id, tipo (pessoal|grupo), nome, dono_id, janela_alerta_dias
membro             espaco_id, usuario_id, papel (admin|membro|pagador|observador)
convite            id, espaco_id, papel, token, expira_em, usado_por?
subgrupo           id, espaco_id, nome, arquivado
categoria          id, espaco_id?, nome, tipo (despesa|receita)

lancamento         id, espaco_id, subgrupo_id?, categoria_id?,
                   criador_id, pagador_id?, tipo (despesa|receita),
                   descricao, valor_centavos, vencimento,
                   status (aguardando|pendente|paga|confirmada|cancelada),
                   visibilidade (grupo|restrita), recorrencia_id?,
                   origem_id?                       -- solicitação: aponta para a conta pessoal
lancamento_acesso  lancamento_id, usuario_id        -- quem vê uma conta restrita
instrumento        lancamento_id, tipo (boleto_bancario|boleto_arrecadacao|pix|manual),
                   codigo, data_emissao?, pdf_url?, chave_pix?, beneficiario?
recorrencia        id, espaco_id, descricao, dia, valor_tipo (fixo|variavel),
                   valor_centavos?, subgrupo_id?, pagador_id?, ativa
pagamento          id, lancamento_id, pago_em, valor_pago_centavos,
                   marcado_por, comprovante_url?
historico          id, lancamento_id, usuario_id, acao, dados (jsonb), criado_em
notificacao        id, usuario_id, lancamento_id, tipo, canal, agendada_para,
                   enviada_em?, chave_idempotencia (única)
```

- **Centavos em inteiro**, nunca `float`.
- **Pagamento separado do lançamento:** permite pagamento parcial e, na v3, ligar o pagamento a uma carteira.
- **Instrumento separado:** novos meios de pagamento entram sem mexer em `lancamento`.
- **`chave_idempotencia` única** em `notificacao` garante RN19 e RNF07.
- **UUID** como chave em tudo; índice em `(espaco_id, vencimento)`.

## 9. Arquitetura, stack e repositório

**Django + DRF + Celery no backend e Next.js no front**, num monorepo, rodando em Docker Compose na VPS. O ecossistema Python é mais forte em leitura de documentos, tarefas agendadas e, na v3, relatórios financeiros.

&#91;embedded content: arquitetura do MVP · 7 componentes\]

A API nunca espera a leitura de um PDF nem o envio de um aviso: ela enfileira a tarefa e responde na hora. O Celery beat dispara a rotina diária do CU12.

| Camada | Tecnologia |
| --- | --- |
| Backend | Django, Django REST Framework, drf-spectacular (OpenAPI), django-allauth headless |
| Tarefas | Celery, Celery beat, Redis |
| Banco | PostgreSQL |
| Leitura de boleto e Pix | Parser próprio da linha digitável (Febraban) e do BR Code (EMV); pdfplumber no MVP para PDF com texto; OCR na v2 |
| Front | Next.js (App Router), TanStack Query, openapi-typescript, PWA com Web Push |
| Arquivos | Armazenamento compatível com S3 (MinIO na VPS) |
| Deploy | Docker Compose: API, worker, beat, Postgres, Redis e Next |

### Repositório

```
varal/
├── api/              # Django + DRF + Celery
├── web/              # Next.js
│   └── src/types/api.ts   # gerado do OpenAPI
├── infra/            # docker-compose, nginx, .env.example
├── docs/             # este documento, ADRs
├── Makefile          # make dev, make types, make test
└── .github/workflows/
    ├── api.yml       # roda só se api/** mudar
    └── web.yml       # roda só se web/** mudar
```

- `make types` gera os tipos do front a partir do OpenAPI; o CI falha se o tipo gerado diferir do commitado.
- Sem Turborepo nem Nx: só o `web/` é JavaScript.

## 10. Identidade visual

O logo aprovado é a opção 1, "Contas no varal": três contas penduradas nas cores dos status, com o nome em Bricolage Grotesque. As cores das contas no logo são as mesmas dos status no app, então a marca já ensina a ler a interface.

### Logo

- **Versões:** horizontal (símbolo + nome), símbolo sozinho, fundo claro e fundo escuro (fio e prendedores em branco).
- **Ícone de app:** símbolo branco sobre azul-marinho `#1C2541`, cantos de 22% do lado.
- **Favicon:** versão simplificada, sem prendedores e com o fio mais grosso.
- **Respiro mínimo:** a altura de uma conta do símbolo em todos os lados. **Tamanho mínimo:** símbolo com 24 px de largura.
- **Não fazer:** trocar a ordem ou as cores das contas, girar o fio, aplicar sombra ou degradê.

### Paleta

| Token | Hex | Uso |
| --- | --- | --- |
| `ink-900` | `#1C2541` | Marca, texto principal, botão primário, fundo do ícone de app |
| `ink-600` | `#4A5372` | Texto secundário e ícones inativos |
| `ink-400` | `#8A91A8` | Placeholder e desabilitado (nunca em texto que precisa ser lido) |
| `line` | `#E3E6EC` | Bordas e divisores |
| `bg` | `#F6F7F9` | Fundo do app |
| `surface` | `#FFFFFF` | Cards, folhas e campos |
| `amber-500` | `#F5A524` | Prendedor, destaques e ícone de "vence em breve" |
| `amber-text` / `amber-50` | `#9A5B00` / `#FEF4E2` | Texto e fundo do selo "Vence em breve" |
| `red-500` | `#E5484D` | Ícone de vencida e ações destrutivas |
| `red-text` / `red-50` | `#B42318` / `#FDECEC` | Texto e fundo do selo "Vencida" |
| `green-600` | `#1F9D6B` | Paga, confirmada e sucesso |
| `green-text` / `green-50` | `#12704B` / `#E6F4EE` | Texto e fundo dos selos "Paga" e "Confirmada" |
| `neutral-50` | `#EEF0F4` | Fundo dos selos "Pendente" e "Aguardando boleto" |

Status nunca é indicado só por cor: todo selo tem ícone e texto (RNF09).

### Tipografia

Duas famílias do Google Fonts: **Bricolage Grotesque**, a mesma do logo, para títulos e valores em destaque, e **Inter** para a interface e o texto corrido.

| Estilo | Família | Peso | Tamanho / linha | Uso |
| --- | --- | --- | --- | --- |
| Display | Bricolage Grotesque | 800 | 32 / 38 px, espaçamento -2% | Títulos de destaque e mensagens de sucesso |
| Título 1 | Bricolage Grotesque | 700 | 24 / 30 px | Título de tela |
| Título 2 | Bricolage Grotesque | 700 | 18 / 24 px | Título de seção |
| Título de card | Inter | 600 | 16 / 22 px | Descrição da conta |
| Corpo | Inter | 400 | 15 / 22 px | Texto geral |
| Corpo forte | Inter | 600 | 15 / 22 px | Botões e ênfase |
| Valor em lista | Inter | 600 | 16 / 22 px, números tabulares | Valores em listas e cards |
| Pequeno | Inter | 500 | 13 / 18 px | Vencimento, casa, pagador |
| Rótulo | Inter | 600 | 12 / 16 px, maiúsculas, +4% | Selos de status e rótulos de seção |

### Espaços e formas

- **Espaçamento:** múltiplos de 4 (4, 8, 12, 16, 24, 32 px); margem lateral das telas de 20 px.
- **Raios:** 8 px em selos, 12 px em campos, 20 px em cards, 28 px no bloco de destaque e nas folhas inferiores; botões e filtros em pílula.
- **Toque:** botões com 52 px de altura; nenhum alvo menor que 44 px.
- **Sombra:** só na barra inferior e em folhas que sobem; cards usam borda `line`.

### Referência visual e movimento

A interface segue o [UGLYCASH](https://onepagelove.com/uglycash): números enormes, cards brancos bem arredondados sobre fundo cinza, botões em pílula e um único bloco de cor forte por tela (o azul-marinho do topo do Início). O total do mês e o valor no detalhe usam um **número-herói** de 48 px em Bricolage 800, com os centavos em 24 px e 55% de opacidade.

O varal com as contas é o motivo da marca dentro do app: aparece no resumo do Início, no Detalhe e na confirmação de pagamento, quando a conta "sai do varal".

| Animação | Onde | Especificação |
| --- | --- | --- |
| Balanço (`swing`) | Contas penduradas | Rotação de ±5° a ±7°, 3 a 3,6 s, infinita, origem no topo, atrasos diferentes por conta |
| Entrada (`rise`) | Cards e listas | Sobe 14 px e aparece em 0,5 s, com 80 ms entre itens |
| Barra do mês (`grow`) | Progresso de pagas | Largura de 0 ao valor em 1,4 s |
| Contagem | Total do mês | De 0 ao valor em 1,2 s, desacelerando |
| Folha (`sheet-up`) | Nova conta, pagamento, convite | Sobe de baixo em 0,5 s |
| Sucesso (`pop` + traço) | Conta paga | Círculo cresce com leve rebote e o check é desenhado |
| Pulso | Ícone do selo Vencida | Escala de 1 para 1,18 a cada 1,8 s |
| Toque | Botões e filtros | Encolhe para 97% ao pressionar |

Toda animação é desligada quando o sistema pede movimento reduzido (`prefers-reduced-motion`).

## 11. Iconografia

Os ícones são próprios e seguem o traço do logo: grade de 24 × 24 px, linha de 2 px com pontas e cantos arredondados, em `ink-900`. Cor só aparece nos ícones de status, sempre acompanhados de texto. Os desenhos estão no canvas do Doop (seção 12), na prancheta "Ícones", como o componente \`Icon\` (prop \`name\`). Além dos 24 da tabela, há \`chevron\` e \`fechar\` para navegação, além de pdf, baixar e enviar, usados no boleto em PDF.

| Nome no código | Desenho | Onde aparece |
| --- | --- | --- |
| `varal` | Fio com uma conta pendurada | Aba Início |
| `contas` | Lista de contas | Aba Contas |
| `grupo` | Duas pessoas | Aba Grupos |
| `perfil` | Uma pessoa | Aba Perfil |
| `boleto` | Documento com código de barras | Tipo de conta e colar código |
| `pix` | QR code estilizado | Tipo de conta Pix (não reproduz a marca Pix) |
| `manual` | Lápis | Tipo de conta manual |
| `casa` | Casa | Subgrupo |
| `calendario` | Calendário | Vencimento |
| `repetir` | Duas setas em círculo | Conta recorrente |
| `cadeado` | Cadeado | Visibilidade restrita |
| `sino` | Sino | Notificações |
| `prendedor` | Prendedor de roupa | Aguardando boleto |
| `pendente` | Círculo vazio | Status Pendente |
| `relogio` | Relógio, em âmbar | Status Vence em breve |
| `alerta` | Círculo com exclamação, em vermelho | Status Vencida |
| `pago` | Círculo com check, em verde | Status Paga |
| `comprovante` | Canhoto com check, em verde | Status Confirmada e anexo |
| `copiar` | Duas folhas | Copiar código |
| `camera` | Câmera | Foto do comprovante |
| `pedir` | Seta saindo de uma caixa | Solicitar pagamento |
| `mais` | Sinal de mais | Nova conta |
| `filtro` | Funil | Filtros da lista |
| `voltar` | Seta para a esquerda | Navegação |

No código, os ícones devem virar componentes SVG com `stroke="currentColor"`, para herdar a cor do texto, e `aria-hidden="true"` quando acompanham um texto.

## 12. Telas

As 13 telas do MVP estão no canvas [Varal no Doop](https://doop.design/c/k0kB5dc-Vo), em 390 × 844 px, montadas com componentes e tokens; é dali que o código deve ser gerado.

**Organização do canvas**

- [01 · Marca e ícones](https://doop.design/c/k0kB5dc-Vo?page=k0kB5dc-Vo:page1): logo, paleta, tipografia e ícones.
- [02 · Telas mobile](https://doop.design/c/k0kB5dc-Vo?page=-eLoZ0SLb1): as 13 telas em 390×844, em três linhas por fluxo.
- [03 · Telas desktop](https://doop.design/c/k0kB5dc-Vo?page=YGk9_iqJ-Y): 5 telas em 1440×900, 6 janelas (modais) e a gaveta de avisos.
- [04 · Componentes](https://doop.design/c/k0kB5dc-Vo?page=page-mwdwblpn): os 16 componentes, cada um com o caminho no código (`web/src/components/...`).
- Guia **Varal · regras de interface** fixado no canvas: tokens, status e especificação das animações.

| Nº | Tela | Casos de uso | Destaque |
| --- | --- | --- | --- |
| 01 | Entrar | CU01 | Contas caem no varal ao abrir; folha de login sobe |
| 02 | Início | CU06 | Total do mês com contagem, barra de pagas e o resumo como contas balançando no varal |
| 03 | Contas | CU06 | Filtros por status, mês e grupos por prazo |
| 04 | Avisos | CU12 | Avisos por tipo, com ponto de não lido |
| 05 | Nova conta | CU05, CU09 | Área "Enviar PDF do boleto" com borda animada; colar código, digitar e recorrente |
| 06 | Conferir conta | CU05, RN25 a RN28 | PDF lido: código, valor, emissão, vencimento e beneficiário preenchidos e marcados com a origem |
| 07 | Detalhe da conta | CU07, CU08 | A conta pendurada balança; copiar o código ou baixar o PDF; data de emissão; histórico |
| 08 | Marcar como paga | CU08 | Data e comprovante opcional |
| 09 | Conta paga | CU08 | A conta sai do varal e o check é desenhado |
| 10 | Grupo | CU02, CU03, CU04, CU09 | Casas com progresso, membros e papéis, recorrentes |
| 11 | Convidar membro | CU03, RN24 | Escolha do papel e link de uso único |
| 12 | Pedir para alguém pagar | CU10, RN20 | Do pessoal para o grupo, só esta conta |
| 13 | Modo simples | CU11 | Ações grandes por conta: Copiar, Já paguei e Baixar boleto em PDF |

**Telas desktop**

A partir de 1024px, a barra inferior dá lugar a um menu lateral fixo (SideNav, 264px) com logo, seletor de espaço, botão Nova conta e usuário. As folhas inferiores viram janelas centralizadas, e Contas e Detalhe ficam lado a lado.

| Nº | Tela | Equivale a | Destaque |
| --- | --- | --- | --- |
| D01 | Entrar | 01 | Bloco azul com as contas no varal à esquerda, login à direita |
| D02 | Início | 02, 04 | Total do mês com o varal grande, contas que pedem atenção, progresso por casa e avisos recentes |
| D03 | Contas + Detalhe | 03, 07 | Lista com filtros à esquerda e a conta aberta à direita, com Copiar, Baixar PDF e histórico |
| D04 | Grupo | 10 | Casas, membros e papéis, recorrentes em colunas |
| D05 | Modo simples | 13 | Contas do pagador em cards grandes, com Copiar, Já paguei e Baixar PDF |
| D06 | Avisos | 04 | Gaveta lateral de 440px aberta pelo sino |
| M01 | Nova conta | 05 | Janela com a área de enviar PDF e as outras formas |
| M02 | Conferir conta | 06 | Prévia do PDF ao lado dos campos, com os dados lidos destacados |
| M03 | Marcar como paga | 08 | Data e comprovante opcional |
| M04 | Conta paga | 09 | Check desenhado e a conta saindo do varal |
| M05 | Convidar membro | 11 | Papel e link de uso único |
| M06 | Pedir para alguém pagar | 12 | Escolha do grupo e de quem paga |

As telas ainda não estão ligadas como protótipo clicável; os botões indicam a navegação prevista.

## 13. Roadmap

O MVP resolve as contas da família; a v2 tira o trabalho de digitar, e a v3 transforma o Varal em gestor financeiro. Cada fase só começa quando a anterior atinge a meta.

| Fase | Foco | Entregas | Meta para avançar |
| --- | --- | --- | --- |
| MVP | Contas da família em dia | RF01 a RF25 | Um mês sem conta vencida sem aviso |
| v2 | Menos digitação | Leitura de foto e de PDF escaneado (OCR), WhatsApp, comprovante lido sozinho, resumo do mês por casa | Cadastrar a maioria das contas sem digitar |
| v3 | Gestor financeiro pessoal | Receitas, carteiras e bancos, orçamento por categoria, relatórios, importação de extrato | Ver o mês inteiro, entradas e saídas |
