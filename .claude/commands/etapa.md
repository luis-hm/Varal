Execute a PRÓXIMA etapa pendente do Varal, seguindo exatamente este fluxo:
1. Leia docs/PROGRESSO.md e docs/etapas/README.md; identifique a próxima etapa "pendente". Se houver uma "em andamento", continue ela. Leia AO VIVO, pelo conector claude.ai Claude Docs, o documento "Varal — Ajustes" (doc ce521944-15d6-44a5-b70c-f0790e03de41) e separe os itens não marcados que tocam esta etapa: eles entram na spec.
2. Se a etapa anterior estiver concluída e ainda fora da main, faça o merge local dela na main (`git merge --no-ff`): rodar /etapa conta como aprovação da etapa anterior. Depois crie a branch etapa/NN-slug a partir da main. Push só quando eu pedir.
3. Delegue ao varal-docs: spec.md, plano.md e tarefas.md da etapa (lendo só os docs que ela cita), incluindo os itens do documento de ajustes separados no passo 1.
4. Mostre-me um resumo (escopo, RF/CU/RN, telas do Doop mobile e desktop, ajustes incluídos, riscos) e PARE aguardando meu "ok". Não escreva código antes do ok.
5. Com o ok, execute tarefas.md em ordem, delegando: varal-boletos → varal-backend → `make types` → varal-frontend → varal-devops (se precisar) → varal-qa → varal-seguranca → varal-docs.
6. Revisão de ajustes (antes do relatório): leia de novo o documento "Varal — Ajustes" e, para cada item não marcado:
   - toca algo já construído → aplique, com commit `fix(ajustes): …`, e marque o item no documento acrescentando " — feito na etapa NN" (nunca apague nem reescreva itens);
   - é de etapa futura → deixe pendente (entra na spec da etapa dele);
   - é ambíguo ou exige mudar o canvas do Doop → não aplique; pergunte no chat;
   - muda regra de negócio → registre ADR em docs/arquitetura/adr/ e uma linha no log do PROGRESSO.md.
   O relatorio.md ganha as seções "Ajustes aplicados" e "Ajustes pendentes".
7. Definição de pronto: `make test` e `make lint` verdes; tipos sincronizados; critérios de aceite cobertos por testes; telas comparadas com o Doop em 390×844 e 1440×900; revisão de segurança sem bloqueantes; ajustes revisados; docs, PROGRESSO.md e matriz atualizados.
8. Faça commits locais em Conventional Commits (pt-BR) na branch da etapa. NÃO faça push sem eu pedir; o único merge permitido é o do passo 2.
9. Mostre o relatório da etapa e PARE. A próxima etapa só começa quando eu rodar /etapa de novo.
Argumento opcional: $ARGUMENTS (ex.: "03" para executar uma etapa específica, se as anteriores estiverem concluídas).
