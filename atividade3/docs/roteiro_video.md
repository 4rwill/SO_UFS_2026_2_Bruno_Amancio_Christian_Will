# Roteiro do vídeo

Duração-alvo: 15:00. Base: 11 slides de `atividade3/output/slides/apresentacao_atividade3.pdf`.

Falas sugeridas para ensaio; não comprovam contribuição técnica efetiva. Nos slides 7 e 10 há troca de locutor sem troca de slide.

## Slide 01 - Virtualização, namespaces e cgroups

Janela: 00:00-00:50.

**Em tela:** Abrir com Bruno visível e a capa compartilhada. Inserir seu nome completo na identificação da gravação.

**Próxima ação:** Cortar para Iasmin e exibir o slide 2.

### Bruno Amancio Ferreira

Olá, eu sou Bruno, da equipe GenResearch. Este vídeo apresenta nosso laboratório da Atividade 3 de Sistemas Operacionais. A pergunta é como namespaces mudam a visão de processos, montagens e rede, e como cgroups limitam recursos dentro de um kernel compartilhado.

Reaproveitamos a experiência da atividade anterior com Linux e medições, mas desenvolvemos os scripts deste laboratório sem o kit de apoio. Vamos acompanhar os onze slides, explicar as seis execuções e mostrar uma auditoria dos dados reais. Cada integrante vai explicar uma parte do laboratório. Iasmin vai apresentar as camadas do ambiente utilizado.

## Slide 02 - Ambiente e kernel compartilhado

Janela: 00:50-02:10.

**Em tela:** Exibir Iasmin identificada e o diagrama. Usar o cursor para destacar cada camada. Não apresentar o Ubuntu como host do daemon.

**Próxima ação:** Passar para Pedro e para o slide 3.

### Iasmin Victoria Teixeira Barreto

Eu sou Iasmin e vou explicar o ambiente experimental. Na parte superior do diagrama está o computador físico com Windows 10. A infraestrutura WSL2 oferece uma camada Linux intermediária. Nessa infraestrutura executa o Docker Desktop, que cria os contêineres A e B.

Os dois contêineres compartilham o kernel Linux. A imagem usada fornece Python e o espaço de usuário Debian; ela não inicia um kernel independente. Essa distinção ajuda a separar contêiner de máquina virtual: uma VM envolve um kernel convidado, enquanto aqui os processos dos contêineres usam o kernel Linux compartilhado.

Registramos doze CPUs lógicas e cerca de 3,72 gibibytes de RAM anunciados pelo daemon, além do Docker Engine e do cgroup versão dois. Também fixamos a imagem por digest para manter a mesma referência nas execuções. O Ubuntu do WSL foi usado para analisar os dados, e não deve ser confundido com o ambiente efetivo do daemon. Pedro apresenta agora as evidências de namespaces.

## Slide 03 - Evidências de namespaces

Janela: 02:10-03:35.

**Em tela:** Manter a tabela legível em tela inteira. Destacar os valores com o cursor, sem ler todos os dígitos dos handles.

**Próxima ação:** Passar para Christian no slide 4.

### Pedro César Figueiredo Carneiro

Eu sou Pedro e vou interpretar os namespaces. Os dados desta tabela foram coletados com os dois contêineres ativos e usando a mesma imagem. O Docker informou os processos 567 e 612 no host do daemon. Mesmo assim, cada contêiner mostrou seu processo inicial com PID um.

Não se trata do mesmo processo. Cada PID namespace apresenta sua própria numeração. O identificador interno precisa ser interpretado junto com a visão em que ele aparece. Também comparamos os handles de PID, mount e network. Em cada uma dessas três linhas, A e B têm identificadores distintos.

O PID namespace está ligado à visão dos processos. O mount namespace organiza a visão das montagens, e o network namespace organiza recursos de rede. O que observamos foi a separação desses namespaces nesta execução; os números podem mudar em outra execução.

