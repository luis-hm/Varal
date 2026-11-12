# Atores e personas

> **Contém:** atores do sistema, o que cada um faz e as personas.
> **Origem:** `docs/especificacao-varal.md`, seção 2.

## 2. Atores e personas

O sistema tem quatro atores humanos e um ator de sistema; o papel vale por grupo, então a mesma pessoa pode ser admin num grupo e pagador em outro.

| Ator | Quem é no cenário | O que faz |
| --- | --- | --- |
| Usuário | Qualquer pessoa com conta no Varal | Gerencia o espaço pessoal, cria grupos e aceita convites |
| Admin do grupo | O estudante ou o pai | Configura o grupo, subgrupos, membros e papéis; faz tudo que o membro faz |
| Membro | Alguém que ajuda a organizar | Cria, edita e paga contas do grupo |
| Pagador | A mãe ou o pai | Vê só as contas atribuídas a ele e as marca como pagas |
| Observador | Alguém que só acompanha | Vê as contas, sem alterar nada |
| Sistema (agendador) | Tarefas automáticas do backend | Gera recorrências, calcula lembretes e envia avisos |

**Personas**

- **Estudante e estagiário:** mora longe dos pais, organiza as contas da família pelo celular. Quer ver de longe se algo venceu.
- **Pai, administra 3 casas:** recebe muitos boletos. Precisa saber o que vence e marcar o que pagou com pouco esforço.
- **Mãe, pagadora:** paga parte das contas. Usa o modo simples: copiar o código e tocar em "Já paguei".
