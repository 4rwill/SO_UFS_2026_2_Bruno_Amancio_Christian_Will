# Roteiro da apresentação

Duração-alvo: 11:00. Base: 14 slides de `atividade3/output/slides/apresentacao_atividade3.pdf`.

Um apresentador por slide. Cada integrante fala em um único bloco de dois slides, sem retorno na exposição.

## Slide 01 - Virtualização, namespaces e cgroups

Janela: 00:00-00:25.

**Em tela:** Exibir a capa com a equipe e o nome de Bruno. No vídeo, identificar Bruno na tela.

**Próxima ação:** Avançar ao slide 2; Bruno continua.

### Bruno Amancio Ferreira

Olá, eu sou Bruno, da equipe GenResearch. Vamos apresentar a Atividade 3 de Sistemas Operacionais: um laboratório próprio para observar namespaces, limites de cgroups e montagem somente leitura em contêineres Linux. O trabalho reúne seis medições reais e registros que permitem conferir os resultados.

## Slide 02 - Objetivo e percurso do laboratório

Janela: 00:25-01:25.

**Em tela:** Apontar a pergunta e as três evidências: namespaces, limites efetivos e escrita negada. Manter Bruno até concluir o slide.

**Próxima ação:** Avançar ao slide 3 e passar a palavra a Iasmin Victoria Teixeira Barreto.

### Bruno Amancio Ferreira

A pergunta é como namespaces alteram a visão dos processos e como cgroups limitam recursos sob um kernel compartilhado. Observamos três aspectos: os identificadores de PID, mount e network; os limites efetivos de CPU, memória, swap e tarefas; e o comportamento de uma montagem somente leitura.

A carga é um cálculo aritmético em Python, sem LLM ou GPU. Comparamos meia CPU e uma CPU, usando o mesmo trabalho e três repetições por condição. Os resultados incluem os arquivos brutos, a análise e um auditor de integridade. Primeiro veremos o ambiente e o protocolo, depois o isolamento, a carga, os limites e os resultados. Silas encerra com as restrições de acesso e as limitações. Iasmin assume agora para mostrar onde os contêineres executam.

## Slide 03 - Ambiente e kernel compartilhado

Janela: 01:25-02:20.

**Em tela:** Iasmin assume. Percorrer o diagrama: Windows, infraestrutura WSL2, ambiente do daemon e contêineres.

**Próxima ação:** Avançar ao slide 4; Iasmin continua.

### Iasmin Victoria Teixeira Barreto

Eu sou Iasmin. O host físico utiliza Windows 10. A infraestrutura WSL2 fornece o ambiente Linux em que executa o Docker Desktop. O kernel compartilhado pertence a esse ambiente Linux intermediário. As imagens dos contêineres fornecem Python e o espaço de usuário Debian, sem iniciar um kernel próprio.

O daemon anunciou doze CPUs lógicas e aproximadamente 3,72 gibibytes de RAM. Esses recursos descrevem a camada do daemon. O Ubuntu usado na análise também deve ser distinguido desse ambiente. O diagrama mostra a camada de virtualização existente no Windows e, dentro do ambiente Linux, os dois contêineres compartilhando o kernel.

## Slide 04 - Protocolo e controle das execuções

Janela: 02:20-03:00.

**Em tela:** Apontar a sequência C1/C2, a imagem fixa e a leitura dos limites antes/depois. Ao terminar, passar para Pedro.

**Próxima ação:** Avançar ao slide 5 e passar a palavra a Pedro César Figueiredo Carneiro.

### Iasmin Victoria Teixeira Barreto

O protocolo fixa a imagem por digest e usa contêineres novos. Um piloto separado ajuda a definir a duração; depois, o trabalho fica congelado em vinte milhões de iterações. A sequência principal é C1, C2, repetida três vezes.

Mantivemos constantes memória, swap, limite de tarefas, usuário e restrições de privilégio. A quota de CPU é a condição comparada. Os limites são lidos antes e depois do trabalho, e os contêineres criados pelo laboratório são removidos ao final. Pedro vai apresentar as evidências de isolamento da visão dos processos.

## Slide 05 - Namespaces: visões de processos, mounts e rede

Janela: 03:00-03:40.

**Em tela:** Pedro assume. Relacionar cada namespace à visão que ele organiza; separar identificação de namespace de teste de tráfego.

**Próxima ação:** Avançar ao slide 6; Pedro continua.

### Pedro César Figueiredo Carneiro

Eu sou Pedro. Os namespaces organizam visões de recursos do kernel. O PID namespace define a numeração de processos vista naquele contexto. O mount namespace organiza a visão das montagens, e o network namespace separa a visão de recursos de rede.

