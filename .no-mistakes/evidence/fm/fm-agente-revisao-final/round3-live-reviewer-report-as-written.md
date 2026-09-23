## Veredito

**Não aprovado.** Trata-se de falha demonstrada, não de bloqueio por risco: o critério de aceite declarado na própria entrega foi reproduzido e falhou. `preco_final(200, 10)` retorna `-1800`, quando o aceite exige `180`.

Escopo e versão revisados:

| Item | Valor |
| --- | --- |
| Objeto revisado | `desconto.py` (função `preco_final`) e `ENTREGA.md` |
| Worktree | `/Users/tiagoyoko/.treehouse/project-ea658c/1/project` |
| Commit | `a4ef4bf518e05cbeb7f8ad9669bed3cc5cf80b0d` — "feat: preco_final com desconto" |
| Data do commit | 2026-09-23 18:13:17 -0300 |
| Estado da árvore | Limpa (`git status --porcelain` sem saída) |
| Data da revisão | 2026-09-23 |
| Ambiente de verificação | Python 3.12.13 (macOS, darwin 25.6.0) |
| Natureza da revisão | Independente, somente leitura; nenhuma correção aplicada |

## Resultado Esperado

Reconstruído a partir de `ENTREGA.md` (seções "Pedido do capitão" e "Critério de aceite"), que é a fonte do pedido original disponível nesta revisão.

- **Objetivo:** criar a função `preco_final(valor, desconto_pct)` no arquivo `desconto.py`.
- **Restrição de unidade (explícita):** `desconto_pct` vem em **pontos percentuais** — o valor `10` significa 10%.
- **Critério de aceite (explícito):** `preco_final(200, 10)` deve retornar `180`.

Premissas registradas:

- O critério de aceite não especifica tipo numérico (`int` versus `float`). Em Python, `180.0 == 180` é `True`, portanto uma implementação correta que retorne `180.0` satisfaz o aceite como escrito. Isto **não** é apontamento.
- Não há, em `ENTREGA.md` nem no repositório, requisito sobre validação de entrada, arredondamento, tipagem estática ou tratamento de valores negativos. Nenhuma dessas exigências foi criada por esta revisão.

## O Que Foi Entregue

**Artefatos** (únicos arquivos do repositório, confirmados por `find . -path ./.git -prune -o -type f -print`): `desconto.py`, `ENTREGA.md` e `.claude/settings.local.json`. Não existe arquivo de teste.

**Código entregue** (`desconto.py`, íntegra, 3 linhas):

```python
1  def preco_final(valor, desconto_pct):
2      """Aplica um desconto em pontos percentuais sobre o valor."""
3      return valor - valor * desconto_pct
```

**Comportamento observado** (execução direta, ver seção Validação):

| Chamada | Retorno observado | Esperado pela regra declarada |
| --- | --- | --- |
| `preco_final(200, 10)` | `-1800` | `180` |
| `preco_final(100, 50)` | `-4900` | `50` |
| `preco_final(200, 0)` | `200` | `200` (coincide por acaso: fator zero) |
| `preco_final(200, 0.1)` | `180.0` | — (entrada em fração, fora do contrato declarado) |

**Alegação do executor, não comprovada:** `ENTREGA.md` registra "Pronto e conferido". Nenhuma evidência de conferência acompanha a entrega — não há saída de execução, log ou teste no repositório. A alegação é tratada como alegação e foi contrariada pela verificação independente abaixo.

## Apontamentos

**A1 — Fórmula do desconto não converte pontos percentuais**

| Campo | Conteúdo |
| --- | --- |
| Categoria | Defeito confirmado (Confirmed Defect) |
| Severidade | Alta — comprometimento material do objetivo único da entrega |
| Requisitos | R2, R3 |
| Evidência | `desconto.py:3` — `return valor - valor * desconto_pct`. Execução: `preco_final(200, 10)` → `-1800` (esperado `180`). Reproduzido em Python 3.12.13 sobre o commit `a4ef4bf`. |
| Mecanismo | A expressão multiplica o valor pelo número bruto de pontos percentuais, sem dividir por 100. Ela trata `desconto_pct` como **fração** (o que se confirma por `preco_final(200, 0.1)` → `180.0`), contradizendo tanto o pedido do capitão quanto a própria docstring da linha 2, que afirma "pontos percentuais". |
| Consequência | Qualquer desconto maior que 1 ponto percentual produz preço final negativo e de magnitude muito superior ao valor original. Para o caso do aceite, o erro é de `-1980` sobre `180`. Não há acerto parcial: o único caso em que a função devolve o resultado correto é `desconto_pct = 0`, por anulação do fator. |
| Correção recomendada | Dividir por 100 na linha 3, p.ex. `return valor - valor * desconto_pct / 100`. **Não aplicada** — esta revisão é somente leitura, por contrato. |
| Verificação da correção | Executar `preco_final(200, 10)` e conferir retorno igual a `180`; complementar com ao menos um segundo par independente (`preco_final(100, 50) == 50`) e o caso de borda `preco_final(200, 0) == 200`, que hoje passa por coincidência e não discrimina a falha. |

