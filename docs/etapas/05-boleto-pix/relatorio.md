# Relatório — Etapa 05 (Boleto e Pix)

> **Contém:** entregas, contrato, verificações, segurança e pendências da Etapa 05.
> **Origem:** branch `etapa/05-boleto-pix`, spec/decisões/fontes da etapa, entregas backend/frontend, QA integral e reauditoria de segurança em 16/11/2026.

**Estado: concluída em 16/11/2026, pronta para commit/merge local.** Parser, persistência/API e interface entregues; rodada integral de types/test/lint/E2E comprovada com `status: passed` e exit 0 em todos os comandos. Capturas revistas após a correção do aviso RNF11; segurança final sem bloqueantes. Sem push.

## Entregas

- **RF08/RN08–RN10:** parser puro em `api/apps/boletos/parser.py` para linha bancária de 47 dígitos e arrecadação de 48, com normalização permitida, DVs de blocos e geral, valor monetário ou ausência e vencimento quando codificado. As [fontes primárias](fontes.md) incluem FEBRABAN, BCB e confirmação do reinício do fator em manuais oficiais Itaú/Banrisul.
- **Fator de vencimento:** 0000 não sugere data; 0001–0999 conserva base legada; 1000–9999 sugere ciclo reiniciado em 22/02/2025 e expõe alternativa legada. Front mostra escolha explícita; backend aceita somente uma data codificada. Não há aproximação pelo relógio nem correção silenciosa de uma escolha legada.
- **RF09:** BR Code validado por TLV/CRC sobre bytes UTF-8, payload integral preservado e chave embutida canônica. Chave avulsa valida sintaxe/DVs e normaliza apresentação. ID54 estático ausente requer valor; zero presente é inválido; ID54/txid de QR dinâmico são ignorados. Não consulta URL dinâmica, DICT ou titularidade; beneficiário é declarado no código, não verificado.
- **Instrumento/API:** OneToOne com a conta, sem backfill em manuais; preview autenticado sem gravação e revalidação no save. Valor/data finais precisam continuar coerentes mesmo em PATCH sem instrumento. Conta/instrumento/transição/histórico são atômicos; troca/remoção de paga/confirmada é recusada. Aguardando com instrumento válido e dados completos passa a pendente, sem criar aguardando avulsa.
- **Privacidade/RN22:** instrumento aparece só no detalhe e respostas de mutação autorizados pela conta; não em lista/resumo/histórico/log. Sem rota por id próprio ou admin independente. Histórico registra tipos antes/depois e `codigo_alterado`, sem payload integral; reenvio idêntico não cria alteração artificial.
- **RF14/UI:** formulário oferece Digitar conta, Colar código e Chave Pix, preserva entrada inválida e protege campos codificados. Detalhe copia boleto normalizado, BR Code integral ou chave, anuncia resultado e oferece campo selecionado quando clipboard falha. Resposta atrasada de preview não sobrescreve nova escolha. A cópia não executa pagamento.
- **CA15/CA16:** gravação em voo mantém campos, modo, conteúdo, fechamento e reenvio protegidos, inclusive antes do próximo render; refetch remoto não substitui o instrumento/conferência da sessão local do formulário. São proteções da mesma interação, não promessa de idempotência global de novas requisições.

