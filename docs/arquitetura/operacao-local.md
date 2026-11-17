# Operação local e restauração — Etapa 11

> **Contém:** seleção do laboratório/primário, manutenção, backup e gates de restauração; limites e provas pendentes.
> **Origem:** scripts atuais `infra/scripts/lab11-*`, modelos/comandos privacidade, T11-E/K e ADR0015; checkpoint de implementação da etapa 11 em 16/11/2026.

Este runbook cobre recursos sintéticos próprios do laboratório, não uma implantação remota aprovada. **P11 continua sem destino/domínio/condições concretos.** P6 é reexportação externa, P9 verificação do próximo push autorizado. O dono atestou Ajustes sem pendentes no chat; não houve conector/reexportação. Sem push, envio externo, limpar-dev, exclusão de conta real ou alteração dos volumes existentes. Não promover credenciais/certificados/fixtures locais a produção.

## Identificar o ambiente antes de operar

`make lab11-init` cria diretório próprio `/tmp/varal11-stack.*`, projeto e materiais privados; `make lab11-up LAB_DIR=<diretório próprio>` usa imagens previamente construídas, sem capturar fonte concorrente. `make lab11-down LAB_DIR=<diretório próprio>` para somente esse laboratório e preserva volumes. Não substituir validações por nomes arbitrários ou executar `down -v` para resolver erro.

Arquivos `project`, labels Compose e `varal.restore`/`varal.parent`, IDs, redes internas e mounts são parte das guardas. Antes de afirmar qual banco está ativo, conferir o volume montado e a identidade do cluster, não apenas nome de serviço/tag de imagem. Runtime é separado de manutenção: `runtime.env` não é a credencial de migração/restore; `restore-maintenance.env` e chaves privadas têm acesso restrito. Não imprimir env/config com segredos, tokens, URLs assinadas, headers ou corpo do atestado.

## Primário restaurado e ACTIVE_RESTORE

`ACTIVE_RESTORE` descreve versão/projeto/restore_id/operação/estado cutover. Sua presença ou a de `CUTOVER` bloqueia **up/down/backup do Compose base**; não apagar o marcador para contornar a guarda. O primário pode estar nos volumes restaurados, não nos originais.

`bash infra/scripts/lab11-active.sh <lab_dir> config|up-core|up|stop` seleciona o override `infra/lab/compose.active-restore.yml`. Valida formato do marcador, projeto, exclusividade operacional e labels dos volumes de PostgreSQL/objetos/staging; confirma que clones manuais não continuam rodando. `up-core` sobe somente dependências, sem produto. `up` exige ausência de `CA08_GATE_PENDING`; não é autorização para ignorar outros gates. `stop` verifica que o primário Compose monta o volume esperado antes de parar. Não manter origem e clone abertos simultaneamente.

O override ativo seleciona `varal11-web-f2-webpack:local`; a imagem local validada tem ID `sha256:326229fbc146bd1ed717a32c77524ecf434389b2ecaa11b66c65826be26e0eb5`. Ela antecede a correção posterior de hidratação do contador com movimento reduzido; não representa o código web final. A tag precisa existir antes de `up`: o script não faz build. O Dockerfile usa Turbopack por padrão, portanto um build sem argumento não reproduz a configuração testada. Enquanto o snapshot privado F2 e seu manifesto existirem, confira o manifesto e construa a tag com:

```sh
cd /tmp/varal11-web-f2-snapshot
sha256sum -c /tmp/varal11-web-f2-snapshot.sha256
docker build --build-arg VARAL_NEXT_BUNDLER=webpack -t varal11-web-f2-webpack:local -f infra/lab/web.Dockerfile .
```

O contexto deve conter apenas o snapshot de código e o Dockerfile, sem dados, `.env`, segredos, `node_modules` ou `.next`. Uma reconstrução pode gerar outro ID; confira a fonte e repita os testes aplicáveis antes de assumir equivalência. O snapshot em `/tmp` não é arquivo durável: se não existir, prepare um contexto privado limpo da fonte aprovada e registre seus hashes antes de construir. O comando não faz deploy remoto.