Coletamos os handles de dois contêineres ativos. Handles diferentes identificam namespaces diferentes nesta execução. Isso não demonstra isolamento absoluto nem mede tráfego de rede: a rede dos contêineres estava desativada. No próximo slide, veremos os identificadores e a relação entre o PID interno e o informado pelo daemon.

## Slide 06 - Evidências de namespaces e PIDs

Janela: 03:40-04:30.

**Em tela:** Apontar PIDs 567/612 no host do daemon, PID interno 1/1 e handles distintos. Ao terminar, passar para Christian.

**Próxima ação:** Avançar ao slide 7 e passar a palavra a Christian Will Silva Santos Nunes.

### Pedro César Figueiredo Carneiro

O Docker informou os PIDs 567 e 612 no host do daemon. Dentro de cada contêiner, o processo inicial tinha PID um. Não existe contradição: a numeração é relativa ao PID namespace.

As três linhas seguintes mostram handles distintos de PID, mount e network entre A e B. Isso sustenta a separação dessas visões na coleta. Os números são identificadores daquele momento, não valores fixos que outra reprodução precisa repetir.

Essa evidência descreve isolamento de visão. A capacidade de CPU e os demais limites serão tratados pelos cgroups. Christian vai mostrar como garantimos que as seis execuções fizeram o mesmo trabalho e como conferir os registros.

## Slide 07 - Carga determinística e checksum

Janela: 04:30-05:15.

**Em tela:** Christian assume. Apontar N fixo, expressão do checksum e oráculo independente. Não tratar a carga como inferência de LLM.

**Próxima ação:** Avançar ao slide 8; Christian continua.

### Christian Will Silva Santos Nunes

Eu sou Christian. A carga executa vinte milhões de iterações de um cálculo aritmético, em uma thread e com memória constante. Cada iteração acumula i ao quadrado, mais três i, mais sete, com resultado limitado a trinta e dois bits.

O checksum esperado também é calculado por uma fórmula fechada independente do laço. Nas seis execuções, o valor foi dois bilhões, quinhentos e oitenta e nove milhões, duzentos e sessenta e um mil, quinhentos e sessenta e oito. A quantidade de trabalho e o resultado correto são comuns às duas condições; a quota é a variável comparada.

## Slide 08 - Auditoria e demonstração dos registros

Janela: 05:15-06:15.

**Em tela:** Executar o auditor do lote existente. Ampliar o terminal e mostrar valid=true, main_runs=6, verified_files=68. Depois abrir runs/C1-1.json. Se houver falha atual, explicar e abrir os registros preservados.

**Próxima ação:** Avançar ao slide 9 e passar a palavra a Marcos Vinícius Dantas Aguiar.

### Christian Will Silva Santos Nunes

Vou mostrar uma verificação dos arquivos já coletados. Este comando não repete o experimento: confere a integridade e a consistência do lote preservado. O resultado esperado para o lote publicado é valid igual a true, seis execuções principais e sessenta e oito arquivos verificados.

O auditor verifica hashes, checksums, limites e limpeza. No registro C1-1, podemos localizar o número de iterações, o checksum e cpu.max. Os contadores antes e depois permitem calcular o throttling. Uma auditoria de integridade não é uma assinatura independente da origem dos dados. Marcos vai explicar o significado dos limites locais e desses contadores.

## Slide 09 - Limites efetivos do cgroup v2

Janela: 06:15-07:00.

**Em tela:** Marcos assume. Apontar cpu.max nas duas condições e os três limites mantidos constantes.

**Próxima ação:** Avançar ao slide 10; Marcos continua.

### Marcos Vinícius Dantas Aguiar

Eu sou Marcos. C1 tem quota de meia CPU e C2, de uma CPU. O arquivo cpu.max mostrou cinquenta mil por cem mil microssegundos em C1 e cem mil por cem mil em C2. Portanto, C1 dispõe de cinquenta milissegundos de tempo agregado de CPU por período de cem milissegundos.

Isso é quota, não afinidade ou reserva de um núcleo. Memória, swap adicional e tarefas ficaram fixos em 256 mebibytes, zero e sessenta e quatro. Essas condições foram confirmadas por leituras dos arquivos do kernel antes e depois do cálculo, além das opções usadas no Docker.

## Slide 10 - Throttling durante a carga

Janela: 07:00-07:45.

**Em tela:** Apontar os deltas das três repetições. Relacionar a quota com a restrição observada; passar para Sibele ao terminar.

**Próxima ação:** Avançar ao slide 11 e passar a palavra a Sibele Oliveira Cruz.

### Marcos Vinícius Dantas Aguiar

Para interpretar throttling, comparamos os contadores antes e depois da carga. Nas três execuções de C1, nr_throttled aumentou setenta e um, oitenta e dois e sessenta e quatro. O tempo associado à restrição também cresceu nas três.

