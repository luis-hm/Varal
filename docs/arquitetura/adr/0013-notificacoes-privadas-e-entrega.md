# ADR 0013 — Central privada e entrega de notificações

> **Contém:** decisões de central privada, identidade dos avisos, transporte e revogação terminal.
> **Origem:** autorização expressa do dono e [Q09-1–9 e D09-1](../../etapas/09-notificacoes/decisoes.md). Não é resposta literal do dono nem alteração da especificação de origem.

**Status:** decidido por delegação em 16/11/2026; implementação concluída na Etapa 09.

## Contexto

RF20/CU12 exigem push/e-mail e repetição controlada; RNF07/RN19 exigem idempotência. Banco não pode provar entrega física única em SMTP/WebPush após timeout/crash. RN06/Q21 limitam destinatários pela visibilidade atual. ADR 0006/P7 exige avisar o removido sem reabrir conta/PDF ou sinalizar ao admin. EventosPagamento da 07 são duráveis; históricos antigos RN21/P7 precisam importação, e P7 não preserva descrição no formato atual.

## Decisão

1. Central única por evento/destinatário; outbox por canal e filho por inscrição. Lembrete identificado por conta/fase, nunca por revisão/vencimento; eventos da 07 e históricos usam UUID de origem. Revalidar envio/leitura/contador por audiência e estado atuais; revogação terminal. P7 tem acesso excepcional só ao aviso próprio.
2. Agenda às 07:00 em Fortaleza, recuperação somente até o fim do dia-alvo. Reagendar pendências sem reiniciar fase consumida. Mudança de pagador só habilita nova pessoa ainda elegível na janela. RN13 não modifica D−3. Sem pagador não inventa destinatário D−3/D0.
3. Três tentativas totais (inicial + 2, após 1 min/5 min), interpretação delegada de CU12. Lease/tentativa iniciada persistidos antes do I/O. Falha recuperável comprovada permite retry; aceitação desconhecida vira incerta sem retransmissão automática. Aceita não significa entregue/lida. Canais/dispositivos são independentes, comunicando esse limite honestamente.
4. P7 novo captura descrição/data/motivo no instante do cancelamento para o removido que via a conta. Sem valores, terceiros ou links. Legado sem snapshot usa descrição genérica, referência opaca do evento, data/motivo; nunca consulta descrição atual para enriquecer. Usuário excluído não recebe. Contadores/admin de grupo não expõem P7.
5. Consumir todos EventosPagamento da 07 pendentes sem corte por data, somente se marca/criador/acesso válidos. Importar RN21/P7 uma vez por id de Historico; legados anteriores à ativação da 09 ficam só central. RN21 exige conta aberta/sem pagador e admins atuais visíveis. Não reconstruir pagamento nem lembrete passado por histórico.
6. Preferências email/push versionadas default true; push só com gesto/permissão/inscrição. Central sempre disponível. Um endpoint por usuário, sem transferência automática por URL; logout revoga inscrição no servidor. Aparelho novo não recebe passado. Payload externo genérico, rota fixa autenticada, SW sem cache privado, VAPID privada restrita.
7. WebPush não aceita URL arbitrária: allowlist do servidor de hosts FCM/Mozilla/Apple homologados; HTTPS na porta 443, parse estrito, sem userinfo/IP/redirects. Resolver/revalidar IP público e fixar conexão com TLS/SNI, sem DNS rebinding ou proxy implícito; alternativamente egress proxy equivalente. Outros provedores aguardam homologação. Detalhes e fontes primárias estão em decisoes.md Q09-7.

8. Marcar todos como lidos alcança todos os avisos atualmente autorizados do próprio destinatário, inclusive fora da página carregada; operação autenticada/CSRF e idempotente. Avisos revogados/alheios não participam nem ressuscitam.
9. O único fluxo diário às 07:00 em Fortaleza executa geração/recuperação da 08 antes de calcular avisos da 09; não usar crontabs independentes em disputa. Manutenção de comprovantes a cada 300 s continua separada (D09-1).

## Consequências e reversão

Central garante registro lógico, sem prometer uma entrega física exata. Estado incerto pode resultar em ausência de push/e-mail; reenvio automático não é solução segura. Catch-up limitado perde fases de dias offline; P7 legado perde reconhecimento por descrição, preservando privacidade. Reversão exige migração de ledger/snapshots/preferências preservando consumidos; mensagens externas já vistas não se recolhem. Provedor novo exige validação de origem/transporte.

Derivados documentam a implementação; matriz e aprovação final dependem do QA. CA06 exige três tentativas totais. Não editar origem, implementar solicitação na 10 ou Perfil na 11, nem declarar envio externo validado por mocks. Doop deve ser lido antes da UI; deploy depende da autorização própria P11.

## Precisão da implementação — instalação e sessão

[D09-2](../../etapas/09-notificacoes/decisoes.md), refinamento de Q09-6 sob delegação, remove DELETE por id de inscrição: somente UUID da instalação permite criar tombstone antes da resposta/POST atrasado. Tombstones e sessão revogada impedem reativação por retry; logout nativo também revoga no servidor. Fingerprint normaliza aliases da origem para propriedade/causalidade, conservando caminho/query opacos do endpoint cifrado; o envio canonicaliza origem HTTPS/host minúsculo/443 implícita; conflito de outro usuário não transfere vínculo. Endpoint/chaves são cifrados com Fernet, sem exposição no contrato de leitura.

Rotina composta mantém lease/checkpoints diários, geração antes de avisos e recuperação a cada 300 s; dispatcher a cada 60 s. A prova operacional usa protocolo real local isolado, sem provedor público ou navegador push real. Aceitação local/criptografia correta não comprova entrega física. P10/Perfil foi resolvida pela delegação expressa para composição na 11, sem implementar a tela nesta etapa; P11 continua pendente e P6 externa.