Backup padrão usa `make lab11-backup LAB_DIR=<lab_dir> BACKUP_KEY_FILE=<arquivo privado>`, somente em ambiente sem primário restaurado ativo. Para o primário selecionado por ACTIVE_RESTORE existe `bash infra/scripts/lab11-backup.sh <lab_dir> <arquivo privado> --active-primary`: seleção por marcador/volumes/labels, nunca fallback silencioso ao banco antigo. Esse caminho passou uma vez no laboratório; não é garantia de restore posterior ou CA16 concluído. Artefatos permanecem em quarentena até as provas correspondentes.

## Backup, WAL e journal

Backup físico PostgreSQL e objetos são cifrados com manifestos/hashes e identidade do cluster; `pg_dump` não substitui PITR para ledger posterior ao snapshot. WAL cifrado tem cadeia, checkpoint independente e ACK autenticado após persistência. Antes de chamar SMTP/Push, o commit de INICIADA deve estar coberto pelo witness WAL e capacidade/lease/audiência são revalidadas fora da barreira. Falha comprovadamente anterior ao transporte conserva orçamento de retry; estado incerto não recebe repetição cega.

`lab11-backup-cut.sh` vincula corte posterior ao snapshot e seu WAL/ACK. `lab11-restore-stage.sh` valida/extrai somente para volumes novos, sem abrir serviço. Scripts recebem argumentos posicionais e arquivos privados; conferir a interface atual do script antes da invocação. Não forjar atestado por preenchimento manual de campos. Retenção 7 dias, RPO alvo 24 h e RTO alvo 60 min são metas locais que exigem medição do exercício inteiro.

Para exclusões, interromper origem API/worker/beat, obter exclusividade e passar journal a DRAIN; reconciliar PREPARE no banco autoritativo antes de SEALED. Selo persiste restart e proíbe novas escritas até RELEASE por credencial separada. Restaurar com cadeia/âncora/WAL ausentes ou PREPARE sem decisão atual é falha fechada, não inferência de ABORT a partir do backup antigo. Checkpoint separado protege o fluxo operacional; não há promessa contra root que recue journal/checkpoint/chaves simultaneamente nem requisito novo de hardware.

## Atestado, ledger e direitos aceitos

