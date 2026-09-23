# Critérios adaptáveis por domínio

Selecione somente verificações que afetem os requisitos ou riscos materiais da entrega. Estes critérios orientam a coleta de evidência; não criam automaticamente novos requisitos nem exigem todos os testes em toda revisão.

| Domínio | Verificações materiais | Evidência de resultado adequada |
| --- | --- | --- |
| Software e arquitetura | Contratos, invariantes, limites, concorrência, modos de falha, segurança, custo de manutenção e adequação à escala requerida. Diferencie arquitetura proposta de sistema implementado. | Código/decisão rastreável, teste pertinente e comportamento observado. Diagramas não comprovam comportamento em produção. |
| Integrações e APIs | Contrato vigente, autenticação versus autorização, paginação, rate limits, retries, idempotência, falhas parciais e consistência entre origem e destino. | Solicitação e resposta sanitizadas, identificador da operação e releitura do objeto no destino. Aceite assíncrono exige verificar o estado final. |
| ERP e CRM | Regras fiscais/comerciais aplicáveis, empresa correta, chaves de vínculo, duplicidade, estado transacional e preservação dos campos fora do escopo. | Comparação antes/depois e releitura dos registros exatos, incluindo vínculos; uma tela de sucesso isolada é insuficiente. |
| Financeiro | Entidade/conta, período, competência versus caixa, moeda, sinal, bruto versus líquido, taxas, arredondamentos, duplicidades e completude. Não inferir valores ausentes. | Fonte primária, memória de cálculo reproduzível e conciliação por registro e total. Um total coincidente não elimina duplicidades compensatórias. |
| Análise de dados | Proveniência, população/amostra, filtros, ausências, duplicidades, joins, denominadores, unidades, incerteza e inferência causal. | Cálculo reproduzível, amostra rastreável e comparação com fonte. Um gráfico plausível não valida a consulta nem a conclusão. |
| Automação de marketing | Público, consentimento/permissões aplicáveis, exclusões, gatilhos, deduplicação, atribuição e métricas ligadas ao objetivo. | Prévia do público e teste autorizado com rastreio do fluxo. Entrega de mensagem não comprova conversão nem causalidade. |
| Estratégia de negócio | Coerência entre objetivo e escolha, hipóteses de demanda/capacidade, alternativas, dependências, reversibilidade e critérios de decisão. | Dados e premissas identificados, cenários e resultados de experimentos quando existentes. Projeção continua sendo estimativa. |
| Processos e resultados de agentes | Cobertura do pedido, ferramentas usadas, limites de autoridade, transições, handoffs, observabilidade e encerramento com evidência. | Artefato final e estado verificável do processo; histórico de chamadas ou autodeclaração de conclusão não bastam. |

Para outros domínios, derive critérios do pedido e de fontes apropriadas. Registre limites de competência e evidência sem simular certificação especializada. Verifique afirmações voláteis em fonte atual quando necessárias à conclusão; referências antigas não demonstram estado operacional atual.