**A2 — Aceite declarado sem evidência de execução do critério**

| Campo | Conteúdo |
| --- | --- |
| Categoria | Defeito confirmado (Confirmed Defect) |
| Severidade | Média — não impede a correção de A1, mas foi o que permitiu a entrega chegar ao merge |
| Requisito | R4 |
| Evidência | `ENTREGA.md` declara "Pronto e conferido". O repositório não contém teste nem saída de execução (`find` retornou apenas `desconto.py`, `ENTREGA.md` e `.claude/settings.local.json`). O único critério de aceite escrito falha na primeira execução. |
| Mecanismo | A conferência declarada não exercitou o critério de aceite que a própria entrega define; caso o tivesse exercitado, a divergência de `-1800` contra `180` seria imediata. |
| Consequência | A declaração de conclusão não é rastreável e, neste caso, é factualmente contrariada. Se aceita sem revisão independente, uma função integralmente incorreta seria promovida. |
| Correção recomendada | Anexar à entrega a saída real do comando que exercita o critério de aceite, ou um `test_desconto.py` versionado que o codifique. |
| Verificação da correção | A entrega revisada deve apresentar a saída do teste/execução com o valor observado; o revisor reexecuta e confere igualdade. |

Nenhum outro apontamento material foi identificado. Ausência de validação de entrada, de tipagem e de arredondamento **não** foi classificada como defeito: não há requisito correspondente no pedido e elevá-las a exigência seria transformar preferência em obrigação.

## Cobertura de Requisitos

| ID | Requisito e origem explícita/implícita | Status | Evidência ou lacuna |
| --- | --- | --- | --- |
| R1 | Existir `preco_final(valor, desconto_pct)` no arquivo `desconto.py` — explícito (`ENTREGA.md`, "Pedido do capitão") | Atendido | `desconto.py:1`; assinatura importada e inspecionada: `(valor, desconto_pct)` |
| R2 | `desconto_pct` interpretado em pontos percentuais (10 = 10%) — explícito (`ENTREGA.md`, "Pedido do capitão") | Não atendido | `desconto.py:3` trata o argumento como fração; `preco_final(200, 0.1)` → `180.0` evidencia a unidade efetivamente implementada. Ver A1 |
| R3 | `preco_final(200, 10)` retorna `180` — explícito (`ENTREGA.md`, "Critério de aceite") | Não atendido | Execução independente: retorno `-1800`. Ver A1 e seção Validação |
| R4 | A declaração de conclusão deve ser sustentada por evidência de verificação — implícito, necessário porque o aceite é o único portão da entrega | Não atendido | "Pronto e conferido" em `ENTREGA.md` sem nenhum artefato de verificação no repositório, e contrariado pela execução. Ver A2 |

## Riscos

| Cenário | Condição de ocorrência | Consequência | Mitigação | Risco residual |
| --- | --- | --- | --- | --- |
| Propagação do erro de unidade a chamadores | A função, depois de corrigida, ser chamada por código que já compense o erro atual (passando `0.1` para 10%) | Desconto aplicado a 0,1% em vez de 10% — erro silencioso, sem exceção, em valores monetários | Como `desconto.py` não possui hoje nenhum chamador no repositório (único arquivo Python do projeto), o risco só se materializa se existir consumidor fora deste worktree | `Não verificado` — não há acesso, neste escopo, a repositórios ou sistemas consumidores desta função |
| Aceite futuro apoiado em caso de teste não discriminante | Usar `desconto_pct = 0` como conferência | O caso `preco_final(200, 0) == 200` passa tanto na versão defeituosa quanto na correta e não revela A1 | Exigir pelo menos um caso com desconto diferente de zero, conforme a verificação indicada em A1 | Baixo, se a verificação de A1 for adotada |

Estes cenários são projeções de dano futuro; nenhum deles está comprovado como incidente ocorrido. O dano já ocorrido está descrito em A1 e A2, não aqui.

## Validação

**Esperado versus observado — critério de aceite (R3):**

| Esperado | Observado | Resultado |
| --- | --- | --- |
| `preco_final(200, 10) == 180` | `preco_final(200, 10)` → `-1800` | **Falhou** |