Contrato completo em [API](../../api/README.md#boleto-e-pix-etapa-05); persistência e restrições em [modelo](../../dados/modelo.md#implementação-da-etapa-05); apresentação em [design](../../design/README.md#boleto-e-pix-implementados-etapa-05).

## Critérios e testes

| CA | Evidência existente / validação final |
| --- | --- |
| CA01–CA03 | `test_rn08_bancario_formatado_e_mutacoes`, `test_rn09_fator_ciclos`, `test_rn09_fator_ausente_e_legado`, `test_rn10_arrecadacao_referencias`, exemplos oficiais de módulos; API `test_rn09_salvar_fator_ambiguo_somente_datas_codificadas` |
| CA04 | `test_rn08_codigo_invalido`, `test_rn08_rf09_preview_invalido_400_sem_gravar`; Vitest e E2E de entrada inválida preservada para correção |
| CA05–CA07 | Vetores BCB, TLV/UTF-8 adversário, chaves inválidas/canônicas, zero estático/dinâmico e ausência de rede; API Pix estático/dinâmico |
| CA08 | `test_rn09_rn11_save_revalida_400_sem_gravacao_parcial`, `test_rn09_patch_instrumento_ausente_ainda_valida_valor_data`, `test_rn09_patch_troca_fator_ambiguo_exige_data_e_sem_parcial`; Vitest valor protegido/data legada |
| CA09 | `test_rn01_rn02_rn06_instrumento_herda_404_conta`, `test_rn05_instrumento_so_edita_quem_pode_editar_conta`, `test_rn06_detalhe_nao_entrega_instrumento_novo_apos_revogar_acesso`, teste de ausência no admin/cascata |
| CA10–CA11 | Testes de trocar/remover/preservar/no-op, fechada sem troca, transição aguardando→pendente e manual legado; restrições do banco/vínculo único |
| CA12 | Vitest de cópia integral e clipboard negado/foco/seleção; dois cenários de `boletos.spec.ts` passaram em mobile e desktop |
| CA13 | Teclado/Tab, código de 4096 caracteres, alvos≥44px e sem overflow verificados; capturas finais comparadas com 05/M01, 06/M02,07/D03 nas duas larguras; aviso RNF11 em dd/mm/aaaa |
| CA14 | Test/lint/types/E2E integrais verdes, comparação visual concluída, segurança sem bloqueantes e matriz atualizada |
| CA15–CA16 | Vitest `pending criar/editar cannot reset or send twice…` e `a remote instrument refetch cannot replace the preview of a dirty local entry`; três regressões falharam antes da correção e passaram depois |

| Verificação direcionada já concluída | Resultado |
| --- | --- |
| Parser puro, sem Django/banco | **65 passaram** após regressão do aviso RNF11; os lotes anteriores de 59/64 são históricos, não soma adicional |
| API/instrumento e regressão de contas | **143 passaram: 54 API + 89 contas** |
| Frontend pertinente final | **27 passaram**, com três regressões que falharam antes do patch; o lote anterior de 20 não é somado a este |
| Revisão de leitura do backend | Sem bloqueantes naquele escopo; reauditoria final da fatia completa também sem bloqueantes |

| Verificação integral final | Estado |
| --- | --- |
| `make test` | **354 pytest e 83 Vitest passaram**, após todos os ajustes |
| `make lint` | **Passou** (ruff, ESLint e typecheck), exit 0 |
| `make types` determinístico | **Duas gerações passaram sem diferenças**, exit 0 |
| `make e2e` integral | **91 passaram e 3 ignorados de propósito**, nenhuma falha; 5,8 min, exit 0 |
| Novos E2E e comparação visual | **4/4 passaram** nas duas larguras e capturas finais revistas; aviso em 03/07/2000 coerente com o seletor |
| Segurança final | **Reauditoria sem bloqueantes**; dois achados funcionais da interface encerrados com regressões |

**Registro da verificação:** tentativas E2E anteriores não produziram resumo final; a causa dos sinais de encerramento não foi determinada. Não foram contabilizadas como rodadas integrais verdes nem somadas à execução final. A rodada independente final registrou sucesso em types, determinismo, test, lint e E2E, e o servidor Next da suíte terminou sem processo próprio remanescente. O resultado anterior de 353 pytest foi substituído pelos 354 após a regressão do aviso RNF11; não são lotes cumulativos.

## Doop e diferenças de escopo

Referências: 05 · Nova conta/M01, 06 · Conferir conta/M02 e 07 · Detalhe/D03. Frontend/QA releram frames, guia e componentes em modo somente leitura. Os quatro novos cenários passaram em 390×844 e 1440×900; capturas `boleto-conferencia-*`, `boleto-detalhe-*` e `pix-dinamico-detalhe-*` foram comparadas com os frames e revistas após corrigir o aviso para 03/07/2000, mantendo datas estruturadas ISO. Composição responsiva adequada ao escopo da etapa; fixtures sintéticas e inspeção visual, sem comparação pixel a pixel. Nenhuma aprovação ou alteração do canvas foi feita.

O seletor atual é integrado à folha de conta existente, com conferência de código/chave e dados em vez da prévia de PDF da 06. PDF/upload, emissão e beneficiário lido de PDF continuam na 06; marcar pagamento/comprovante na07; recorrência na08; modo simples completo na10. Esses recursos futuros não são botões falsos entregues nesta etapa.

## Segurança e limites

- Preview usa sessão/CSRF e limite de texto; não consulta objetos de outros usuários nem grava conta. Toda leitura/mutação persistida herda a autorização e as travas da 04.
- Código inválido, conflito valor/data ou tipo/conteúdo inconsistente não deixa gravação parcial. Banco limita estrutura e vínculo, serviço valida DVs/CRC e coerência.
- A revisão final encerrou dois achados funcionais: mudança/reset de controles durante gravação podia permitir novo envio, e refetch de instrumento remoto podia substituir a conferência local. Trava síncrona/controles protegidos e snapshot da sessão corrigem os casos, com três regressões e CA15/CA16; reauditoria sem bloqueantes.
- HTTP rejeita NUL pelo `CharField`/DRF. **Limite da biblioteca pura para a 06:** um BR Code com CRC recalculado ainda pode conter NUL em campo textual; worker de PDF deve validar NUL e Unicode inválido fora do DRF antes de persistir em campos/JSONB. Não foi demonstrado erro 500 acessível pela API atual; a reauditoria da integração HTTP atual ficou sem bloqueantes.
- Nenhuma URL dinâmica é dereferenciada e nenhum código/chave ou texto integral será usado em logs/histórico. Beneficiário e sintaxe de chave não certificam titularidade.

## Decisões, ajustes e pendências

Decisões em [decisoes.md](decisoes.md), sob a delegação expressa do dono; não são respostas literais dele para cada item. Nenhuma pergunta nova aguarda ok genérico.

**Ajustes aplicados:** nenhum item remoto novo. Ao pedido de conferência atual, o dono declarou no chat: "no varal ajustes n tem nenhum pendente". O Codex não leu nem marcou o documento pelo conector, indisponível; não reutilizou rev 24 como atual.

**Ajustes pendentes / itens a marcar como " — feito na etapa 05":** nenhum, conforme essa declaração. Se o dono fornecer novo item durante a execução, incorporá-lo antes do fechamento.

- **P6 externa:** Claude Code deve reexportar a origem sem categoria; cópia local permanece defasada, sem edição manual. ADR 0005 já rege a implementação sem categoria.
- **06:** armazenamento já passou saúde/autenticação (P1), mas ainda requer teste real de objeto/URL assinada; validar texto extraído fora do DRF e implementar PDF assíncrono com acesso herdado da conta.
- **Verificações concluídas:** QA integral, capturas, segurança, auditoria de decisões e matriz. Commit/merge locais e abertura da 06 ficam com o orquestrador conforme autorização vigente; nenhum push foi feito.
- **Limites de ambiente:** avisos de depreciação Django/Vite permanecem; o override de cadastro de desenvolvimento do E2E continua até `make dev` (M6 já aceito na 04). Não representam testes falhando nem mudança de limites em produção.
