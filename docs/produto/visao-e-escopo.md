# Visão e escopo

> **Contém:** objetivo, problema, solução, MVP dentro/fora e roadmap.
> **Origem:** `docs/especificacao-varal.md`, seções 1, 3 e 13.

## 1. Objetivo do sistema

O Varal é um app web mobile-first para cadastrar e acompanhar contas (boletos e Pix) no espaço pessoal e em grupos familiares, para que nenhuma conta vença sem que alguém saiba.

**Problema.** Um estudante que trabalha como estagiário paga as próprias contas pequenas e repassa as maiores (aluguel, fatura, luz) para os pais pagarem. O pai administra 3 casas, com muitos boletos. Às vezes um deles fica esquecido, vence, e ninguém sabe se foi pago.

**Solução.** Cada conta tem um espaço, um responsável pelo pagamento, um vencimento e um status sempre visível. O sistema lê os dados do boleto ou do Pix, gera as contas recorrentes todo mês, avisa antes e depois do vencimento e registra o comprovante.

**Objetivos mensuráveis do MVP**

- Nenhuma conta da família vence sem aviso ao pagador e ao criador.
- Cadastrar uma conta a partir da linha digitável em menos de 30 segundos.
- Todo mês, saber quais contas recorrentes ainda não tiveram o boleto cadastrado.

**Visão de longo prazo.** Evoluir para um gestor financeiro pessoal, com receitas, carteiras, orçamento por categoria e relatórios. O modelo de dados já nasce baseado em lançamentos financeiros para permitir essa evolução.

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

## 13. Roadmap

O MVP resolve as contas da família; a v2 tira o trabalho de digitar, e a v3 transforma o Varal em gestor financeiro. Cada fase só começa quando a anterior atinge a meta.

| Fase | Foco | Entregas | Meta para avançar |
| --- | --- | --- | --- |
| MVP | Contas da família em dia | RF01 a RF25 | Um mês sem conta vencida sem aviso |
| v2 | Menos digitação | Leitura de foto e de PDF escaneado (OCR), WhatsApp, comprovante lido sozinho, resumo do mês por casa | Cadastrar a maioria das contas sem digitar |
| v3 | Gestor financeiro pessoal | Receitas, carteiras e bancos, orçamento por categoria, relatórios, importação de extrato | Ver o mês inteiro, entradas e saídas |