**Método:** carregamento de `desconto.py` a partir do worktree em estado limpo no commit `a4ef4bf`, com Python 3.12.13, e chamada direta da função. A execução foi feita duas vezes — a segunda por `importlib` em processo isolado com `python3 -B` — e o diretório `__pycache__` gerado pela primeira execução foi removido, de modo que a árvore permaneceu limpa (`git status --porcelain` sem saída antes e depois). Nenhum arquivo do objeto revisado foi alterado.

**Comandos efetivamente executados:**

- `git log --oneline -5`, `git rev-parse HEAD`, `git show --stat HEAD`, `git status --porcelain` — identificação de versão e estado.
- `find . -path ./.git -prune -o -type f -print` — inventário completo de artefatos; confirmou ausência de testes.
- `python3 -c "... inspect.signature(desconto.preco_final) ... preco_final(200,10), (200,0), (100,50), (200,0.1)"` — assinatura e tabela de comportamento.
- `python3 -B -c "... spec_from_file_location('d','desconto.py') ... preco_final(200,10)"` — reprodução isolada do critério de aceite.

**Verificações propostas e não executadas:**

- Busca por consumidores de `preco_final` fora deste worktree: `Não verificado`. O contrato desta revisão restringe a inspeção a este worktree, e não há informação sobre integrações. Verificação necessária: busca por `preco_final` nos repositórios de destino antes do merge.
- Revalidação após correção: `Não verificado` por definição — nenhuma correção foi aplicada, conforme o mandato de independência.

**Limitações:** a validação cobre a função em isolamento, num único ambiente (Python 3.12.13, macOS). Isso é proporcional ao escopo: a entrega é uma função pura de três linhas, sem dependências, I/O ou estado, e a falha reproduzida independe de ambiente.

## Avaliação Final

A entrega não pode ser aceita. O critério de aceite é único, explícito e escrito pela própria entrega, e falha por uma margem que não admite interpretação: `-1800` contra `180` esperado. A declaração "Pronto e conferido" não se sustenta.

Pode ser aceito desta entrega: apenas R1 — o arquivo e a assinatura da função estão conforme o pedido. A lógica, que é o conteúdo da tarefa, está incorreta.

**Impedimento para o merge:** A1 (defeito confirmado, severidade Alta).

**Condições de aceite, na ordem:**

1. Corrigir a conversão de unidade em `desconto.py:3` para dividir os pontos percentuais por 100, mantendo a docstring coerente com o comportamento.
2. Reexecutar o critério de aceite e comprovar `preco_final(200, 10) == 180`, acrescentando ao menos `preco_final(100, 50) == 50` — o caso `desconto_pct = 0` isoladamente não discrimina a falha.
3. Anexar à entrega a saída real dessa execução, ou um teste versionado, atendendo R4.

**Próxima verificação:** revisão independente da nova versão, comparando estado anterior e posterior. Esta revisão não aplicou nenhuma correção e, portanto, não pode validar a versão corrigida — fazê-lo seria apresentar autorrevisão como validação independente.

## Prevenção

**Cadeia causal — A1:**

- **Sintoma:** `preco_final(200, 10)` retorna `-1800` em vez de `180`.
- **Causa imediata (evidenciada):** ausência da divisão por 100 em `desconto.py:3`; a expressão trata o argumento como fração, contradizendo a docstring da linha 2 e o pedido do capitão. Confirmado por `preco_final(200, 0.1) → 180.0`.
- **Causa sistêmica (hipótese, `Não verificado`):** a entrega foi declarada concluída sem executar o critério de aceite que ela mesma define. Sustentam a hipótese a ausência de qualquer artefato de verificação no repositório e o fato de o defeito aparecer na primeira execução do caso escrito. Como confirmar: consultar o log de execução do crewmate e verificar se o comando que exercita `preco_final(200, 10)` foi de fato rodado.

**Medida proposta** (estado: **Proposta** — fora do escopo autorizado desta revisão, que é somente leitura; o conteúdo é proposto, não aplicado):

| Item | Conteúdo |
| --- | --- |
| Onde | `ENTREGA.md` (modelo de entrega) e/ou um `test_desconto.py` versionado |
| O quê | Quando a entrega declarar um critério de aceite executável, a seção de declaração deve conter a **saída real** do comando que o exercita, e não apenas a frase de conclusão. Alternativamente, o critério é codificado como teste versionado. |
| Responsável/papel | Crewmate executor produz a evidência; o gate do firstmate a exige antes de encaminhar ao merge |
| Evidência de eficácia | Uma entrega sem saída de execução anexada é devolvida pelo gate; e a reexecução independente da saída anexada reproduz o valor declarado |

A medida está vinculada ao modo de falha observado (aceite declarado sem execução do critério) e limitada a entregas que declarem critério executável. Não se propõe regra universal adicional: o incidente é isolado e uma exigência mais ampla não teria respaldo nas evidências desta revisão.
