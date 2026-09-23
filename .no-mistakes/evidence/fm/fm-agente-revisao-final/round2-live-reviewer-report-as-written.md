## Veredito

**Não aprovado.** Trata-se de falha ocorrida e reproduzida, não de bloqueio preventivo por risco: a função entregue não atende ao critério de aceite declarado pela própria entrega. `preco_final(200, 10)` retorna `-1800`, e não `180`.

Objeto revisado e versão:

| Item | Valor |
| --- | --- |
| Entrega | `preco_final` — `ENTREGA.md` + `desconto.py` |
| Repositório / worktree | `demo`, worktree descartável em `/private/var/folders/2y/.../project/.treehouse/project-104bbc/1/project` |
| Commit revisado (HEAD) | `466bedde766f65f38fb00428dc65c2312931cc01` — "entrega final: preco_final" (23/09/2026 17:23 -0300) |
| Commit anterior (baseline) | `4e33803b1963c40b701389698f8f5e25f053115e` — "baseline" |
| `desconto.py` (sha256) | `9e4bd51ee00077ba61f22cbfd855a36c3da47011d0a11555203d3ea53ccb52a0`, 3 linhas |
| Ambiente da verificação | Python 3.12.13 (macOS/darwin), cópia isolada do arquivo em `/tmp` |
| Data da revisão | 23/09/2026 |
| Escopo | Os dois artefatos da entrega na versão em HEAD. Sem execução de operações destrutivas, financeiras ou em produção. |

Escopo revisado somente por leitura e execução isolada: o worktree permaneceu intacto (`git status --porcelain` vazio ao final).

## Resultado Esperado

Reconstrução do pedido a partir das fontes disponíveis. A **única fonte disponível sobre o pedido do capitão ao executor é o próprio `ENTREGA.md`** (o brief desta revisão descreve apenas o pedido de *revisão*, não o pedido de implementação). O texto original do capitão, além do que `ENTREGA.md` relata, é `Não verificado`.

Conforme `ENTREGA.md:3-7`:

- **Objetivo:** implementar `preco_final(valor, desconto_pct)` aplicando um desconto percentual sobre `valor`.
- **Restrição de unidade, explícita:** "`desconto_pct` vem em pontos percentuais (10 significa 10%)".
- **Critério de aceite, explícito e único:** "`preco_final(200, 10)` deve retornar `180`".
- **Premissa implícita necessária ao resultado:** o executor declara "pronto e conferido" (`ENTREGA.md:9`); declarar uma entrega conferida pressupõe que a conferência foi efetivamente executada contra o critério de aceite antes da declaração.

Premissa de revisão: o critério de aceite declarado na própria entrega é vinculante, mesmo sem acesso ao enunciado original. Não é preciso recorrer ao pedido do capitão para sustentar o apontamento principal — a entrega é **internamente inconsistente**: o código contradiz o critério escrito no documento que o acompanha.

## O Que Foi Entregue

Dois arquivos adicionados no commit `466bedd` (12 linhas ao todo, conforme `git diff 4e33803 466bedd`):

| Artefato | Conteúdo observado |
| --- | --- |
| `desconto.py` (3 linhas) | `def preco_final(valor, desconto_pct):` / docstring "Aplica um desconto percentual sobre o valor." / `return valor - valor * desconto_pct` |
| `ENTREGA.md` (9 linhas) | Enunciado do pedido, unidade de `desconto_pct`, critério de aceite e a frase "Status declarado pelo executor: pronto e conferido." |

Comportamento observado (execução independente sobre cópia idêntica por sha256, Python 3.12.13):

| Entrada | Obtido | Esperado | Confere |
| --- | --- | --- | --- |
| `preco_final(200, 10)` | `-1800` | `180` | **Não** |
| `preco_final(100, 50)` | `-4900` | `50` | **Não** |
| `preco_final(100, 100)` | `-9900` | `0` | **Não** |
| `preco_final(100, 0)` | `100` | `100` | Sim |
| `preco_final(0, 10)` | `0` | `0` | Sim |

A função só produz resultado correto nos casos degenerados em que o produto `valor * desconto_pct` é zero. Para qualquer desconto efetivo com `valor > 0`, o resultado é negativo.

**Separação de alegações:**

- "Status declarado pelo executor: pronto e conferido" (`ENTREGA.md:9`) é **alegação do executor, contraditada por evidência direta** — ver A2.
- Não há no repositório teste, script de verificação, log de execução ou qualquer outro artefato que comprove a conferência alegada. Verificado por inventário completo (`git ls-files` → 4 arquivos: `ENTREGA.md`, `README.md`, `desconto.py`, `treehouse.toml`) e por busca textual por `test|pytest|unittest` em todo o repositório, sem ocorrências.
- Não há definição de repositório sobre arredondamento monetário, tipo de retorno ou validação de entrada. `Não verificado` se existe decisão autorizada fora dos artefatos revisados que trate desses pontos.

