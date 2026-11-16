# Fontes e contrato — extrator PDF da Etapa 06

> **Contém:** fontes, contrato, testes isolados e limites da extração de PDF.
> **Origem:** preparação do especialista de boletos e reauditoria de segurança, antes da integração da Etapa 06.

## Fontes

- [pdfplumber — documentação oficial](https://github.com/jsvine/pdfplumber#loading-a-pdf): `open` aceita objeto binário e senha opcional; método `Page.extract_text` extrai caracteres de páginas; a biblioteca não faz OCR. A versão 0.11.10 testada encapsula exceções do pdfminer em `PdfminerException`, com original em `__context__`.
- RN25–RN29 e `docs/etapas/05-boleto-pix/fontes.md`: validar conteúdo estruturado fora da fronteira HTTP/DRF, especialmente NUL e Unicode inválido; reutilizar parser 05.

## Contrato puro

`extrair_pdf(arquivo: bytes) -> ResultadoPDF`; não acessa rede, filesystem ou banco, não salva conta e não retorna texto integral. Estados `lido`, `conferencia_manual`, `invalido`. O resultado possui `candidatos: tuple[Candidato,...]`, `valor_centavos`, `vencimento`, `data_emissao`, `beneficiario`, `valor_textual_centavos`, `vencimento_textual`, `avisos`. Cada candidato contém `tipo`, `codigo`, `valor_centavos`, `vencimento`, `vencimentos_possiveis`, `avisos`, compatíveis com parser05. Datas são `datetime.date`, conversão explícita ISO para JSON é responsabilidade do backend.

A entrada aceita exclusivamente bytes até 5 MiB; limite de 20 páginas e 200 mil caracteres resulta em conferência manual, sem apresentar resultado parcial como completo. PDF sem texto, sem código, protegido ou erro recuperável também vai para conferência manual. Não-PDF e PDFs com estrutura inválida são `invalido`. PDF válido com texto/código ilegível ainda depende da biblioteca classificar corretamente a estrutura; testar integrações e formatos reais antes da entrega. Não inclui OCR. Cada extração de uma página pode consumir tempo/memória antes de ser possível contar seus caracteres: trabalhador deve aplicar limite de tempo e recursos externos, conforme plano06.

As linhas são limitadas a 47/48 dígitos, pontos e espaços, localizadas por linha e verificadas integralmente pelo parser05; sem captura por recortes de grupos maiores. A deduplicação usa o código normalizado. Mais de um código válido retorna candidatos, exige escolha e omite dados textuais agregados que não podem ser atribuídos com segurança. Com apenas um código, valor e datas codificados prevalecem; data textual só é sugerida se faz parte dos vencimentos possíveis. Os avisos são separados e código não é gravado automaticamente.

Extração textual conservadora: campos rotulados em linhas próprias `Data do documento`, `Vencimento`, `Valor do documento`/`Valor cobrado`, `Beneficiário`, com formatos esperados de data e moeda; múltiplos valores distintos são omitidos. Layout de banco complexo ou rótulos diferentes poderão exigir conferência manual. NUL/surrogates em qualquer texto da extração invalidam a análise estruturada; beneficiário limitado a200 caracteres, resultado do parser e avisos também são validados antes de retornar. Valores e datas textuais não são validados como autenticidade do documento.

Testes geram PDFs sintéticos em memória via reportlab, sem dados reais; cobrem bancário, arrecadação, texto, duplicados, ambiguidade, divergências, criptografia, não-PDF, múltiplas páginas, limites e Unicode adversário. Ambiente isolado `/tmp/varal-pdf06-venv`: pdfplumber 0.11.10, reportlab 5.1.0, pytest 9.2.0. Instalação não alterou dependências do repositório. Foram executados 12 testes sem banco, e Ruff check/format com configuração da API.

## Integração necessária

Após abertura oficial da06, mover o arquivo para o pacote de boletos, ajustar imports dos testes e incluir dependências nas configurações/lock próprios, revisão de segurança e testes de worker e storage. O worker precisa converter explicitamente os dataclasses e datas para JSON e reaplicar validação nos limites da persistência, bem como limitar tempo/recursos e não registrar exceções contendo texto ou dados do documento. A leitura parcial não substitui conferência, nem comprova identidade ou legitimidade da cobrança.

## Ajustes após revisão de segurança

- O catálogo precisa ter árvore `Pages` estruturada (`Type`, `Kids`, `Count`) antes de percorrer/fechar páginas. O PDF sintético com catálogo `/Pages (a)` é classificado como inválido; PDF criptografado, sem texto ou não legível continua em conferência manual.
- Avisos emitidos por `pdfminer`/`pdfplumber` durante a leitura têm mensagem e dados de exceção substituídos por texto fixo, sem conteúdo do arquivo. A fábrica de `LogRecord` previamente configurada é restaurada mesmo em exceção; chamadas desta biblioteca são serializadas e a redação afeta somente a thread leitora. A fábrica é uma configuração global do Python: outra parte que a substitua concorrentemente não participa da trava. Integrar a leitura em processo dedicado, como já previsto, e manter o teste de logs no worker; não afirmar isolamento absoluto diante de alterações simultâneas da configuração global de logging.
- Linhas puramente numéricas consecutivas podem ser reunidas para um código quebrado; cada sequência completa é validada por DV. Runs maiores de dígitos não são recortados para fabricar uma linha válida; códigos completos distintos em linhas adjacentes permanecem candidatos separados. Essa política conservadora pode deixar leituras complexas para conferência manual.

Atualização da verificação: 17 testes sintéticos passaram, incluindo PDF real quebrado em duas linhas, catálogo inválido, conteúdo sensível em warning, restauração do logging e runs maiores. Ruff API verde.
