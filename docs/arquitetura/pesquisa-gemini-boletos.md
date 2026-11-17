# Pesquisa — Gemini API para leitura de boletos

> **Contém:** capacidades, limites e tratamento de dados observados nas fontes oficiais do Google para subsidiar o plano de IA do Varal.
> **Origem:** pesquisa documental solicitada pelo dono em 16/11/2026; páginas oficiais consultadas nesta data, sem chamada autenticada, leitura da chave ou envio de PDF.

## Estado da pesquisa

Este documento registra o que a documentação pública informa. Não comprova que a chave do projeto funciona, que tem acesso a um modelo, que possui determinada cota ou que um boleto foi interpretado corretamente. As páginas são atualizadas pelo Google; conferir novamente antes de implementar ou trocar o modelo. As URLs antigas `ai.google.dev/gemini-api/docs/…` redirecionaram para `aistudio.google.com/docs/…` nesta consulta.

## Leitura de PDF

Gemini aceita PDF com compreensão visual e textual: pode interpretar texto, imagens, tabelas e a disposição da página, além de produzir extração estruturada. Isso torna possível avaliar PDFs digitalizados, sem equivaler a garantia de OCR ou acerto de números pequenos. A documentação informa limite de 50 MB e 1000 páginas por PDF, sujeito também à janela de contexto. São limites do provedor; não autorizam ampliar o limite de upload do Varal. [Document understanding](https://aistudio.google.com/docs/document-processing).

Para um boleto pequeno processado uma vez, a documentação apresenta envio inline dos bytes. Para arquivos maiores ou reutilizados em várias requisições, apresenta a Files API. Inferência para o Varal: avaliar inicialmente inline e manter o original no Silo, sem tornar o bucket público ou fornecer URL assinada ao modelo. [PDF inline e Files API](https://aistudio.google.com/docs/document-processing#inline_data).

## Arquivos remotos e retenção não são a mesma coisa

A Files API informa exclusão automática em 48 horas e permite exclusão explícita via `client.files.delete(name=arquivo.name)`. O serviço comporta 20 GB por projeto e arquivos de até 2 GB em geral; o processamento de PDF mantém seu limite específico menor. Uploads não são armazenamento durável nem substituem Silo ou backup. [Files API](https://aistudio.google.com/docs/files#usage-info), [exclusão explícita](https://aistudio.google.com/docs/files#delete-uploaded).

Excluir um recurso Files, evitar upload reutilizável ou usar inline não representa promessa de ausência de outros logs do provedor. Esses controles têm finalidades diferentes dos termos de uso de dados e do monitoramento de abuso, descritos adiante.

## Contrato estruturado

Structured outputs aceita um subconjunto de JSON Schema e possui integração com Pydantic no SDK Python. A documentação recomenda validar valores na aplicação: JSON válido pode conter informação incorreta. Algumas restrições, como `minLength` e `maxLength`, são ignoradas pelo servidor; schemas complexos podem ser rejeitados. [Structured outputs](https://aistudio.google.com/docs/structured-output#limitations).

Consequência para o plano: schema simples com valores ausentes representados por `null`, campos de evidência/página e candidatos separados; Django valida tipos, limites, dinheiro em centavos, datas e dígitos verificadores. O resultado do modelo é uma sugestão, não uma autorização para criar lançamento, alterar valor ou pagar. Essa é recomendação para o Varal, não capacidade prometida pelo Google.

## SDK, chave e modo sem histórico

O SDK detecta automaticamente `GEMINI_API_KEY` ou `GOOGLE_API_KEY`; quando ambas existem, a segunda tem precedência. `API_KEY_GOOGLE`, escolhido pelo dono, exige leitura explícita pela aplicação e passagem ao cliente. É possível preservar esse nome privado, sem renomear ou copiar o segredo. [Using Gemini API keys](https://aistudio.google.com/docs/api-key#setup-environment).

Exemplo de inicialização proposta, não executado e ainda não implementado no Varal:

```python
import os
from google import genai

client = genai.Client(api_key=os.environ["API_KEY_GOOGLE"])
```

A documentação atual recomenda Interactions API para novos projetos e continua suportando `generateContent`, classificada como interface legada. Interactions armazena requisições por padrão (`store=true`): 55 dias no plano pago e um dia no gratuito. `store=false` desativa esse armazenamento de interações e impede histórico por `previous_interaction_id` e execução em background do provedor. O Celery local pode continuar coordenando o trabalho. `store=false` não equivale a zero retenção de abuso. [Interactions API e retenção](https://aistudio.google.com/docs/interactions-overview#data-storage-retention).

## Modelo e custo: candidato, não escolha já aprovada

O catálogo consultado marca Gemini 3.5 Flash-Lite como estável e sua ficha confirma entrada PDF e saída estruturada. É candidato a benchmark por ser voltado a extração simples e custo baixo; falta comparar acurácia, latência e custo no corpus sintético do Varal. A mesma consulta informa acesso aos modelos 2.5 limitado a usuários anteriores; não adotar uma indicação antiga de 2.5 como garantia para uma chave nova. [Catálogo](https://aistudio.google.com/docs/models), [ficha 3.5 Flash-Lite](https://aistudio.google.com/docs/models/gemini-3.5-flash-lite).

Na tabela Standard consultada, `gemini-3.5-flash-lite` possui entrada/saída gratuitas no Free Tier; no pago, US$ 0,30 por milhão de tokens de entrada e US$ 2,50 por milhão de saída, incluindo thinking. São preços observados, não orçamento contratado. Medir `usage` real, retries e erros antes de estimar custo por boleto. Não habilitar cobrança, fallback para modelo mais caro ou ferramentas de busca implicitamente. [Preços](https://aistudio.google.com/docs/pricing#gemini-3.5-flash-lite).

As cotas são por projeto, não por chave; RPM, TPM e RPD variam por modelo e nível. Exceder qualquer dimensão gera limitação, e a capacidade não é garantida. A cota efetiva precisa ser consultada no AI Studio do projeto. Não inferir “X boletos grátis/dia” a partir de uma tabela antiga ou da existência da chave. [Rate limits](https://aistudio.google.com/docs/rate-limits), [limites do projeto](https://aistudio.google.com/rate-limit?timeRange=last-28-days).

## Dados de clientes: diferença essencial entre gratuito e pago

Os termos em vigor desde 23/03/2026 dizem que, nos Unpaid Services, conteúdo e respostas podem melhorar produtos e tecnologias do Google, com revisão humana, e orientam não enviar informação pessoal, sensível ou confidencial. Há exceção de tratamento para EEE, Suíça e Reino Unido; isso não é hipótese aplicável automaticamente à operação brasileira do Varal. Para a API, o regime Paid Services depende de projeto associado a conta de faturamento ativa; nesse regime prompts e respostas não são usados para melhorar produtos, sob os termos de processamento indicados pelo Google. [Termos — gratuito e pago](https://aistudio.google.com/docs/terms#unpaid-services).

A política de monitoramento de abuso informa retenção por 55 dias de prompts, contexto e respostas; conteúdo sinalizado pode ser revisado por pessoal autorizado. Não prometer que ativar faturamento, excluir Files ou usar `store=false` elimina todo armazenamento ou toda revisão humana. [Abuse monitoring](https://aistudio.google.com/docs/usage-policies#how-we-handle-data).

Recomendação para o plano: gratuito somente com PDFs totalmente sintéticos, sem identificadores ou dados de clientes. Antes de enviar documento real, decidir e registrar finalidade, regime/conta, dados mínimos, transparência ao usuário, retenção e exclusão, incluindo os limites do provedor. Anonimização parcial de CPF/nome não garante que um PDF inteiro ficou anônimo: linha digitável, Pix, metadados, textos e imagens também podem identificar pessoas. A presença da chave não autoriza ativação automática em produção.

## Melhoria contínua

Guardar conversas ou chamar repetidamente a API não implementa aprendizado personalizado do Varal. A recomendação de engenharia é versionar prompt/schema/validador/modelo; registrar correções autorizadas e classificadas; gerar casos sintéticos de regressão e comparar versões em conjunto de teste separado. Só promover mudança quando reduzir erros sem regressão relevante. A política de dados acima impede usar o gratuito como repositório de exemplos reais de clientes.

Ainda é necessário avaliar a execução real com documentos sintéticos, acesso da chave ao modelo, cotas do projeto e desempenho campo a campo. Nenhum desses resultados foi medido nesta pesquisa.