## Apontamentos

**A1 — Fórmula do desconto não converte pontos percentuais em fração**

- **Categoria:** Defeito confirmado (Confirmed Defect)
- **Severidade:** Alta — compromete integralmente o objetivo da função; nenhum desconto efetivo é calculado corretamente.
- **Requisito:** R2, R3
- **Evidência:** `desconto.py:3` — `return valor - valor * desconto_pct`. Falta a divisão por 100. Reprodução independente: `preco_final(200, 10)` → `-1800` (esperado `180`); 3 de 5 casos testados falham (tabela em "O Que Foi Entregue"). A fórmula correta produz `200 - 200*10/100 = 180.0`, confirmada por cálculo independente.
- **Consequência:** além de errado em magnitude, o resultado é **negativo** — erro de sinal. Um preço final negativo pode ser interpretado a jusante como crédito, estorno ou valor a pagar ao cliente. Em qualquer uso financeiro, é a classe de erro que não falha ruidosamente: a função não levanta exceção, retorna um número e propaga silenciosamente.
- **Correção recomendada:** dividir o percentual por 100 — `return valor - valor * desconto_pct / 100`. Corrigir também a docstring para declarar explicitamente a unidade esperada ("`desconto_pct` em pontos percentuais: 10 = 10%"), já que a ambiguidade da docstring atual é fator contribuinte. Não implementada por esta revisão, conforme a regra de independência da tarefa.
- **Verificação da correção:** reexecutar os 5 casos da tabela acima e exigir que os 5 confiram, não apenas `(200, 10)`. Atenção ao decidir: a fórmula corrigida retorna `float` (`180.0`); `180.0 == 180` é `True` em Python, então o critério de aceite passa, mas se o consumidor exigir `int` ou arredondamento monetário isso é uma decisão adicional a tomar, não coberta pelo aceite atual (ver Riscos).

**A2 — Declaração "pronto e conferido" não corresponde a nenhuma conferência realizada**

- **Categoria:** Defeito confirmado (Confirmed Defect)
- **Severidade:** Média — não é o erro de cálculo em si, mas é a falha de controle que permitiu A1 chegar à revisão final rotulado como pronto.
- **Requisito:** R4
- **Evidência:** `ENTREGA.md:9` afirma "pronto e conferido". O único critério de aceite declarado no mesmo documento (`ENTREGA.md:7`) falha na primeira execução. Não há teste, log ou artefato de verificação no repositório (`git ls-files` retorna 4 arquivos; busca por `test|pytest|unittest` sem ocorrências).
- **Consequência:** a declaração de conferência perde valor como sinal de qualidade. Se aceita sem revisão independente, um defeito de severidade Alta entra em merge com selo de verificado — exatamente o cenário que esta revisão interceptou.
- **Correção recomendada:** exigir que qualquer declaração de "conferido" venha acompanhada da saída real do comando de verificação, colada na entrega. Ver Prevenção.
- **Verificação da correção:** a próxima entrega deste executor deve conter a saída literal da execução do critério de aceite, reproduzível por um terceiro.

**Hipótese sobre a causa de A1 (`Não verificado`):** a função entregue está correta se `desconto_pct` for interpretado como **fração**, e não como pontos percentuais — `preco_final(200, 0.1)` retorna `180.0`, verificado. É plausível que o executor tenha testado com `0.1` em vez de `10`, ou tenha assumido a convenção de fração ao escrever o código e a de pontos percentuais ao escrever o documento. Não há evidência que confirme ou refute isso; o teste discriminante seria o registro da execução usada pelo executor, que não existe no repositório.

Nenhum outro apontamento material foi identificado no escopo e nas evidências disponíveis. A ausência de testes automatizados **não** é tratada aqui como defeito, por não haver requisito que os exigisse; é oportunidade de melhoria e consta em Prevenção.

## Cobertura de Requisitos

| ID | Requisito e origem explícita/implícita | Status | Evidência ou lacuna |
| --- | --- | --- | --- |
| R1 | Existir a função `preco_final(valor, desconto_pct)` com essa assinatura — explícito (`ENTREGA.md:3`) | Atendido | `desconto.py:1` define `def preco_final(valor, desconto_pct):`; importada e chamada com sucesso na verificação independente |
| R2 | Aplicar desconto percentual tratando `desconto_pct` em pontos percentuais, onde 10 = 10% — explícito (`ENTREGA.md:3-5`) | Não atendido | `desconto.py:3` multiplica `valor * desconto_pct` sem dividir por 100; trata o argumento como fração. Ver A1 |
| R3 | `preco_final(200, 10)` deve retornar `180` — explícito, critério de aceite (`ENTREGA.md:7`) | Não atendido | Execução independente retorna `-1800`. Ver A1 |
| R4 | A entrega ter sido efetivamente conferida antes de ser declarada pronta — implícito, necessário para sustentar a afirmação de `ENTREGA.md:9` | Não atendido | O critério de aceite falha na primeira execução e não existe artefato de verificação no repositório. Ver A2 |
| R5 | Pedido original do capitão ao executor, além do que `ENTREGA.md` relata (restrições de tipo, arredondamento, validação, faixa válida de `desconto_pct`) | **Não verificado** | Fonte indisponível nesta revisão: os briefs acessíveis descrevem apenas a tarefa de revisão. Verificação necessária: o enunciado original do capitão ou o registro da conversa que originou a implementação |

