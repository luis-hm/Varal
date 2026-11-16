# Plano — Etapa 07 (Pagamento)

> **Contém:** modelo, contratos implementados em validação, fronteiras de permissão e ordem da fatia pagamento/comprovante.
> **Origem:** spec07 preparatória, RF15–RF17/CU08/RN14–RN16, decisões04 e infraestrutura06; pontos não literais da fonte estão marcados em `decisoes.md`.

## Ordem de execução

1. Docs/decisor consolidaram Q07-1–9 e ADR 0011: integral, autoria/papel alterado, anexação posterior, retenção e métricas; integrados após fechar a 06. Sem novo ok genérico, pois escolhas foram delegadas; registrar o que foi interpretação, não regra literal da origem.
2. Backend implementa Pagamento/DocumentoComprovante, permissões, transações/concorrência, validação de data/valor e endpoints; DevOps apenas ajusta infraestrutura reaproveitada com propriedade de arquivos separada.
3. Orquestrador gera OpenAPI/tipos; frontend lê frames/componentes atuais e integra07/D03,08/M03,09/M04 e progresso02/D02/10/D04.
4. QA (negativos por endpoint, arquivos reais, papéis/concurrency, dois tamanhos) → segurança → decisor → docs/commits locais. Sem push; continuar próximo estágio conforme autorização.

## Modelo implementado (validação em andamento)

`pagamentos.Pagamento`: UUID, `lancamento` FK CASCADE, `pago_em` DateField civil, `valor_pago_centavos` positivo, `marcado_por` SET_NULL, `criado_em`, `desfeito_em?`, `desfeito_por?` SET_NULL. **Uma ativa por conta** via restrição parcial onde `desfeito_em IS NULL`; FK permite guardar marcas desfeitas sem implementar parcelas agora. Autor excluído aparece Ex-membro, sem e-mail permanente em histórico.

`DocumentoComprovante`: UUID, destino de conta obrigatório, pagamento-alvo opcional para anexação posterior, pagamento confirmado OneToOne opcional, uploader SET_NULL, marca irreversível de vínculo, MIME/tamanho/nome seguro, estado e UUID de tentativa. Arquivos/chaves imutáveis em prefixo próprio; reutilizar primitivas de spool, limites, django-storages, assinatura pública e intenção de limpeza, **não autorização/endpoint de boleto**.

Foto/PDF são validados em processo dedicado limitado, antes de vincular. Q07-4 fixa formatos JPEG/PNG/PDF, limite de 5 MiB e imagem até 20MP; fonte RF16 não define esses números/formatos exatos. Não extrair texto bancário nem afirmar autenticidade. Preservar original e EXIF sem recompressão, orientar apresentação conforme metadados quando suportado e avisar sobre original/metadados acessíveis aos espectadores. Alias de storage comprovantes controla MIME pelo formato validado: não usar MIME fixoPDF de storages[pdf] paraJPEG/PNG. Worker só altera DocumentoComprovante; não marca paga/confirmada.

## Contrato implementado

| Operação | Entrada | Resultado / guarda |
| --- | --- | --- |
| `POST /api/lancamentos/{id}/pagamentos/` | `{pago_em,valor_centavos_esperado,comprovante_id?}` | Revalida conta visível e permissão atual de pagar, pendente, data não futura e valor atual esperado;201 ContaDetalhe paga ou confirmada se arquivo já validado |
| `POST /api/lancamentos/{id}/comprovantes/` | multipart arquivo, `pagamento_id?` para anexação posterior | Endpoint próprio;202 draft privado. Sem alvo é intenção de nova marcação; com alvo só daquela marca ativa, sujeito à política de anexação aprovada |
| `GET /api/comprovantes/{cid}/` e `arquivo/` | — | Draft: uploader com permissão atual do contexto; vinculado: acesso atual à conta. Preview/URL nunca conferem permissão de marcar/anexar; URL curta para arquivo válido vinculado ativo ou histórico, sempre pelo acesso atual à conta; draft só próprio e autorizado |
| `POST /api/lancamentos/{id}/pagamentos/{pid}/comprovante/` | `{comprovante_id}` | Confere alvo ativo exato, papel atual, autoria/política e documento pronto do mesmo contexto; vincula e promove a confirmada atomicamente |
| `POST /api/lancamentos/{id}/pagamentos/{pid}/desfazer/` | corpo vazio | Autor ou admin atualmente visível conforme RN16/política consolidada; trava/alvo exato; marca desfeito e devolve pendente;409 para marca já desfeita ou diferente da atual |
| `GET` detalhe da conta | — | Acrescenta pagamento ativo/ref de comprovante e flags de ações autorizadas; sem URL permanente/conteúdo do arquivo. Leituras de documento/registro sempre aninhadas à conta autorizada |

Após autorizar a conta, ids aninhados devem pertencer a ela. Não buscar pagamento/documento só por UUID confiando no frontend. Falhas de estado só são reveladas após autorizar acesso; invisível continua404. Quaisquer campos de valor recebido são conferência do valor integral esperado, não autorização a alterar débito ou criar parcial sem regra.

