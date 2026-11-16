# Spec — Etapa 09 (Notificações)

> **Contém:** escopo e critérios de aceite para push, e-mail e central privada.
> **Origem:** RF20, CU08/CU12/CU07, RN18/RN19/RN21/RN32, RNF06/RNF07/RNF10, P7/ADR 0006, Q21/04, Q07-9/ADR 0011 e Q08-4/ADR 0012; [Q09-1–9 e D09-1](decisoes.md).

Etapa 09 aberta em 16/11/2026 na branch `etapa/09-notificacoes`, após commits `b5d516d` e `eadb1c2` da 08 e merge local `59e0cc5`. Dono delegou decisões/execução e atestou Ajustes sem pendentes no chat, sem leitura remota. Q09-1–9 e D09-1 estão decididas por delegação no [registro](decisoes.md) e [ADR 0013](../../arquitetura/adr/0013-notificacoes-privadas-e-entrega.md). Implementação concluída; o relatório distingue resultados direcionados das verificações finais concluídas. P6 externa e P11/destino pendente permanecem; P10 resolvida por delegação expressa para composição do Perfil na 11, sem implementá-lo agora.

## Escopo

Push e e-mail assíncronos, central 04/D06, NoticeRow, ponto de não lido e avisos recentes 02/D02. Rodada diária às 07:00 America/Fortaleza (instantes gravados UTC; vencimentos são datas civis). RN13/janela de selos não altera RN19.

| Gatilho | Audiência elegível atual, sem duplicar pessoas |
| --- | --- |
| D−5, ocorrência variável ainda aguardando boleto | Criador e pagador que veem a conta |
| D−3 e D0, conta aberta sem pagamento | Pagador que vê a conta |
| D+1, conta aberta sem pagamento | Pagador, criador e admins atuais que veem a conta |
| Marca de pagamento da 07 | Criador referido por EventoPagamento ainda autorizado; marca deve continuar ativa |
| RN21, conta ficou sem pagador | Admins atuais que veem essa conta |
| RN32/P7, remoção administrativa cancelou restrita órfã | Somente removido identificado em Historico.dados.removido; exceção limitada ao aviso, sem detalhe/arquivos |

`aguardando` da 08 significa boleto/informações ainda não conferidos; conferência manual completa também resolve a ausência, conforme Q08-4. Conta pessoal sem pagador não ganha destinatário implícito: D−3/D0 sem destinatário; D−5/D+1 podem alcançar criador conforme regra. Central permanece disponível mesmo com canais externos desligados.

## Critérios de aceite

| ID | Dado / Quando / Então | Lastro |
| --- | --- | --- |
| CA01 | Dada data civil em Fortaleza e execução às 07:00, quando identificar D−5/D−3/D0/D+1, então criar só os tipos e destinatários da tabela; nenhuma mensagem para paga/confirmada/cancelada, nem tolerância de fuso UTC que antecipe o dia | RN18/RN19/CU12 |
| CA02 | Dada variável aguardando, quando chegar D−5, então avisar criador/pagador elegíveis uma vez; PDF apenas enviado não resolve ausência; conferência completa da 08 resolve, inclusive manual | RN18/Q08-4 |
| CA03 | Dado EventoPagamento da 07 pendente, inclusive anterior à 09, quando consumir, então avisar criador ainda visível apenas se marca ativa; anexação não duplica, undo/exclusão/revogação concluem evento sem enviar | CU08/ADR 0011 |
| CA04 | Dada saída/remoção com pagador removido, quando processar RN21, então só admins atuais visíveis são avisados; nulidade/repetição de papel não cria avisos e admin invisível não obtém contagem ou indício | RN21/Q21 |
| CA05 | Dado cancelamento automático RN32, quando entregar P7, então somente o removido recebe lista mínima das contas canceladas; legado sem snapshot usa referência do evento/data/motivo, sem enriquecer por dados atuais; leitura desse aviso não exige associação atual, não reabre conta/PDF e não sinaliza evento ao admin invisível | P7/ADR 0006 |
| CA06 | Dadas concorrência, repetição de beat e falha/retry, quando reservar evento, então banco limita um aviso lógico por evento/destinatário e uma entrega por canal; canais independentes e até três tentativas totais (inicial + 2 retries após 1 min/5 min); registrar ambiguidade após aceitação externa, sem prometer entrega física exatamente uma vez | RN19/RNF07/CU12 |
| CA07 | Dado aviso comum criado antes da perda de acesso, quando enviar ou listar/contar/marcar como lido, então revalidar audiência/contexto atual e ocultar tudo que deixou de ser permitido; revogação é terminal mesmo após reingresso; P7 usa somente a exceção CA05 | RN01–07/RN32 |
| CA08 | Dadas edições de vencimento/pagador, pagar/undo ou cancelar, quando recalcular agenda, então invalidar pendências obsoletas, não repetir lembrete lógico já consumido e não ressuscitar avisos antigos; novo destinatário só pode receber dentro da janela vigente | CU07/RN19/ADR 0011 |
| CA09 | Dada rodada perdida, quando recuperar, então processar lembretes só na janela definida Q09-3, sem rajada de fases vencidas; eventos duráveis da 07 são consumidos sem esse corte e legados RN21/P7 seguem Q09-8 | CU12/Q09-3/Q09-8 |
| CA10 | Dadas preferências, permissão negada e dispositivos múltiplos, quando despachar, então respeitar opt-out por canal, nunca pedir permissão automaticamente, enviar a cada inscrição ativa do usuário e desativar endpoint expirado 410/404 sem bloquear e-mail/central | RF20/RNF10/Q09-6 |
| CA11 | Dada sessão autenticada, quando acessar central/recentes/contador/leitura, então receber somente avisos próprios elegíveis, com paginação estável e leitura idempotente; em 390×844 e 1440×900 seguir 04/D06/02/D02 lidos ao vivo antes da UI, com teclado, vazio/erro e movimento reduzido | RF20/Doop/RNF08–09 |
| CA12 | Dado SSR/build sem navegador, sessão trocada/logout e tentativa cross-site, quando carregar PWA ou alterar inscrição/preferências/leitura, então não falhar no servidor, não cachear dados financeiros entre contas, exigir autenticação/CSRF e não expor chave privada VAPID/endpoints ou payload financeiro em logs | RNF01–03/RNF10 |