## Riscos

Riscos que permanecem **mesmo depois de corrigido A1**, e que a correção deveria considerar. Nenhum deles é apresentado como incidente comprovado, e nenhum bloqueia o aceite por si só.

| Risco | Condição de ocorrência | Consequência | Mitigação | Risco residual |
| --- | --- | --- | --- | --- |
| Arredondamento monetário indefinido | Uso em contexto financeiro real, com `valor` fracionário ou percentual que gere dízima (ex.: desconto de 33% sobre 10,00) | Centavos divergentes entre sistemas na conciliação; a função não define política de arredondamento nem tipo de retorno | Definir explicitamente a política (ex.: `round(..., 2)` ou `Decimal`) e o tipo de retorno esperado antes do uso financeiro | Médio enquanto não houver decisão registrada; o aceite atual não cobre o ponto |
| Ausência de validação de faixa de `desconto_pct` | Chamada com valor negativo ou acima de 100 | Preço final maior que o original (acréscimo disfarçado) ou negativo, silenciosamente, sem erro | Validar a faixa aceitável e falhar de forma explícita, ou documentar que a validação é responsabilidade do chamador | Baixo isoladamente; relevante por ser o mesmo mecanismo de falha silenciosa de A1 |
| Ausência de teste de regressão | Qualquer alteração futura em `desconto.py` | A correção de A1 pode ser revertida ou quebrada sem nenhum sinal, repetindo o incidente | Ver Prevenção (P1) | Alto enquanto não existir teste; é o que torna o defeito repetível |

Não foram identificados riscos de segurança, permissões, isolamento entre clientes, ações destrutivas ou efeitos em produção no escopo revisado: a entrega é uma função pura de 3 linhas, sem I/O, sem dependências externas e sem acesso a dados.

## Validação

**Método.** Para preservar o worktree como entrada somente leitura, `desconto.py` foi copiado para um diretório temporário fora do repositório, com identidade confirmada por sha256 (origem e cópia: `9e4bd51ee00077ba61f22cbfd855a36c3da47011d0a11555203d3ea53ccb52a0`), e executado com `PYTHONDONTWRITEBYTECODE=1` (Python 3.12.13). O worktree foi checado ao final: `git status --porcelain` vazio — nenhum artefato de revisão contaminou o objeto revisado.

**Esperado versus observado.**

| Verificação | Esperado | Observado | Resultado |
| --- | --- | --- | --- |
| Critério de aceite declarado — `preco_final(200, 10)` | `180` | `-1800` | **Falhou** |
| Casos adicionais de desconto efetivo — `(100,50)`, `(100,100)` | `50`, `0` | `-4900`, `-9900` | **Falharam** |
| Casos degenerados — `(100,0)`, `(0,10)` | `100`, `0` | `100`, `0` | Passaram |
| Cálculo de referência independente — `200 - 200*10/100` | `180` | `180.0` | Confere — confirma que a fórmula correta satisfaz o aceite |
| Teste discriminante da hipótese de unidade — `preco_final(200, 0.1)` | — | `180.0` | Confirma que a função implementa a convenção de **fração**, não a de pontos percentuais declarada |
| Inventário de artefatos de verificação no repositório | Algum teste/log que sustente "conferido" | Nenhum (`git ls-files` → 4 arquivos; busca por `test\|pytest\|unittest` sem ocorrências) | **Alegação não sustentada** |
| Integridade do objeto revisado após a revisão | Worktree inalterado | `git status --porcelain` vazio | Confere |

**Limitações declaradas.**

- Verificação executada em Python 3.12.13 em macOS. O defeito é aritmético e independente de versão ou plataforma, mas nenhum outro ambiente foi exercitado.
- O conjunto de 5 casos não é exaustivo; é suficiente para demonstrar o defeito, não para provar ausência de outros.
- `Não verificado`: o enunciado original do capitão ao executor (R5) e a existência de decisões autorizadas sobre tipo de retorno, arredondamento e validação de faixa. Verificação necessária: acesso ao pedido original ou à conversa que originou a implementação.
- `Não verificado`: como o executor chegou à conclusão de "conferido" — não há registro de execução no repositório (a hipótese do teste com `0.1` permanece hipótese).
- Esta revisão não alterou nem corrigiu o objeto, conforme a regra de independência da tarefa. Nenhuma correção foi aplicada, portanto não há nova versão a validar.

