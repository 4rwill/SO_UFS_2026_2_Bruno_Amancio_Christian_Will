# Roteiro da apresentação

Duração-alvo: 11:00. Base: 11 slides de `atividade3/output/slides/apresentacao_atividade3.pptx`.

Falas sugeridas para ensaio; não comprovam contribuição técnica efetiva. Nos slides 7 e 10 há troca de locutor sem troca de slide.

## Slide 01 - Virtualização, namespaces e cgroups

Janela: 00:00-00:40.

**Em tela:** Manter a capa e olhar para a turma. Apresentar o objetivo antes dos detalhes técnicos.

**Próxima ação:** Trocar para o slide 2 quando Bruno anunciar Iasmin.

### Bruno Amancio Ferreira

Olá, nós somos a equipe GenResearch, e eu sou Bruno. Nesta atividade de Sistemas Operacionais, investigamos como contêineres Linux isolam a visão dos processos e limitam recursos usando o mesmo kernel. Criamos um laboratório próprio, com dois contêineres e seis medições de uma carga de CPU. Vamos apresentar o ambiente, as evidências de isolamento, os resultados e suas limitações. Iasmin começa mostrando onde esses contêineres executam.

## Slide 02 - Ambiente e kernel compartilhado

Janela: 00:40-01:40.

**Em tela:** Apontar o diagrama de cima para baixo: Windows, WSL2, kernel, daemon e contêineres.

**Próxima ação:** Trocar para o slide 3 após a passagem para Pedro.

### Iasmin Victoria Teixeira Barreto

Eu sou Iasmin. O host físico utiliza Windows 10. Acima dele, a infraestrutura WSL2 fornece o ambiente Linux em que executa o Docker Desktop. É o kernel desse ambiente Linux que os contêineres compartilham. Cada imagem fornece seu espaço de usuário, com Python e bibliotecas Debian.

O daemon anunciou doze CPUs lógicas e aproximadamente 3,72 gibibytes de RAM. Esses valores descrevem a camada Linux intermediária. O Ubuntu usado na análise também precisa ser distinguido do ambiente efetivo do daemon. Neste desenho existe uma camada de virtualização, mas cada contêiner continua sendo um conjunto de processos sob o kernel compartilhado. Pedro vai mostrar como esses processos podem ter visões diferentes.

## Slide 03 - Evidências de namespaces

Janela: 01:40-02:50.

**Em tela:** Apontar primeiro os PIDs 567 e 612, depois os dois PIDs internos iguais a 1 e as três linhas de handles.

**Próxima ação:** Trocar para o slide 4 na passagem para Christian.

### Pedro César Figueiredo Carneiro

Eu sou Pedro. Coletamos os dados enquanto dois contêineres independentes estavam ativos. O Docker informou os PIDs 567 e 612 no host do daemon. Dentro de cada contêiner, o processo inicial tinha PID um. Isso acontece porque a numeração é relativa ao PID namespace de cada contêiner.

Na tabela, os identificadores de PID, mount e network são diferentes entre A e B. Esses handles sustentam que os contêineres pertenciam a namespaces distintos. O namespace de PID organiza a visão dos processos; o de mount, a visão das montagens; e o de network, os recursos de rede.

A diferença dos identificadores não comprova isolamento absoluto. A rede estava desativada, e não fizemos um teste de tráfego. Christian vai explicar o trabalho usado para comparar as quotas de CPU.

## Slide 04 - Carga determinística e protocolo

Janela: 02:50-04:00.

**Em tela:** Apontar vinte milhões, o checksum e a ordem C1/C2. A fórmula do slide é uma operação de acumulação, não inferência de IA.

**Próxima ação:** Trocar para o slide 5 na passagem para Marcos.

### Christian Will Silva Santos Nunes

Eu sou Christian. Para comparar as quotas, usamos uma carga de CPU com uma única thread e vinte milhões de iterações. O laço acumula uma expressão aritmética e limita o resultado a trinta e dois bits. Uma fórmula fechada calcula o checksum esperado de forma independente, e as seis execuções chegaram ao mesmo resultado indicado no slide.