| CA13 | Dado aviso próprio autorizado fora da página carregada, quando marcar todos como lidos, então atualizar todo o universo autorizado de forma idempotente, sem incluir revogados/alheios ou alterar timestamps já marcados. | Q09-9/04/D06 |
| CA14 | Dada rotina diária, quando executar às 07:00 em Fortaleza, então gerar/recuperar competências da 08 antes de avaliar avisos da 09 num único fluxo ordenado, preservando manutenção de comprovantes separada. | D09-1/CU12 |

## Fora de escopo e pronto

Solicitação/RN20 fica na 10; Perfil, auditoria final de instalação/performance e implantação na 11. Não criar nova página/frame, alterar canvas ou enviar por WhatsApp. Central, preferências e gesto de push compõem a interface existente. O canvas foi lido pelo orquestrador em leitura: 04/D06, 02/D02 e NoticeRow são draft, referências adotadas por delegação sem mudar status.

Pronto exige implementação, tipos determinísticos, QA CA01–CA14/concorrência/visibilidade, prova local de worker/transportes, segurança, comparação mobile/desktop e docs/matriz/relatório com resultados reais. Mocks não comprovam entrega externa real; aceitação por SMTP/Web Push não comprova leitura/entrega física única.

## Invariantes da triagem

- Consumir **todos** os EventosPagamento pendentes da 07 sem corte de data, revalidando marca ativa, criador e acesso; anexação não cria evento novo.
- Importar RN21/P7 uma vez por histórico com checkpoint de ativação persistido; legados anteriores à ativação ficam **somente na central**. P7 sem snapshot seguro usa referência opaca/data/motivo, sem descrição atual ou busca privilegiada.
- Revogação terminal do aviso comum; não reaparece por reingresso, undo ou mudança de destinatário. Preferência/inscrição novas não reenviam passado. Destinatário novo só recebe fase ainda na janela do próprio dia-alvo, entre 07:00 e seu fim.
- **Três tentativas totais** por entrega/filho push: inicial e dois retries após 1 min/5 min somente em falha recuperável comprovada. Aceitação desconhecida vira incerta, sem retransmissão automática cega. Canais/dispositivos independentes.
- Web Push usa provedores homologados, conexão HTTPS fixada a IP público validado/TLS/SNI, sem redirects/proxy implícito ou DNS rebinding. Inscrição por usuário, sem transferência automática; logout revoga servidor. Payload genérico e SW sem cache privado.

## Integração concluída

Contratos reais em [API](../../api/README.md#notificações-etapa-09) e entidades em [modelo](../../dados/modelo.md#implementação-da-etapa-09). CA12 inclui sessão terminal/tombstone da instalação e aliases de fingerprint (D09-2), sem DELETE por id de inscrição. CA11 inclui gaveta desktop no mesmo URL/contexto/history e `/avisos` direto com Início ao fundo (D09-3). P7 resolvida pela central privada e legado seguro, com critérios finais verdes.
