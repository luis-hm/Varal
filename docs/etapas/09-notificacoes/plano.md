# Plano — Etapa 09 (Notificações)

> **Contém:** sequência de execução, dados e contratos implementados da central e dos transportes.
> **Origem:** [spec](spec.md), [Q09-1–9 e D09-1](decisoes.md), ADR 0011–0013 e implementação final das Etapas 07/08.

## Ordem e responsabilidade

Abertura/triagem concluídas após merge local da 08. Backend implementa domínio, migrações, API e outbox; DevOps prepara configuração local/transportes e coordena variáveis sem exibir segredos. Depois do schema, gerar tipos e integrar frontend. Frontend lê guia e recursos atuais do Doop por nome 04/D06, 02/D02 e NoticeRow; leitura identificada da abertura foi fornecida pelo orquestrador, sem alegar leitura própria. QA valida CA01–CA14, segurança revisa privacidade/transportes/PWA, decisor audita e docs consolida relatório/PROGRESSO; matriz é do QA.

## Dados implementados

- Evento de notificação com chave de origem única: lembrete conta/fase, pagamento UUID de EventoPagamento, RN21/P7 UUID de histórico. Não substituir o outbox da 07 por reconstrução de pagamentos.
- Notificação única por evento/destinatário: lido, revogação terminal e conteúdo mínimo P7 quando necessário. Conteúdo comum é projeção autorizada atual, sem snapshot financeiro liberado a ex-membro.
- Entrega única por aviso/canal, com reserva/lease, tentativa iniciada persistida, aceitação, falha, descarte ou incerteza. Filhos push únicos por inscrição congelam dispositivos elegíveis; aceito/incerto nunca volta à fila automaticamente.
- Inscrição push própria com endpoint único protegido e chaves validadas. Checkpoint/versionamento de ativação/importação persistidos. Nomes e campos implementados estão no [modelo](../../dados/modelo.md#implementação-da-etapa-09).

Eventos/materialização são transacionais; rede fica fora da transação. Revalidar antes da reserva e junto do envio, sem prometer atomicidade banco/provedor. Até três tentativas totais, inicial e retries após 1 min/5 min, só para falha recuperável comprovada. Mensagem física já aceita não pode ser recolhida; payload externo é genérico.

## Contratos implementados

Sessão autenticada e CSRF nas escritas. Rotas e payloads constam na [API](../../api/README.md#notificações-etapa-09) e tipos gerados; sem DTO paralelo.

| Operação | Guarda/efeito |
| --- | --- |
| Listar central com cursor/limite | Página estável, somente avisos próprios atualmente autorizados, contador do mesmo universo |
| Resumo da central | Recentes e não lidos por projeção/autorização comum; quantidade conforme referência visual, sem inventar cards |
| Marcar um como lido | Idempotente, timestamp estável; alheio/revogado/invisível não é exposto |
| Marcar todos como lidos | Q09-9: todos os próprios autorizados, inclusive fora da página; segunda chamada não cria evento nem altera timestamps marcados |
| Ler/alterar preferências | Versão e booleanos email/push, sem e-mail/endpoints; não cria Perfil |
| Configuração pública de push | Somente habilitação/chave pública VAPID |
| Criar/revogar inscrição própria | Validação de endpoint/chaves; conflito de outro usuário não transfere vínculo; logout revoga servidor antes de encerrar sessão |

Sem endpoint cliente de disparo. Links externos usam rota fixa autenticada da central; SW não aceita destino livre ou cache de dados privados. Respostas e logs não expõem endpoint, chaves ou dados financeiros.

## Integrações e validação prevista

D09-1: um fluxo diário às 07:00 America/Fortaleza executa geração/recuperação da 08 antes dos avisos da 09. Dispatcher operacional cuida de pendências/retries; manutenção de comprovantes a cada 300 s permanece separada. Eventos imediatos são assíncronos; consumo de EventoPagamento termina só após materialização idempotente ou descarte motivado.

Consumir todos os pendentes da 07 sem corte temporal. Importar RN21/P7 por checkpoint persistido: anteriores à ativação só central, sem rajada externa. Novo P7 captura mínimo seguro no cancelamento; legado sem snapshot não consulta descrição atual. Revogação é terminal, sem ressuscitar por reingresso. Edição/pagamento/undo/saída reavaliam pendências preservando identidade de fase; lembretes recuperam somente no próprio dia-alvo a partir das 07:00.

Validar datas/fases, concorrência real, leases/crash/aceitação incerta, opt-out/dispositivos, SSR/CSRF/SSRF e central/P7 nas duas larguras. SMTP capturado e Web Push em navegador compatível exigem prova própria; indisponibilidade deve virar limite concreto no relatório, nunca sucesso por mock. Não implantar VPS ou antecipar a 10.

D09-2 exige revogação por UUID de instalação, tombstone causal e logout nativo com sessão terminal; DELETE por id de inscrição foi removido. D09-3 preserva tela/filtros/history na gaveta desktop pelo mesmo URL; acesso direto `/avisos` tem fundo Início. Frontend implementado e congelado, 111 Vitest/lint/tsc e 483 pytest na integral; E2E inicial 129/3/2 reprovado; suíte Playwright completa final 131/3 verde em serviços existentes verificados, sem declarar wrapper make e2e aprovado. Provas reais locais do transporte já ocorreram; limites e resultados no [relatório](relatorio.md).