Primeiro fizemos um piloto separado, com um milhão de iterações. Depois congelamos o trabalho principal e mantivemos a mesma quantidade nas seis medições. Cada execução usou um contêiner novo, alternando C1 e C2 três vezes.

Assim, a comparação mantém o trabalho e a imagem, variando a quota de CPU. O piloto não entra nas estatísticas. A carga não utiliza LLM, GPU ou espera simulada. Marcos vai mostrar os limites que realmente observamos no kernel.

## Slide 05 - Limites efetivos do cgroup

Janela: 04:00-05:00.

**Em tela:** Apontar cpu.max em C1 e C2, depois memória, swap e tarefas. Ler os valores como microssegundos por período.

**Próxima ação:** Trocar para o slide 6 na passagem para Sibele.

### Marcos Vinícius Dantas Aguiar

Eu sou Marcos. C1 recebeu quota de meia CPU, e C2, quota de uma CPU. Confirmamos esses limites lendo os arquivos do cgroup antes e depois do trabalho, além de registrar a configuração do Docker.

Em C1, cpu ponto max mostrou cinquenta mil por cem mil microssegundos. Isso significa até cinquenta milissegundos de tempo agregado de CPU por período de cem milissegundos. A quota não reserva um núcleo nem define afinidade.

As duas condições mantiveram duzentos e cinquenta e seis mebibytes de memória, swap adicional zero e limite de sessenta e quatro tarefas, incluindo threads. Também conferimos os arquivos de memória e tarefas. Não provocamos esgotamento de recursos. Sibele apresenta agora os tempos medidos.

## Slide 06 - Seis medições de tempo decorrido

Janela: 05:00-06:20.

**Em tela:** Apontar azul para C1, verde para C2, os três pares e as medianas abaixo do gráfico.

**Próxima ação:** Trocar para o slide 7; Marcos começa e Sibele continua sem trocar novamente.

### Sibele Oliveira Cruz

Eu sou Sibele. Cada par de barras representa uma repetição, com azul para meia CPU e verde para uma CPU. As seis execuções fizeram o mesmo trabalho e passaram na verificação de correção. Medimos o tempo do laço, excluindo a criação do contêiner e a inicialização do Python.

A mediana foi aproximadamente sete vírgula zero sete quatro segundos em C1 e três vírgula três oito quatro segundos em C2. A razão entre essas medianas foi dois vírgula zero nove. Isso mostra uma redução observada do tempo quando aumentamos a quota neste ambiente.

Também precisamos olhar a variação. C1 apresentou tempos de cerca de seis vírgula trinta e nove a oito vírgula vinte e um segundos; C2 ficou entre três vírgula vinte e sete e três vírgula cinquenta. Temos apenas três repetições por condição, então esse resultado não demonstra um ganho universal de duas vezes. Marcos vai relacionar esses tempos aos contadores de throttling.

## Slide 07 - Throttling e escopos de memória

Janela: 06:20-07:20.

**Em tela:** Marcos aponta a tabela superior; Sibele assume ao final da passagem e aponta as três definições abaixo. Manter o slide.

**Próxima ação:** Trocar para o slide 8 após Sibele anunciar Silas.

### Marcos Vinícius Dantas Aguiar

Em C1, o contador de períodos com throttling aumentou nas três execuções: setenta e um, oitenta e dois e sessenta e quatro. Também houve aumento do tempo de throttling. Em C2, esses deltas foram zero na janela observada. Junto com cpu ponto max e com os tempos, isso sustenta que a quota restringiu a carga em C1. Sibele explica agora os escopos da memória.

### Sibele Oliveira Cruz

RSS máximo descreve páginas residentes do processo. Memory current mostra o uso contabilizado no grupo em instantes de coleta. Memory peak registra o pico desde a criação do cgroup, incluindo a inicialização. Essas medidas têm escopos diferentes e não são todas uma média de RAM. O limite foi confirmado sem provocar OOM. Silas vai apresentar a restrição de escrita.

## Slide 08 - Mount read-only e menor privilégio

Janela: 07:20-08:30.

**Em tela:** Apontar leitura permitida, criação negada, EROFS e os controles de privilégio. Não tentar escrever em outro diretório do host.

**Próxima ação:** Trocar para o slide 9 quando Silas passar a palavra a Christian.

### Silas Santos da Silva

