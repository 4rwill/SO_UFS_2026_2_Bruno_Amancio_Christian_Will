/**
 * Requer o runtime Codex com @oai/artifact-tool e a skill Presentations.
 * Configure CODEX_RUNTIME_NODE_MODULES, CODEX_PRESENTATIONS_SKILL e
 * CODEX_RUNTIME_PYTHON. Execute com o Node.js do runtime, da raiz do repo.
 * O arquivo final não é sobrescrito pelo finalizador. Para uma revisão, use
 * --output caminho-novo.pptx. Previews e recibos ficam em atividade3/.build.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const runtime = process.env.CODEX_RUNTIME_NODE_MODULES;
const skill = process.env.CODEX_PRESENTATIONS_SKILL;
const python = process.env.CODEX_RUNTIME_PYTHON;
if (!runtime || !skill || !python) throw new Error('Configure os três caminhos de runtime descritos no cabeçalho.');
process.env.RUNTIME_NODE_MODULES ??= runtime;
const build = path.join(root, '.build', 'slides');
await fs.mkdir(build, {recursive:true});
// O link resolve imports internos dos utilitários no Windows sem instalar pacotes.
const {Presentation, PresentationFile} = await import(pathToFileURL(path.join(runtime, '@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const {finalizePresentation, applyPresentationChartFont} = await import(pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')).href);
const batch = '20261108T013949Z-19921f7f';
const analysis = JSON.parse(await fs.readFile(path.join(root, 'results', 'analysis', batch, 'analysis.json'), 'utf8'));
const raw = path.join(root, 'results', 'raw', batch);
const namespaces = JSON.parse(await fs.readFile(path.join(raw, 'namespaces.json'), 'utf8'));
const C = {ink:'#14364D', blue:'#2463A6', green:'#20836E', muted:'#506473', pale:'#EAF0F5', line:'#CAD6E0', white:'#FFFFFF'};
const deck = Presentation.create({slideSize:{width:1280,height:720}});
const fonts = {typeface:'Arial'};
const sources = {
  ns:'https://man7.org/linux/man-pages/man7/namespaces.7.html',
  cg:'https://docs.kernel.org/admin-guide/cgroup-v2.html',
  docker:'https://docs.docker.com/engine/containers/resource_constraints/'
};
function text(slide, value, left, top, width, height, size=28, bold=false, color=C.ink) {
  const shape=slide.shapes.add({geometry:'textbox',position:{left,top,width,height},fill:'none',line:{fill:'none',width:0}});
  shape.text=value;
  shape.text.style={...fonts,fontSize:size,bold,color,wrap:'square',autoFit:'none',insets:0};
  return shape;
}
function base(title, notes) {
  const slide=deck.slides.add();
  slide.background.fill=C.white;
  text(slide,title,70,50,1140,70,44,true);
  text(slide,String(deck.slides.items.length).padStart(2,'0'),1160,675,50,25,18,false,C.muted);
  slide.speakerNotes.text=notes;
  return slide;
}
function table(slide, values, top, widths, height) {
  const t=slide.tables.add({rows:values.length,columns:values[0].length,left:70,top,width:1140,height,columnWidths:widths,values});
  t.borders.assign({fill:C.line,width:.6,style:'solid'});
  t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({
    textStyle:{fontSize:23,typeface:'Arial',color:C.ink},
    margins:{left:14,right:12,top:12,bottom:10},anchor:'center'});
  for(let r=0;r<values.length;r++){
    t.rows[r].height=height/values.length;
    for(let c=0;c<values[0].length;c++){
      const cell=t.getCell(r,c);
      cell.fill=r===0?C.pale:C.white;
      cell.text.style={...fonts,fontSize:23,bold:r===0,color:C.ink};
    }
  }
  return t;
}
function box(slide,label,x,y,w,h,fill=C.pale,size=26){
  const s=slide.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:C.line,width:1}});
  s.text=label;s.text.style={...fonts,fontSize:size,color:C.ink,alignment:'center',verticalAlignment:'middle',insets:12};
  return s;
}

let s=base('','Equipe GenResearch, UFS 2026.2. Tempo previsto: 40 segundos. Abrir com o objetivo de observar mecanismos do SO com evidências reais. Scripts próprios, sem kit do docente.');
text(s,'Virtualização,\nnamespaces e cgroups',70,135,1130,220,68,true);
text(s,'Sistemas Operacionais, Atividade 3',74,405,1100,55,32,false,C.blue);
text(s,'Equipe GenResearch\nUniversidade Federal de Sergipe, 2026.2',74,500,1100,100,27,false,C.muted);

s=base('Ambiente e kernel compartilhado',`Tempo previsto: 60 segundos. Diagrama editável das camadas observadas. Windows 10 Home Single Language 10.0.19045, Intel i5-11260H, 6 núcleos/12 CPUs lógicas, 8.358.518.784 bytes físicos. Daemon Docker Desktop 4.96.3/Engine 29.9.2, kernel WSL2 6.18.54.1-microsoft-standard-WSL2, cgroup v2/cgroupfs. O daemon anuncia 3.989.606.400 bytes. O Ubuntu foi usado na análise e não é a distribuição do daemon. Imagem Debian 13 com Python 3.12. Fontes: ${raw}/docker-environment.json; linux-environment.json; results/evidence/host-20261108T014504Z/environment.json. Conceitos: ${sources.ns}`);
box(s,'Hardware físico e host Windows 10',70,152,1140,90,C.pale,29);
const linuxBox=box(s,'Virtualização WSL2, ambiente Linux intermediário',100,260,1080,340,'#F7F9FB',29);
linuxBox.text.verticalAlignment='top';
// O diagrama é evidência conceitual solicitada no enunciado, com objetos editáveis.
text(s,'Kernel Linux compartilhado',155,335,970,44,32,true,C.blue);
text(s,'Docker Desktop, cgroup v2, 12 CPUs lógicas, 3,72 GiB',155,391,970,40,27,false,C.muted);
box(s,'Contêiner A\nPython e espaço de usuário Debian',150,466,465,100,C.white,26);
box(s,'Contêiner B\nPython e espaço de usuário Debian',665,466,465,100,C.white,26);
text(s,'O kernel pertence ao ambiente Linux intermediário.',74,625,1100,35,25,false,C.muted);

s=base('Evidências de namespaces',`Tempo previsto: 70 segundos. Ambos os contêineres estavam ativos. PID host A=567, B=612, mas PID interno de ambos=1. Handles distintos sustentam namespaces distintos, sem provar isolamento absoluto. --network none, sem teste de tráfego. Fonte bruta: ${raw}/namespaces.json. Referência: ${sources.ns}`);
const a=namespaces[0].observation.namespaces,b=namespaces[1].observation.namespaces;
table(s,[['Recurso','Contêiner A','Contêiner B'],['PID no host do daemon','567','612'],['PID interno','1','1'],['PID namespace',a.pid,b.pid],['Mount namespace',a.mnt,b.mnt],['Network namespace',a.net,b.net]],165,[350,395,395],365);
text(s,'Cada PID namespace possui sua própria numeração.',74,565,1110,45,29,true,C.blue);
text(s,'Handles distintos identificam namespaces distintos nesta execução.',74,620,1110,35,25,false,C.muted);

s=base('Carga determinística e protocolo',`Tempo previsto: 70 segundos. Uma thread, memória constante. Piloto separado de 1 milhão, wall 0,30954567 s em 0,5 CPU. Congelamos N=20 milhões antes das seis execuções. A fórmula soma(i²)+3*soma(i)+7*N módulo 2³² verifica a correção independentemente do laço. Checksum 2589261568 em todas. Watchdogs interno 60 s e externo 90 s. Fonte: ${raw}/manifest.json e runs/*.json.`);
text(s,'20.000.000 de iterações',74,160,1120,90,57,true,C.blue);
text(s,'checksum = (checksum + i*i + 3*i + 7) & 0xffffffff',74,280,1120,60,28);
text(s,'Fórmula independente confirma o resultado 2589261568.',74,365,1120,70,29);
text(s,'Piloto separado, N congelado, contêiner novo a cada execução.',74,460,1120,70,29);
text(s,'Ordem: C1/C2, C1/C2, C1/C2. Três repetições por condição.',74,555,1120,70,29);

s=base('Limites efetivos do cgroup',`Tempo previsto: 60 segundos. Os valores são leituras do kernel antes/depois, além das configurações de inspect. cpu.max contém quota e período em microssegundos. 50000/100000 = 0,5 CPU de tempo agregado. A quota não implica afinidade ou reserva. memory.max=268435456 e memory.swap.max=0, pids.max=64. Sem OOM ou esgotamento de tarefas. Fontes: seis registros runs/; ${sources.cg}; ${sources.docker}`);
table(s,[['Condição','cpu.max (µs)','Memória','Swap adicional','Tarefas'],['C1: 0,5 CPU','50000 100000','256 MiB','0','64'],['C2: 1 CPU','100000 100000','256 MiB','0','64']],180,[205,320,205,225,185],215);
text(s,'50 ms de CPU por período de 100 ms em C1.',74,445,1120,65,34,true,C.blue);
text(s,'cpu.max, memory.max, memory.swap.max e pids.max',74,535,1120,50,28);
text(s,'Leituras antes e depois de cada trabalho confirmam os limites locais.',74,600,1120,45,25,false,C.muted);

s=base('Seis medições de tempo decorrido',`Tempo previsto: 80 segundos. Gráfico nativo editável das seis execuções, n=3 por quota. Tempo em segundos do laço, exclui startup Docker/Python e coleta. C1 mediana 7,073924493, C2 mediana 3,384014666. Razão entre medianas 2,090394. Trabalho igual em todas. CSV completo e gráfico de mediana/mínimo-máximo em results/analysis/${batch}. Piloto excluído. Fonte: ${raw}/runs.`);
const chart=s.charts.add('bar',{
 position:{left:70,top:150,width:1140,height:410},
 categories:['Repetição 1','Repetição 2','Repetição 3'],
 series:[{name:'C1: 0,5 CPU',values:analysis.rows.filter(x=>x.condition==='C1').map(x=>Number(x.wall_s.toFixed(6))),fill:C.blue},
         {name:'C2: 1 CPU',values:analysis.rows.filter(x=>x.condition==='C2').map(x=>Number(x.wall_s.toFixed(6))),fill:C.green}],
 barOptions:{direction:'column',grouping:'clustered',gapWidth:140},
 hasLegend:true,legend:{position:'bottom',textStyle:{fontSize:23}},
 xAxis:{textStyle:{fontSize:23},majorGridlines:null},
 yAxis:{title:{text:'Tempo decorrido (s)',textStyle:{fontSize:23}},min:0,max:10,majorUnit:2,numberFormatCode:'0.0',textStyle:{fontSize:23},majorGridlines:{fill:C.line,width:1}},
 dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{fontSize:23}},
 chartFill:C.white,plotAreaFill:C.white});
applyPresentationChartFont(chart,{fontFamily:'Arial'});
s.speakerNotes.append(' Valores do gráfico arredondados a seis casas decimais para compatibilidade numérica do workbook Excel. Dados brutos e CSV preservam a precisão original.');
text(s,'Medianas: 7,074 s em C1 e 3,384 s em C2',74,580,1130,50,33,true,C.blue);
text(s,'Razão observada: 2,090 vezes. n = 3 por condição.',74,635,1130,35,25,false,C.muted);

s=base('Throttling e escopos de memória',`Tempo previsto: 60 segundos. Deltas positivos de nr_throttled e throttled_usec em C1 sustentam restrição no período de trabalho. C2 deltas zero nesta janela, sem garantir ausência de toda restrição externa. usage e tempos do processo têm sobrecargas distintas. RSS é máximo do processo, memory.current são dois snapshots do grupo e memory.peak cobre sua vida. Fonte: runs.csv e registros brutos. Referência: ${sources.cg}`);
table(s,[['Condição','Delta nr_throttled','Delta throttled (s)'],['C1: repetições 1/2/3','71 / 82 / 64','3,545 / 4,088 / 3,192'],['C2: repetições 1/2/3','0 / 0 / 0','0 / 0 / 0']],160,[365,355,420],215);
text(s,'RSS máximo: páginas residentes do processo.',74,420,1120,55,28);
text(s,'memory.current: snapshots do uso contabilizado no grupo.',74,495,1120,55,28);
text(s,'memory.peak: pico desde a criação do cgroup.',74,570,1120,55,28);

s=base('Mount read-only e menor privilégio',`Tempo previsto: 70 segundos. Diretório sintético montado em /dados com ro. Leitura funcionou, criação de /dados/tentativa-escrita.txt retornou errno 30 EROFS. O mountinfo registra ro, UID 65534, CapEff zero, NoNewPrivs=1 e Seccomp=2. Separar visão do mount, opção ro e identidade/políticas de acesso. Demonstra restrição pontual, não isolamento absoluto. Fonte: ${raw}/mount-readonly.json e namespaces.json.`);
text(s,'Leitura do documento: permitida',74,160,1120,65,38,true,C.green);
text(s,'Criação de arquivo em /dados: negada',74,255,1120,65,38,true,C.blue);
text(s,'errno 30, EROFS, Read-only file system',74,350,1120,60,31);
text(s,'UID 65534, CapEff zero, NoNewPrivs = 1',74,455,1120,60,31);
text(s,'A restrição da montagem soma-se aos controles de privilégio.',74,565,1120,70,28,false,C.muted);

s=base('Evidência selecionada',`Tempo previsto: 60 segundos. Demonstração ensaiada: executar auditor do lote publicado na raiz do repositório. Mostrar seis execuções válidas e 68 arquivos verificados. Abrir runs/C1-1.json para cpu.max/cpu_stat_delta e mount-readonly.json para EROFS. Não fazer download ou instalar dependências na apresentação. Seis testes passaram no Ubuntu, incluindo rejeição de dados alterados em fixtures. Logs em results/evidence/tests.txt.`);
text(s,'Auditoria do lote publicado',74,165,1120,60,36,true,C.blue);
text(s,'python atividade3/scripts/audit.py \\\n  atividade3/results/raw/20261108T013949Z-19921f7f',74,265,1120,115,29);
text(s,'6 execuções válidas, 68 arquivos conferidos',74,435,1120,60,34,true);
text(s,'Checksum independente, limites do kernel e limpeza confirmados.',74,540,1120,75,28,false,C.muted);

s=base('Limitações e relação com inferência',`Tempo previsto: 60 segundos. Ameaça principal: host compartilhado, sem controle contínuo de frequência/temperatura/carga externa. Só três repetições, alternância fixa. PID de inspect não visível no /proc acessível via WSL, ancestrais externos não confirmados. Limites de RAM/tarefas e corpus ro reduzem impacto de uma carga em servidor compartilhado, mas kernel/runtime permanecem comuns e precisam atualização/configuração. RAM não representa VRAM. Sem LLM/GPU nesta carga. Referências: ${sources.ns}; ${sources.cg}; ${sources.docker}`);
text(s,'Host compartilhado e três repetições',74,165,1120,55,34,true,C.blue);
text(s,'Ruído, frequência e temperatura não foram isolados.',74,235,1120,55,28);
text(s,'Ancestrais externos não confirmados pela visão disponível.',74,330,1120,70,28);
text(s,'Quotas e corpus read-only reduzem o impacto de uma carga.',74,435,1120,70,28);
text(s,'Kernel e runtime compartilhados mantêm riscos comuns.',74,545,1120,70,28,false,C.muted);

s=base('Equipe e revisão final',`Tempo previsto: 30 segundos. Os nomes vêm da equipe da Atividade 2. Os temas apresentados são propostas de revisão, ainda não contribuições efetivas confirmadas. A equipe deve substituir pela participação real antes da entrega. Codex auxiliou implementação, coleta, auditoria, análise e materiais. Modelo exato não exposto por fonte verificável nesta sessão. Prompts e decisões em docs/uso_ia.md. URL do vídeo, contribuições efetivas e commit final pendentes. Entrega em 10/11/2026, apresentação em 11/11/2026. Não há declaração de submissão concluída.`);
table(s,[['Integrante','Tema proposto para revisão'],['Bruno Amancio Ferreira','Objetivo e organização'],['Christian Will Silva Santos Nunes','Código e demonstração'],['Iasmin Victoria Teixeira Barreto','Ambiente e método'],['Marcos Vinícius Dantas Aguiar','Cgroups e throttling'],['Pedro César Figueiredo Carneiro','Namespaces e PIDs'],['Sibele Oliveira Cruz','Métricas e gráfico'],['Silas Santos da Silva','Read-only e limitações']],140,[620,520],415);
text(s,'Proposta de participação, a confirmar com a equipe.',74,575,1120,42,25,false,C.muted);
text(s,'Assistência: Codex. Vídeo e commit final permanecem pendentes.',74,627,1120,42,25,false,C.muted);

const requestedOutput=process.argv.indexOf('--output');
const finalPath=requestedOutput>=0?path.resolve(process.argv[requestedOutput+1]):path.join(root,'output','slides','apresentacao_atividade3.pptx');
await fs.mkdir(path.dirname(finalPath),{recursive:true});
const candidatePath=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidatePath);
for(const [i,slide] of deck.slides.items.entries()){
 const blob=await deck.export({slide,format:'png',scale:1});
 await fs.writeFile(path.join(build,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
}
const result=await finalizePresentation({workspaceDir:root,candidatePath,finalPath,
 pythonExecutable:python,
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',
             ...[3,5,7,11].flatMap(n=>['--require-native-table-slide',String(n)])],
 requiredNativeTableOwnerSlides:[3,5,7,11],requiredNativeChartOwnerSlides:[6],
 materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:['Arial']},
 verifyArtifactToolImport:true,receiptPath:path.join(build,`validation-${Date.now()}.json`)});
console.log(JSON.stringify({finalPath,receipt:result.receiptPath,sha256:result.finalSha256,slides:deck.slides.items.length},null,2));