Esses resultados não demonstram uma barreira de segurança absoluta. Usamos rede desativada e não testamos comunicação. Além disso, o PID informado por inspect pertence ao host do daemon, e não deve ser procurado em qualquer visão de proc sem confirmar sua correspondência. Agora Christian apresenta a carga determinística.

## Slide 04 - Carga determinística e protocolo

Janela: 03:35-05:00.

**Em tela:** Exibir Christian identificado. Apontar a expressão e depois a sequência. O código workload.py pode ser aberto apenas se já estiver preparado.

**Próxima ação:** Passar para Marcos no slide 5.

### Christian Will Silva Santos Nunes

Eu sou Christian e vou explicar o desenho da carga. Na atividade anterior havia uma espera simulada para representar geração. Para observar quota de CPU, usamos aqui um cálculo aritmético de uma thread, com memória constante e trabalho conhecido.

O laço executa vinte milhões de iterações. Em cada uma, acumula a expressão mostrada no slide e mantém o resultado em trinta e dois bits. A correção não depende apenas de repetir o laço: uma fórmula fechada, baseada nas somas dos inteiros e dos quadrados, calcula o valor esperado. As seis execuções concordaram com esse checksum.

Antes das medições principais, fizemos um piloto de um milhão de iterações e escolhemos uma quantidade segura. Depois disso, o trabalho permaneceu congelado. A ordem foi C1, C2, repetida três vezes, sempre com contêiner novo e a mesma imagem por digest.

O tempo do piloto fica separado das estatísticas. Também limitamos a duração com watchdogs de sessenta segundos dentro da carga e noventa segundos no comando externo. Marcos vai mostrar como confirmamos os limites de recursos.

## Slide 05 - Limites efetivos do cgroup

Janela: 05:00-06:20.

**Em tela:** Exibir Marcos identificado. Usar a tabela como guia e destacar que as linhas são leituras efetivas do kernel.

**Próxima ação:** Passar para Sibele no slide 6.

### Marcos Vinícius Dantas Aguiar

Eu sou Marcos e vou explicar os cgroups. Namespaces organizam visões de recursos. Já os cgroups permitem organizar processos e controlar o consumo de recursos. Neste laboratório, usamos cgroup versão dois.

C1 recebeu quota de meia CPU e C2, de uma CPU. O arquivo cpu ponto max contém a quota e o período em microssegundos. Em C1, os valores cinquenta mil e cem mil representam cinquenta milissegundos de CPU em cada período de cem milissegundos. Esse é um teto de tempo agregado, sem reservar fisicamente meio núcleo ou fixar o processo em um núcleo.

Apenas solicitar flags ao Docker não seria evidência suficiente. Por isso, lemos os limites antes e depois do trabalho. Mantivemos a mesma memória de duzentos e cinquenta e seis mebibytes e confirmamos swap adicional zero e sessenta e quatro tarefas, incluindo threads.

Não foi necessário provocar falta de memória ou criar tarefas em excesso. A comprovação aqui é dos limites configurados e observados. Agora Sibele apresenta as seis medições.

## Slide 06 - Seis medições de tempo decorrido

Janela: 06:20-07:50.

**Em tela:** Exibir Sibele identificada e ampliar o gráfico. Deixar os três pares visíveis. Os rótulos estão arredondados a duas casas; as medianas abaixo têm três.

**Próxima ação:** Passar para Marcos no slide 7 e manter o mesmo slide durante a fala seguinte de Sibele.

### Sibele Oliveira Cruz

Eu sou Sibele e vou interpretar os resultados. O gráfico mostra as seis observações, com três pares de barras. Azul corresponde a C1, com meia CPU, e verde a C2, com uma CPU. Todas as execuções concluíram vinte milhões de iterações com o mesmo checksum.

O eixo vertical mostra o tempo decorrido em segundos. Esse tempo cobre o laço de trabalho e exclui a criação do contêiner, a inicialização do Python e a coleta posterior. Assim, ele tem um escopo definido e não representa toda a duração do comando Docker.