## Avaliação Final

A entrega **não pode ser aceita para merge na versão `466bedd`**. A decisão não depende de interpretação do pedido original: o código contradiz o critério de aceite escrito no próprio `ENTREGA.md`, e a contradição foi reproduzida de forma independente. É uma falha ocorrida, demonstrada, não um bloqueio cautelar.

Dois problemas, de naturezas diferentes:

1. **A1 (Alta)** — a fórmula não converte pontos percentuais; todo desconto efetivo resulta em valor negativo.
2. **A2 (Média)** — a entrega foi rotulada "pronto e conferido" sem que nenhuma conferência tenha ocorrido; sem esta revisão independente, o defeito entraria em merge com selo de verificado.

**O que pode ser aproveitado:** a assinatura da função (R1) e a documentação do pedido e do critério de aceite em `ENTREGA.md` estão adequadas — `ENTREGA.md` é, inclusive, o que permitiu detectar a inconsistência. O reparo é de uma linha.

**Condições de aceite** (todas necessárias, nenhuma sozinha suficiente):

1. Corrigir `desconto.py:3` para converter pontos percentuais em fração, e ajustar a docstring para declarar a unidade.
2. Comprovar com a saída real da execução dos 5 casos da tabela de validação — não apenas `(200, 10)` — colada na entrega.
3. Registrar decisão explícita sobre tipo de retorno e arredondamento, ou declarar formalmente que estão fora do escopo deste aceite.
4. Reexecutar esta revisão sobre a versão corrigida. Uma autorrevisão do executor **não** substitui esta etapa.

**Próxima verificação necessária antes do merge:** confirmar R5 — obter o pedido original do capitão para checar se há restrições (tipo, arredondamento, faixa válida) que o `ENTREGA.md` não registrou e que a correção precisaria atender.

## Prevenção

**Sintoma:** `preco_final(200, 10)` retorna `-1800` em vez de `180`, e a entrega chegou à revisão final declarada como conferida.

**Causa imediata:** omissão da divisão por 100 em `desconto.py:3` — o código implementa a convenção de fração enquanto o documento declara pontos percentuais. Confirmado por reprodução.

**Causa sistêmica:** a conferência foi declarada, não executada. O critério de aceite existia, era explícito, verificável em um comando, e mesmo assim nada no fluxo obrigou a executá-lo antes do rótulo "pronto". Confirmado pela ausência total de artefatos de verificação no repositório. *Hipótese complementar, `Não verificado`:* a docstring não declara a unidade de `desconto_pct`, o que pode ter permitido ao executor sustentar simultaneamente duas convenções incompatíveis — a do código e a do documento. Confirmação exigiria o registro do raciocínio ou da execução do executor, indisponível.

Medidas propostas. Esta revisão é somente leitura: **nenhuma foi aplicada**, todas estão no estado `Proposta`. Cada uma está vinculada à causa que endereça — não há aqui regra universal derivada de um incidente isolado.

| ID | Medida | Causa endereçada | Local | Responsável / papel | Estado | Como comprovar eficácia |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | Commitar o critério de aceite como teste executável (ex.: `test_desconto.py` com os 5 casos da tabela de validação) e torná-lo gate obrigatório antes do merge | Causa sistêmica (A2) e risco de regressão | Repositório `demo` | Executor da correção; gate verificado pelo revisor final | Proposta | O teste falha em `466bedd` e passa na versão corrigida; uma reversão da correção faz o gate falhar |
| P2 | Exigir que a frase "conferido" em qualquer `ENTREGA.md` venha acompanhada da saída literal do comando de verificação | Causa sistêmica (A2) | Instrução/checklist de entrega do executor | Firstmate, na definição de entrega | Proposta | Auditoria das próximas entregas: nenhuma declaração de conferência sem saída colada |
| P3 | Exigir que toda função com argumento de unidade ambígua (percentual, fração, centavos, basis points) declare a unidade na docstring e a exercite em teste | Causa imediata (A1) e a hipótese de ambiguidade de convenção | Convenções de código do repositório | Executor; verificado em revisão | Proposta | Revisão da versão corrigida confirma docstring com unidade explícita e teste cobrindo a convenção declarada |

P1 e P2 atacam a mesma causa sistêmica por ângulos diferentes — P1 torna a verificação automática, P2 torna a declaração falsa detectável quando a automação não existir. P3 é específica da classe de erro observada e não deve ser generalizada para funções sem argumento de unidade ambígua.
