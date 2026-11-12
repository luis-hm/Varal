Execute a PRÓXIMA etapa pendente do Varal, seguindo exatamente este fluxo:
1. Leia docs/PROGRESSO.md e docs/etapas/README.md; identifique a próxima etapa "pendente". Se houver uma "em andamento", continue ela.
2. Crie a branch etapa/NN-slug a partir da main.
3. Delegue ao varal-docs: spec.md, plano.md e tarefas.md da etapa (lendo só os docs que ela cita).
4. Mostre-me um resumo (escopo, RF/CU/RN, telas do Doop, riscos) e PARE aguardando meu "ok". Não escreva código antes do ok.
5. Com o ok, execute tarefas.md em ordem, delegando: varal-boletos → varal-backend → `make types` → varal-frontend → varal-devops (se precisar) → varal-qa → varal-seguranca → varal-docs.
6. Definição de pronto: `make test` e `make lint` verdes; tipos sincronizados; critérios de aceite cobertos por testes; telas comparadas com o Doop; revisão de segurança sem bloqueantes; docs, PROGRESSO.md e matriz atualizados.
7. Faça commits locais em Conventional Commits (pt-BR) na branch da etapa. NÃO faça push nem merge sem eu pedir.
8. Mostre o relatório da etapa e PARE. A próxima etapa só começa quando eu rodar /etapa de novo.
Argumento opcional: $ARGUMENTS (ex.: "03" para executar uma etapa específica, se as anteriores estiverem concluídas).