## Consistência e casos extremos

- Marcar, desfazer e vincular comprovante revalidam vínculo/papel/visibilidade sob travas compatíveis com admins/membro→conta. A transição paga→pendente deve serializar com saída/remoção/troca de papel, não repetir o caso de conta que vira aberta fora da avaliação RN32.
- Duas marcações: só uma ativa, uma transição/histórico; repetição é conflito uniforme ou no-op explicitamente definido, sem promessa de idempotência entre dispositivos sem chave persistida.
- Undo referencia UUID do pagamento esperado. SeA foi desfeito eB criado, pedido atrasado deA não alteraB.
- Upload para uma marca específica não pode migrar para outra. Se alvo foi desfeito, conta ficou restrita ou ator perdeu permissão, recusar novo vínculo/assinatura conforme acesso atual; conclusão do worker não altera status.
- Undo com pagador que saiu enquanto a conta estava paga segue Q07-8: limpar a atribuição viva ao reabrir, preservando autoria/identidades históricas e RN32, sem conceder visão a admin.
- Corte integral Q07-1/8: impedir alteração de valor da conta enquanto há pagamento ativo; para corrigir, desfazer primeiro. Isso é política delegada no ADR 0011, não regra literal do RF12. Descrição e demais campos não são congelados genericamente por suposição.
- Comprovante de marca desfeita não reabre como draft. Undo conserva evidência histórica privada ligada ao pagamento/conta e legível pela autorização atual; não elimina objeto nem reabre draft. Sem troca/remoção isolada; corrigir exige undo e nova marca; qualquer delete só após commit, com recuperação de fila/storage e chaves imutáveis. URLs já emitidas seguem prazo curto, sem promessa de revogação instantânea.
- Histórico registra ações, datas, valores em centavos e ids/autoria necessários; nunca nome de arquivo, código, chave S3, URL assinada ou conteúdo integral. Pagamento bancário real permanece fora do Varal.

## Resumos e filtro

Acrescentar `pagas_qtd` ao resumo e aos itens PorCasa; progresso por quantidade do mês, só sobre o queryset visível e não cancelado. Paga e confirmada contam uma vez; não somar múltiplas marcas históricas da mesma conta. MemberRow usa a métrica ratificada, calculada por espectador, sem contador global revelando restritas.

Contrato Ex-membro: `pagador=ex_membro`, `opcoes.ex_membro: bool`, opções UUID apenas para membros atuais. Agrupamento usa FK não nula sem vínculo atual; nulo continua `nenhum`. Não usar UUID fictício, renomear identidades ou inferir usuário excluído. Fonte Q04-37 já aprovou o agrupamento; nomes/forma exatos do contrato são desenho interno.

Não implementar RN20/origem nesta etapa: relação/solicitação só nasce na10. A integração futura deve chamar os serviços autorizados de pagamento, sem criar sincronização cruzada invisível agora.

## Integração consolidada pelo decisor

Prevalecem decisoes.md Q07-1–9 e ADR0011 sobre propostas anteriores deste plano. Acrescentar EventoPagamento único porPagamento, persistido junto da marcação para consumo09; não iniciar transporte. Histórico de pagamentos deve oferecer comprovante antigo por referência/endpoint autorizado pela conta, sem recriar draft. Guardar pagador no instante da marca como FK anulável, sem nomes/e-mails snapshots. Draft inicial precisa de versão/intenção persistida que não atravesse outro ciclo de marcação/undo. Autor visível agora observador conserva só o undo. Reabertura limpa pagador sem vínculo atual, revalidaRN32 e recusa409 atomicamente se órfã. Valor efetivamente diferente é409 com marca ativa, mesmo valor é no-op.


## Precisão do contrato atual

`Documento` retorna `{id,estado,nome,tamanho,mime,criado_em}`; `estado` é o enum `pendente|lendo|valido|invalido|erro`, independente do status da conta. Detalhe inclui `pagamento_ativo`, `pagamentos`, `pode_pagar`, `pode_desfazer_pagamento` e `pode_anexar_comprovante`; Pagamento expõe `id,pago_em,valor_pago_centavos,criado_em,desfeito_em,marcado_por,comprovante_id`. As flags orientam a interface, mas não substituem nova autorização na escrita.

Resumo/PorCasa expõem `pagas_qtd`; seu contexto é o mês atual em Fortaleza, devolvido em `mes`. O detalhe do grupo expõe `membros[].contas_atribuidas_qtd` para esse mesmo mês atual, sem filtro de mês próprio. A lista continua com `mes=AAAA-MM`; `opcoes.ex_membro` vem apenas do visível daquele mês. Não confundir mês de vencimento com data de pagamento.

Manutenção operacional: beat chama `recuperar_comprovantes` a cada 300 s (D07-1). Reprocessa pendentes, marca leitura antiga como erro, expira drafts de 24 h e recupera intenções de limpeza. Não implementa a geração mensal de recorrências da 08. Storage usa alias `comprovantes`, MIME validado e prefixo `comprovantes/{uuid}`, com spool privado separado. Validar I/O, Content-Type e recuperação reais antes de fechar.
