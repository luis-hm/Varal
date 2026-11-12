# Requisitos não funcionais

> **Contém:** RNF01–RNF12 (segurança, privacidade, desempenho, usabilidade, dados).
> **Origem:** `docs/especificacao-varal.md`, seção 5.

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