A mediana de C1 foi cerca de sete vírgula zero sete quatro segundos. Em C2, foi três vírgula três oito quatro. A razão entre as medianas foi aproximadamente dois vírgula zero nove. Na tabela consolidada também registramos trabalho por segundo, que significa iterações por segundo e não tokens de um modelo.

C1 variou mais que C2. Como temos apenas três repetições e o host é compartilhado, o resultado deve ser interpretado dentro dessas condições. Não isolamos frequência, temperatura ou carga externa. Os contadores que Marcos apresenta a seguir ajudam a sustentar a interpretação da quota.

## Slide 07 - Throttling e escopos de memória

Janela: 07:50-09:00.

**Em tela:** Marcos aparece no início; fazer uma troca clara de locutor para Sibele, com identificação na tela. Nenhuma troca de slide entre as falas.

**Próxima ação:** Passar para Silas e para o slide 8.

### Marcos Vinícius Dantas Aguiar

Para verificar throttling, usamos diferenças entre os contadores lidos antes e depois da carga. Nas três execuções de C1, houve aumento do número de períodos com throttling e do tempo associado à restrição. Em C2, esses deltas foram zero nessa janela. Não estamos afirmando ausência de toda restrição externa: estamos descrevendo esses contadores locais. A combinação entre limites, tempos e deltas torna a interpretação mais sustentada. Sibele continua com a memória.

### Sibele Oliveira Cruz

Na memória, distinguimos três escopos. RSS máximo vem do processo e descreve suas páginas residentes. Memory current é a contabilização do grupo nos instantes observados. Memory peak cobre a vida do cgroup, inclusive a inicialização. Por isso, os valores podem diferir e não devem ser chamados de RAM média. Também não representam uma quota de memória de GPU. Não provocamos OOM nem esgotamento de tarefas. Silas mostra agora o teste de montagem somente leitura.

## Slide 08 - Mount read-only e menor privilégio

Janela: 09:00-10:25.

**Em tela:** Exibir Silas identificado. Apontar o erro e, se necessário, mostrar o arquivo mount-readonly.json já aberto. A demonstração é a evidência da execução registrada.

**Próxima ação:** Passar para Christian no slide 9 e preparar a captura do terminal.

### Silas Santos da Silva

Eu sou Silas e vou apresentar o teste de montagem somente leitura. Criamos um arquivo de texto sintético e montamos apenas seu diretório em barra dados. A leitura funcionou. Quando tentamos criar um novo arquivo nesse mesmo ponto de montagem, o sistema negou a operação com errno trinta, EROFS, ou sistema de arquivos somente leitura.

Registramos o erro e a opção ro no mount observado. Essa combinação relaciona a negação ao caráter somente leitura da montagem. Também executamos o teste com UID sessenta e cinco mil quinhentos e trinta e quatro, sem root, com capabilities efetivas zeradas e NoNewPrivs igual a um.

É importante separar os papéis. O mount namespace organiza a visão das montagens; a opção ro restringe escrita; identidade, permissões e políticas de privilégio regulam o acesso. O conjunto reduz as ações disponíveis, mas não elimina riscos do kernel e do runtime compartilhados.

Não montamos diretórios sigilosos, a raiz do host ou o Docker socket. O teste negativo ficou dentro do diretório sintético autorizado. Christian vai mostrar a verificação dos registros guardados.

## Slide 09 - Evidência selecionada

Janela: 10:25-12:55.

**Em tela:** Seguir a página de operação: 0-20 s no slide; 20-55 s executar auditor e explicar a saída; 55-95 s mostrar C1-1.json; 95-125 s mostrar mount-readonly.json; 125-150 s retornar ao slide e concluir. Reservar trechos silenciosos para leitura dos campos.

**Próxima ação:** Retornar aos slides, avançar para o 10 e passar a palavra a Iasmin.

### Christian Will Silva Santos Nunes

Nesta demonstração, vamos conferir o lote que produziu os resultados. O comando do slide executa uma auditoria dos arquivos existentes. Não estamos criando uma nova medição nem repetindo agora as seis cargas.