`lab11-restore-attest.sh` e comando backend `reconciliar_exclusoes_restore` consomem provas de identidade/timeline/LSNs, cadeia WAL, objetos/pins e selo fresco nonce/HMAC. Marcador exclusivo da operação é criado no clone após replay/promoção. O comando aplica RN04/RN32 ao conjunto antes de Collector, troca época de R e registra digest idempotente; não abre tráfego/dispatch. Um HMAC válido prova origem/integridade da afirmação, não a execução física por si. Ver [protocolo do journal](protocolo-journal.md#selo-e-atestado-operacional-de-restauração-t11-ek).

O gate `lab11-ledger-gate.sh` compara ledger completo do clone com a **origem atual fechada**, exige igualdade, watermark arquivado, witness, selo/fence e HMAC. `lab11-ledger-consume.sh` só consome gate validado no clone isolado. INICIADA restaurada torna-se incerta conforme lease/política; nunca vira reenvio apenas porque houve restore. Ledger igual não prova preservação de toda regra de domínio.

**Correção de direitos aceitos CA16:** um aceite legítimo ocorrido depois do target PITR pode faltar no clone mesmo com objetos e ledger consistentes. Direitos aceitos/pins/snapshot/destino devem ser preservados sem recriar pessoal excluído ou ampliar acesso. Backend/DevOps implementaram projeção protegida da origem atual fechada para o clone após reaplicar journal, seguida de comparação e gate de objetos/direitos. `lab11-rights-gate.sh` verifica inventários/objetos, ausência de writers incertos, estabilidade da origem e ligação com ledger/atestado; isso não autoriza inserir direitos por inferência.

A prova negativa específica de objeto anterior ao backup com direitos de aceite posteriores ao target **rejeitou** a abertura corretamente. O POS de direitos aceitos passou, inclusive worker PREPARANDO→ATIVA, origem NULL e SHA igual. O gate ACL/auth adicional também passou NEG/POS no corte atual descrito abaixo; isso não aprova globalmente CA16. Manter produto/worker fechados enquanto houver `CA08_GATE_PENDING`, diferenças de direitos, objetos/pins ausentes ou prova ambígua. Estado fixture não é política de produção.

## Evidências disponíveis e limites

- Make test supervisionado passou 546 API em 667,11 s e 149 web em 170,56 s antes de D11-5. Lint final passou; tipos são herdados da dupla determinística01. Delta Providers always/retry false tem foco3/3, primeira web posterior reprovou151/152 (sem causa demonstrada), segunda passou152/152 (41 arquivos/153,82 s, fonte igual). API sem alteração mantém prova válida; não somar recortes ou atribuir a web anterior ao delta.
- CA08: prova real aceite10→DELETE204→worker/cópia S3, hash e ACL, usando DjangoClient no processo, sem proxy. Pin direto/manipulação de fixture anterior não substituem essa prova.
- CA17: SMTP STARTTLS real com uma captura aceita e Push TLS/VAPID/AES por worker com uma entrega aceita no receptor local. Sem provedor público/recepção externa garantida.
- QA final 24/24 nas três larguras, axe/Doop e instalação técnica Chromium/CDP aprovados. PWA técnico não prova gesto físico ou entrega externa. Reauth código SMTP passou com sessão inicial sintética; não é Google público.
- CA16: direitos/pins NEG/POS passaram, gate ACL/auth NEG/POS, restart/backup CURRENT/relay passaram. Segurança encerrou esses bloqueantes específicos, sem concluir CA16/18 globalmente.

Os 18 CAs permanecem sujeitos ao corte final, QA/matriz e segurança. Estado corrente/resultados completos vivem no [relatório da etapa](../etapas/11-acabamento-deploy/relatorio.md) e [PROGRESSO](../PROGRESSO.md). Este runbook não muda regra de produto ou concede implantação remota.

## Gate adicional antes de prepare/finalize — ACL/auth T11-L

Não reutilizar POS de direitos10 como prova de autorização atual. `restore-acl-inventory.sql` deve comparar origem atual quiescente e clone pós-journal, cobrindo identidade/credenciais/ativo/permissões, sessões/prova nativa/tickets, membros/papéis/reingresso/convites, audiência/documentos/central/push e **preferências de opt-out**. Projeções privadas usam hashes; não imprimir/publicar inventário.

`lab11-rights-gate.sh` assina `acl_sha256` junto dos direitos/objetos e vínculos de ledger/proof/WAL/fence. `restore-cutover-verify.py` exige esse campo, recalcula estado no clone e verifica de novo no primário reiniciado por prepare/finalize. Recibo antigo sem ACL ou divergência conserva bloqueio. Não eliminar CA08_GATE_PENDING/manipular ACTIVE_RESTORE para forçar abertura.

Negativo real de membro removido rejeitou uma linha Membro divergente. Negativo separado de opt-out usou transação com rollback e rejeitou uma linha Usuario divergente. POS final ACL/direitos/objetos e ledger passou, com HMACs válidos ligados à mesma operação/época/fence/watermark e acl_sha256. Backup CURRENT `snapshot.T1fmz1pV` e `lab11-active stop/up` passaram: TLS confiável em ready/entrar e relay 200, web b1c9. D ativo fez login nativo novo e recebeu 404 duas vezes. Segurança adendo 21:46 encerrou os bloqueantes específicos de ACL/direitos/opt-out; não é aprovação global CA16/18. Ferramenta RPO versionada passou exit 0 e reproduz 26,280613 s / 13 COMMITs de exercício anterior; não é RTO ACL novo. E2E01 interrompido143/-15 e focos não aprovam integral; QA recebeu janela exclusiva para RNF10/WebKit/calibração/80 amostras, sem resultado antecipado, cujo primeiro frame persistido não foi comprovado em Chromium/no-store. Novo estado deve ser incorporado ao [relatório](../etapas/11-acabamento-deploy/relatorio.md), sem inferência a partir de fixture ou parecer de fonte.
