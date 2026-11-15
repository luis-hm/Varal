# Requisitos funcionais

> **Contém:** RF01–RF25, com módulo, prioridade e caso de uso.
> **Origem:** `docs/especificacao-varal.md`, seção 4.

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