Em C2, os deltas desses campos foram zero na janela observada. Isso não prova ausência de restrições em toda a hierarquia externa. Os contadores locais ajudam a explicar por que uma quota menor pode aumentar o tempo decorrido para o mesmo cálculo. Sibele vai mostrar os seis tempos e distinguir as métricas de memória.

## Slide 11 - Seis medições de tempo decorrido

Janela: 07:45-08:45.

**Em tela:** Sibele assume. Ler o gráfico por pares, apontar as medianas e n=3. Explicar a razão entre medianas.

**Próxima ação:** Avançar ao slide 12; Sibele continua.

### Sibele Oliveira Cruz

Eu sou Sibele. Cada par de barras representa uma repetição: azul para meia CPU e a segunda cor para uma CPU. As seis execuções concluíram o mesmo trabalho com o checksum correto. O tempo representado é o do cálculo, sem incluir a inicialização dos contêineres.

A mediana foi aproximadamente sete vírgula zero setenta e quatro segundos em C1 e três vírgula trezentos e oitenta e quatro em C2. A razão entre essas medianas foi dois vírgula zero noventa. As três observações de C1 foram maiores que as três de C2 nesta amostra.

São apenas três repetições por condição, em host compartilhado. Portanto, apresentamos os seis valores e a variação, sem concluir que qualquer carga terá exatamente esse ganho. Os deltas de throttling mostrados por Marcos ajudam a interpretar a diferença observada.

## Slide 12 - Memória: processo e cgroup

Janela: 08:45-09:25.

**Em tela:** Distinguir RSS máximo, memory.current e memory.peak. Ao terminar, passar para Silas, que segue até o encerramento.

**Próxima ação:** Avançar ao slide 13 e passar a palavra a Silas Santos da Silva.

### Sibele Oliveira Cruz

As métricas de memória têm escopos diferentes. O RSS máximo descreve páginas residentes do processo. memory.current mostra o uso contabilizado do grupo nos instantes coletados. memory.peak cobre o pico desde a criação do cgroup, inclusive a inicialização.

Esses valores não devem ser chamados de RAM média, nem confundidos com memória de GPU. O limite de 256 mebibytes foi confirmado, mas não provocamos esgotamento de memória. Silas assume agora para mostrar a restrição de escrita e encerrar com os limites das conclusões.

## Slide 13 - Mount read-only e menor privilégio

Janela: 09:25-10:15.

**Em tela:** Silas assume. Mostrar leitura permitida e escrita negada. No vídeo, abrir mount-readonly.json e apontar errno, UID e controles.

**Próxima ação:** Avançar ao slide 14; Silas continua.

### Silas Santos da Silva

Eu sou Silas. Criamos um documento sintético e montamos seu diretório como somente leitura. A leitura funcionou. Ao tentar criar um novo arquivo no mesmo diretório, a operação foi negada com errno trinta, EROFS: sistema de arquivos somente leitura.

O processo também executou com UID 65534, capabilities efetivas zeradas e NoNewPrivs igual a um. A restrição da montagem soma-se aos controles de menor privilégio. O teste comprova essa negação de escrita no mount observado. Ele não demonstra segurança absoluta, porque kernel, runtime e outros componentes permanecem compartilhados.

## Slide 14 - Limitações, aplicação e conclusão

Janela: 10:15-11:00.

**Em tela:** Silas permanece até o encerramento. Mostrar limitações, conclusão e links. Não retornar a apresentadores anteriores.

**Próxima ação:** Encerrar a exposição e abrir o período de perguntas.

### Silas Santos da Silva

A amostra tem três repetições por condição em um host compartilhado. Frequência, temperatura e carga externa não foram isoladas, e não confirmamos os limites ancestrais externos pela visão disponível.

Em um servidor de inferência, quotas, tetos de memória e tarefas, corpus somente leitura e menor privilégio podem reduzir o impacto de uma carga. Este experimento, porém, não executou LLM ou GPU.

Concluímos que houve namespaces distintos, limites locais confirmados, throttling em C1 e escrita negada. O repositório reúne dados e materiais, e o vídeo está no link indicado. Declaramos o apoio do Codex e a responsabilidade de revisão da equipe. Obrigado; estamos disponíveis para perguntas.

## Apoio à demonstração

O auditor verifica o lote existente; não repete os experimentos.

```bash
python atividade3/scripts/audit.py atividade3/results/raw/20261108T013949Z-19921f7f
```

Preparar C1-1.json e mount-readonly.json no editor. Instruções detalhadas, perguntas ou checklist de gravação estão no PDF.

PDF: [../output/pdf/roteiro_apresentacao.pdf](../output/pdf/roteiro_apresentacao.pdf).
