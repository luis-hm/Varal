# ADR 0010 — PDF assíncrono e conferência privada

> **Contém:** recepção, envio ao S3, extração limitada e vínculo seguro do PDF com a conta.
> **Origem:** RNF06, RN25–RN29, ADR 0002 e decisões delegadas do dono para executar as etapas restantes.

- **Status:** aceita por delegação (16/11/2026).

## Decisão

- A API recebe o multipart e faz somente validações baratas e spool em volume local privado compartilhado com o worker. Recepção e spool são transporte; **envio ao S3 e extração acontecem no Celery**, fora da requisição (RNF06). A requisição não espera S3 ou pdfplumber.
- Cada upload tem UUID, arquivo de staging e chave S3 próprios e imutáveis. O volume não é servido por HTTP. O worker usa apenas caminhos derivados desses identificadores, sem aceitar caminhos ou URLs do usuário.
- Extração executa em processo dedicado com limites explícitos de tempo/memória e saída estruturada validada. A configuração temporária de logging do extrator não é compartilhada com outras tarefas; nenhum texto do PDF ou erro com operandos é registrado.
- Antes do vínculo, acesso exige uploader e permissão atual no espaço/destino. Depois do vínculo, só vale o acesso à conta. Destino de edição não equivale a vínculo confirmado. Um documento antes vinculado nunca volta a draft legível pelo uploader.
- Confirmação vincula documento, instrumento e campos na transação da conta. Worker não altera a conta já salva; vários códigos exigem escolha explícita. PDF válido sem leitura/código permite conferência manual.
- Limites aprovados: 5 MiB por arquivo; leitura de até 20 páginas/200 mil caracteres com aviso e alternativa manual; URL assinada de 60 s; drafts sem vínculo expiram em 24 h. Tempo/memória do processo terão defaults e regressões registrados na implementação.
- Troca/remoção revoga o documento antigo. Limpeza de staging/S3 é idempotente e disparada após commit, com recuperação quando broker/storage falham. Rollback preserva o arquivo usado; tarefas antigas não atingem chaves novas.

## Consequências

API e worker precisam compartilhar o volume de staging e o armazenamento S3 privado. O worker valida texto fora do DRF antes de persistir JSONB. O endpoint público do S3 é usado ao assinar downloads, sem reescrever host após a assinatura. Storage de produção permanece na Etapa 11.