A saída indica um resultado válido, seis execuções principais e sessenta e oito arquivos verificados. Isso significa que a auditoria conferiu a integridade interna, a correção do trabalho, os limites observados e outros critérios do lote.

Vou abrir o registro C1 um. Aqui aparecem a condição, a quantidade fixa de trabalho, o checksum e os snapshots do cgroup. Em cpu ponto max, vemos cinquenta mil por cem mil. Nos deltas de CPU, podemos identificar o aumento dos contadores de throttling.

Agora mostramos o registro do mount somente leitura. Ele preserva a leitura bem-sucedida, o erro trinta na tentativa de escrita e os controles de privilégio. Esses arquivos permitem confrontar os números apresentados com as evidências da execução.

A auditoria é uma verificação de consistência e integridade dos registros; ela não representa uma assinatura independente de sua origem. Os dados completos e os scripts permanecem no repositório. Vamos voltar aos slides para discutir as limitações com Iasmin e Silas.

## Slide 10 - Limitações e relação com inferência

Janela: 12:55-14:15.

**Em tela:** Identificar a troca de Iasmin para Silas sem mudar o slide. Não apresentar hipóteses de frequência ou temperatura como causas medidas.

**Próxima ação:** Passar para Bruno e exibir o slide 11.

### Iasmin Victoria Teixeira Barreto

A principal limitação é que o host era compartilhado. Temos três repetições por condição e uma ordem alternada fixa, mas não controlamos continuamente carga externa, frequência ou temperatura. Esses fatores podem influenciar a variação e não foram isolados. Também houve uma limitação de visibilidade: o PID informado pelo Docker não apareceu no proc acessível via WSL. Assim, não confirmamos os limites ancestrais externos. Não substituímos essa ausência por uma afirmação de que eles estavam ilimitados.

### Silas Santos da Silva

A relação com inferência é conceitual. Limitar CPU, memória e tarefas ajuda a reduzir o impacto de uma carga em infraestrutura compartilhada. Um corpus somente leitura reduz alterações acidentais ou indevidas nos dados. Mesmo assim, kernel, runtime e host continuam sendo recursos e pontos de risco comuns. Nossa carga é aritmética Python: não carregamos um modelo de linguagem nem avaliamos GPU ou VRAM. Os resultados mostram os mecanismos observados neste laboratório, sem quantificar um serviço real de inferência. Bruno fará o encerramento.

## Slide 11 - Equipe e revisão final

Janela: 14:15-15:00.

**Em tela:** Bruno fecha o vídeo. O slide 11 contém uma distribuição simulada de contribuições e pendências: conferir as atribuições com o trabalho efetivo antes da gravação final. Conferir se todos apareceram identificados em seus trechos.

**Próxima ação:** Encerrar a gravação. Conferir áudio, legibilidade e participação antes de publicar.

### Bruno Amancio Ferreira

Encerramos com três evidências centrais: namespaces distintos entre os contêineres, limites locais de cgroup confirmados e escrita negada no mount somente leitura. Na comparação de trabalho fixo, elevar a quota de meia para uma CPU reduziu o tempo mediano observado, dentro das limitações apresentadas.

Os scripts, os registros brutos, o gráfico e o relatório estão organizados no repositório. Também declaramos a assistência do Codex e a necessidade de revisão crítica pela equipe. A equipe permanece responsável por revisar os resultados e explicar os mecanismos utilizados. Obrigado por acompanhar nosso laboratório de Sistemas Operacionais.

## Apoio à demonstração

O auditor verifica o lote existente; não repete os experimentos.

```bash
python atividade3/scripts/audit.py atividade3/results/raw/20261108T013949Z-19921f7f
```

Preparar C1-1.json e mount-readonly.json no editor. Instruções detalhadas, perguntas ou checklist de gravação estão no PDF.

PDF: [../output/pdf/roteiro_video.pdf](../output/pdf/roteiro_video.pdf).