Eu sou Silas. Criamos um documento sintético e montamos seu diretório em barra dados com a opção somente leitura. O contêiner conseguiu ler o documento, mas a tentativa controlada de criar um arquivo nesse mesmo diretório foi negada. O erro foi trinta, EROFS, que indica sistema de arquivos somente leitura.

Também observamos a opção ro no ponto de montagem. A execução usou usuário não root, capabilities efetivas zeradas e a restrição de novos privilégios ativada. Cada mecanismo tem um papel: o mount namespace define a visão das montagens, a opção ro restringe escrita e a identidade limita ações permitidas.

Essa negação comprova a restrição daquele mount, sem demonstrar segurança absoluta. O teste ficou limitado ao diretório sintético. Christian vai mostrar como auditamos as evidências preservadas.

## Slide 09 - Evidência selecionada

Janela: 08:30-09:30.

**Em tela:** 0-10 s: explicar no slide. 10-30 s: terminal preparado, executar o auditor e apontar o resultado. 30-50 s: mostrar C1-1.json já aberto. 50-60 s: voltar e passar a palavra. Comandos na página de operação.

**Próxima ação:** Retornar aos slides e avançar para o 10; Iasmin assume.

### Christian Will Silva Santos Nunes

Vou mostrar uma evidência verificável. Este comando audita o lote já coletado; ele não repete os experimentos. O resultado informa seis execuções principais válidas e sessenta e oito arquivos conferidos.

No registro C1 um, podemos localizar cpu ponto max com a quota de meia CPU e os deltas dos contadores. O auditor também recalcula o checksum e confere limites, ordem das execuções e limpeza. Assim, a interpretação pode ser confrontada com os arquivos, além dos slides. Iasmin e Silas encerram discutindo os limites do estudo.

## Slide 10 - Limitações e relação com inferência

Janela: 09:30-10:30.

**Em tela:** Iasmin apresenta as três primeiras linhas; Silas continua com a relação com servidores e o risco compartilhado. Manter o slide entre os locutores.

**Próxima ação:** Trocar para o slide 11 após Silas passar a palavra a Bruno.

### Iasmin Victoria Teixeira Barreto

Nossa principal ameaça à validade é o host compartilhado. Fizemos três repetições por condição, sem isolar carga externa, frequência ou temperatura. Além disso, a visão de proc acessível via WSL não permitiu localizar os ancestrais reais dos contêineres. Por isso, os limites externos permanecem não confirmados. As leituras dos limites locais continuam registradas, mas a generalização precisa respeitar essas condições.

### Silas Santos da Silva

Em um servidor de inferência, quotas podem reduzir o impacto de uma carga sobre as demais, e um corpus somente leitura reduz alterações indevidas nos documentos. Ainda permanecem riscos ligados ao host, ao kernel e ao runtime compartilhados. Nosso teste usou aritmética Python, então não mede desempenho de LLM ou GPU. Bruno encerra retomando os resultados e a participação da equipe.

## Slide 11 - Equipe e revisão final

Janela: 10:30-11:00.

**Em tela:** Manter a tabela da equipe. Antes da apresentação final, atualizar a proposta de participação e as pendências do rodapé com informações confirmadas.

**Próxima ação:** Encerrar a exposição. Abrir o período separado de 3-5 minutos para perguntas.

### Bruno Amancio Ferreira

Para concluir, observamos namespaces distintos, limites efetivos de cgroup e uma restrição real de escrita. Com o mesmo trabalho, a quota maior apresentou menor tempo mediano nesta execução. O repositório reúne código, dados e documentação para conferência. Registramos a assistência do Codex, e a revisão e a responsabilidade acadêmica pertencem à equipe. Obrigado. Estamos disponíveis para as perguntas.

## Apoio à demonstração

O auditor verifica o lote existente; não repete os experimentos.

```bash
python atividade3/scripts/audit.py atividade3/results/raw/20261108T013949Z-19921f7f
```

Preparar C1-1.json e mount-readonly.json no editor. Instruções detalhadas, perguntas ou checklist de gravação estão no PDF.

PDF: [../output/pdf/roteiro_apresentacao.pdf](../output/pdf/roteiro_apresentacao.pdf).
