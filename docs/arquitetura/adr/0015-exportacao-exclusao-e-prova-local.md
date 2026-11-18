# ADR0015 — Exportação, exclusão e prova local

> **Contém:** decisão delegada sobre RN30, Perfil e validação operacional local, com limites de recuperação.
> **Origem:** delegação expressa do dono, RN30/ADR0003 e Q11-1–11/T11-A–H ratificadas pelo orquestrador em 16/11/2026.

**Status:** journal, WAL, bootstrap e laboratório de restauração **substituídos pela [ADR 0018](0018-exclusao-e-backup-simples.md)** (18/11/2026); o resto continua valendo. Original: decidido por delegação; implementação e provas pendentes na abertura da etapa 11. Não é resposta literal do dono, alteração manual da especificação de origem ou conclusão jurídica.

## Decisão

- JSON v1 assíncrono inclui perfil/pessoal/participações atuais/avisos autorizados/documentos pessoais, sem credenciais ou arquivos de grupo por autoria/upload. Jobs idempotentes expiram em 24 h desde o pedido; revisão transacional e ACL invalidam gerações desatualizadas. Links pessoais são assinados por 60 s no download autenticado. A última checagem de R após sessão/prova/TTL/ACL sob barreira curta autoriza a emissão; a barreira é liberada antes da rede. Não se promete atomicidade até primeiro byte físico ou recolhimento de resposta autorizada.
- Solicitar/baixar/excluir exige reauth allauth nativa estritamente menor que 300 s, por senha utilizável ou código para endereço próprio verificado, inclusive OAuth sem senha. Corrigir confirmação por link com `{key}`; verificação simples/request de código/login comum não provam reauth. Intenção de exclusão é única, vinculada à sessão/ação/CSRF e consumida só no commit bem-sucedido.
- Exclusão reutiliza barreira e ordem real 10, checa RN04/RN32 de todo o conjunto antes de efeitos pessoais, preserva grupo/evidências/autor NULL/Ex-membro. Não resolve órfãs dentro do DELETE nem concede visibilidade ao admin. Identidade estruturada é removida; não se promete reescrever menções livres ou conteúdo PDF/EXIF legitimamente compartilhado.
- Pins/reservas aceitas 10 preservam somente snapshot/destino autorizados e audiência atual, sem recriar pessoal. Cleanup pós-commit usa intenção durável, geração/CAS e reconciliação de PUT tardio; nunca elimina bytes com referência/pin/writer legítimo.
- Operação DB independente do usuário e journal externo PREPARE/COMMIT/ABORT têm recibos duráveis/idempotência/fencing/checkpoint. Sem rede/fsync sob barreira de domínio. Após PREPARE, conflito pode deixar bookkeeping opaco ABORT, sem remover dados/sessões/arquivos nem consumir intenção. Restore exige prova autoritativa atual para PREPARE pendente, nunca infere ABORT do backup antigo, não inventa promoção/admin e bloqueia sem estado/ledger compatíveis.
- No laboratório o checkpoint é independente e protegido dos scripts de backup/restore DB+objetos; comprovar truncamento após ACK, ausência/corrupção e guardas. Não se afirma proteção contra root que retroceda simultaneamente journal/checkpoint/chaves; não se impõe hardware monotônico. Ausência da âncora esperada mantém falha fechada. Journal/chaves de verificação duram mínimo 8 dias no laboratório de retenção 7 dias e enquanto backups/pins/jobs/objetos dependentes persistirem +1 dia; ambiguidade não expira automaticamente.
- PWA guarda só assets públicos versionados. Sem cache privado ou replay financeiro offline. Logout/troca/abas/bfcache/respostas tardias preservam isolamento. Offline limpa localmente e conserva pendência opaca de revogação. B autenticado usa seus dados/ações normalmente; apenas rebind push aguarda reconciliação autorizada. UUID não autoriza B a revogar A; nonces 10 opacos permanecem por dono.
- RNF05 mede 20 frio +20 quente em cada cenário pessoal/grupo, fixture e perfil 4G/CPU definidos no plano, p95 (19ª/20) ≤2 s até dados/controles prontos. Publicar todas as amostras/LCP/TTFB/erros; skeleton não vale como carregado.
- Laboratório isolado testa TLS/SSR/proxy/RN31/logs/storage/transportes/backup/restore. Listener SSR privado só GET `/api/me/`, `/api/espacos/{UUID}/resumo/` e `/api/notificacoes/resumo/`, UUID estrito, cookies no servidor, backend reautoriza, sem cache privado ou proxy arbitrário. RPO 24 h/RTO 60 min/retenção 7 dias são alvos locais a medir. Sem envio externo/deploy real; protocolo WebPush local não prova recepção pública.

## Perfil e autoridade — Q11-11

ADR0003/D5 previa nova tela por ausência de frame. A pergunta específica não recebeu resposta literal. O dono delegou expressamente analisar, decidir e executar as etapas restantes; o orquestrador ratificou compor Perfil com varal-ui/tokens/componentes atuais e shell/rota existentes, nas duas larguras e mínimo 360 px. Essa delegação, não o silêncio, supera somente o gate procedural de pedir tela/ok novamente. RN30 e demais regras permanecem; ADR0003 e origem não são reescritos como se a composição fosse original.

Escopo: dados próprios somente leitura, preferências 09, exportar/excluir/reauth e sair, sem nova função de identidade. Consultar canvas/guia somente leitura, citar referências reais e ausência de frame dedicado. Um desenho posterior pode exigir retrabalho de apresentação/QA. Não há autorização para excluir conta real do dono.

## Consequências e dependências

Prova fresca/revisão global podem exigir nova geração; medir contenção/starvation, sem servir parcial/antigo para ocultar falha. Triggers exigem inventário completo de fontes; leitores sem lock não provam ausência de deadlocks dos writers. Pins/journal aumentam retenção técnica mínima e exigem reconciliação; backup não desfaz exclusão. Reverter política exige nova decisão/contrato/migração sem ampliar audiência, apagar ledger cedo ou reenviar avisos. Detalhes reversíveis de lotes/arquivos ficam em D11-1/2.

P10 resolvida por delegação; P11 continua dependência concreta de destino/domínio/condições para implantação remota. P6 é reexportação externa; P3/P4 são provas locais da 11 e P9 verificação no próximo push autorizado. Nenhum novo ok genérico impede implementação local. Sem push/envio externo/deploy real ou alteração dos volumes existentes.

[Spec](../../etapas/11-acabamento-deploy/spec.md), [decisões](../../etapas/11-acabamento-deploy/decisoes.md), [plano](../../etapas/11-acabamento-deploy/plano.md).
