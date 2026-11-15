# Movimento

> **Contém:** as animações da interface (nome, onde, especificação) e a regra de movimento reduzido.
> **Origem:** guia `varal-ui` do canvas Doop `k0kB5dc-Vo` e `docs/especificacao-varal.md`, seção 10.

Toda animação é CSS e é desligada com `@media (prefers-reduced-motion: reduce)`.

## Aplicação na Etapa 02

Autenticação usa `swing` nas três contas, entrada `drop`, `sheet-up` na folha mobile e `rise` no formulário desktop. Em 13/11/2026, o dono aprovou seguir o **guia** para a folha: `translateY(100%) → 0`, `0,5s`, resolvendo a diferença do HTML do frame (40px, 0,6s). Nenhum frame foi alterado. O reduced motion desliga essas animações e o efeito de pressão.

## Aplicação na Etapa 03

Convite usa `sheet-up` (11) e `modal-pop` (M05), primeira folha/modal reutilizável do app, e `shine` na caixa do link. O dono aprovou em 14/11/2026 seguir o frame no `shine`: 2,4s, atraso 0,6s (M05) a 0,8s (11), **2 repetições e para**; o guia `varal-ui` passou a listá-lo. Página do grupo usa `rise`; `grow` não roda enquanto as casas não têm contas (barra escondida). Movimento reduzido desliga tudo.

## Aplicação na Etapa 04

Início usa `count-up` no total do mês, `swing` nas contas do varal e `rise` em "Precisa de atenção"; Contas usa `rise` na lista, `swing` na conta pendurada do detalhe e `slide-in` no painel do D03; o selo Vencida usa `badge-pulse`; formulário e "Configurações" usam `sheet-up`/`modal-pop`. `grow` não roda: a barra de pagas só entra na 07. Movimento reduzido desliga tudo.

## Tabela do guia varal-ui (usar esta no código; conferida em 14/11/2026)

No mobile as ações sobem em folhas (`sheet-up`); a partir de 1024px viram modais (`modal-pop`), e o detalhe e a gaveta de avisos entram com `slide-in`. Regra responsiva em [README.md](README.md#regra-responsiva).

| Nome | Onde | Spec |
| --- | --- | --- |
| swing | Contas no varal | rotate ±5–7deg, 3–3.6s ease-in-out infinite, transform-origin topo, delays defasados |
| rise | Entrada de cards/listas | translateY 14px→0 + fade, .5s cubic-bezier(.2,.8,.2,1), stagger 60–80ms |
| grow | Barra de progresso do mês | width 0→valor, 1.4s, delay .4s |
| count-up | Total do mês | 0→valor em 1.2s, ease-out cúbico (requestAnimationFrame) |
| sheet-up | Folhas inferiores (mobile) | translateY 100%→0, .5s cubic-bezier(.2,.9,.25,1) |
| modal-pop | Modais (desktop) | scale .96→1 + fade, .3s |
| slide-in | Painel de detalhe e gaveta (desktop) | translateX 24px→0 + fade, .45s |
| scan | Leitura do PDF | linha verde percorre a prévia; campos lidos ganham moldura âmbar com rótulo |
| shine | Link de convite recém-gerado | brilho âmbar (rgba(245,165,36,.18)) atravessa a caixa, 2.4s ease-in-out, delay .6–.8s, **2 repetições e para** |
| pop + draw | Check de sucesso | scale .3→1.12→1 (.6s) e stroke-dashoffset do check (.5s) |
| badge-pulse | Ícone do selo Vencida | scale 1→1.18, 1.8s infinite |
| press | Botões | :active scale(.97) |

## Da especificação

### Referência visual e movimento

A interface segue o [UGLYCASH](https://onepagelove.com/uglycash): números enormes, cards brancos bem arredondados sobre fundo cinza, botões em pílula e um único bloco de cor forte por tela (o azul-marinho do topo do Início). O total do mês e o valor no detalhe usam um **número-herói** de 48 px em Bricolage 800, com os centavos em 24 px e 55% de opacidade.

O varal com as contas é o motivo da marca dentro do app: aparece no resumo do Início, no Detalhe e na confirmação de pagamento, quando a conta "sai do varal".

| Animação | Onde | Especificação |
| --- | --- | --- |
| Balanço (`swing`) | Contas penduradas | Rotação de ±5° a ±7°, 3 a 3,6 s, infinita, origem no topo, atrasos diferentes por conta |
| Entrada (`rise`) | Cards e listas | Sobe 14 px e aparece em 0,5 s, com 80 ms entre itens |
| Barra do mês (`grow`) | Progresso de pagas | Largura de 0 ao valor em 1,4 s |
| Contagem | Total do mês | De 0 ao valor em 1,2 s, desacelerando |
| Folha (`sheet-up`) | Nova conta, pagamento, convite | Sobe de baixo em 0,5 s |
| Sucesso (`pop` + traço) | Conta paga | Círculo cresce com leve rebote e o check é desenhado |
| Pulso | Ícone do selo Vencida | Escala de 1 para 1,18 a cada 1,8 s |
| Toque | Botões e filtros | Encolhe para 97% ao pressionar |

Toda animação é desligada quando o sistema pede movimento reduzido (`prefers-reduced-motion`).
