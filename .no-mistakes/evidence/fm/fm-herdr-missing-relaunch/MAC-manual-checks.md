# MAC validação do controle e da recuperação de terminais

Herdr 0.9.4 e Pi 1.2.0 reais. Sem substituto de agente nos cenários manuais.

## Observações verificadas

- Terminal original removido pelo Herdr real
- Regressão reproduzida antes da correção
- Exit ausente idempotente e sem perda de dados
- Endpoint ausente reconstruído na sessão gravada e Pi real em execução
- Pi real recebeu o pedido mas não dispõe de credencial no perfil isolado
- Segundo lançamento recusado enquanto Pi real está ativo
- Exit para Pi real encerrou o agente e preservou seu terminal
- Verificador ajustado à mensagem pública real; a primeira recusa foi válida
- Rótulo duplicado recusou recuperação sem criar endpoint órfão
- Recuperação disponível após remover somente o conflito criado pelo teste
- Viewer Herdr real anexado em PTY de 40 linhas e 120 colunas, com master drenado pelo helper
- Sessão Herdr parada foi reconstruída pelo próprio relaunch na sessão registrada
- Endpoint tmux ausente recusado antes de gravar nota ou diário

## Limites

- O perfil isolado do Pi exibiu `No API key found`; o modelo não comprovou processamento da nota ou continuidade do trabalho.
- O cenário com journal de apresentação parou na aquisição do lock: o laboratório usa caminho relativo de socket para respeitar o limite Unix e a fronteira do diretório; essa proteção exige caminho absoluto. Não foi considerado falha de produto.
- As imagens são screenshots do HTML que renderiza a captura ANSI real; não são capturas da janela nativa do Herdr.

## Preparação e verificadores corrigidos

- A primeira execução hermética de relaunch com TMPDIR interno ativou o guard que recusa home de secondmate dentro do Firstmate. Repetir com TMPDIR=/tmp passou.
- Uma asserção manual esperava a palavra ambiguous; o produto relatou explicitamente dois workspaces com rótulo firstmate. A asserção foi ajustada à resposta real e o cenário foi reexecutado, sem mudança de código.

## Evidências

- live-product-transcript.json: comandos, respostas públicas, processos e hashes.
- persisted-task-state.json: estado gerado pelo produto antes da limpeza.
- pi-recovered.html / pi-recovered.png: captura ANSI real com o bloqueio de autenticação visível.
- live-present-relaunch.log: relançamento preservando o terminal existente.
