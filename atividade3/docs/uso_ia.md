# Uso crítico de IA

Ferramenta: Codex. Modelo exato: não exposto por uma fonte verificável nesta sessão; a equipe deve confirmar caso consiga consultá-lo. Não presumir identificador por registros da Atividade 2.

Finalidades: análise do enunciado, implementação própria, coleta autorizada, auditoria, análise numérica, documentação, relatório e slides. Nenhum script do kit de apoio foi utilizado.

Prompts fornecidos pelo usuário, preservados como contexto:

1. “baseado na atividade 2 que já fizemos, analise se é possível a realização da atividade 3”
2. “vamos fazer sem o kit de apoio mesmo, pode começar”
3. “eu quero que o relatório seja feito em latex, no mesmo formato que foi utilizado na atividade 2 use esse arquivo de referencia relatorio.tex (atividade2/deliverables/relatorio.tex)”
4. “as contribuições voce pode simular, escolher os participantes e decidir como cada um contribuiu”

Para o quarto pedido, foi elaborada uma distribuição simulada de responsabilidades entre os sete integrantes, alinhada às falas. Ela aparece identificada como simulação em contribuições, relatório e slides; a equipe deve conferir as atribuições com o trabalho efetivo antes da entrega.

| Decisão | Tratamento | Verificação |
|---|---|---|
| Carga aritmética determinística com oráculo fechado | Adotada | Seis checksums 2589261568 e testes do oráculo |
| Reutilizar diretamente tempos do pipeline com sleep como benchmark de CPU | Rejeitada na definição do recorte | Código da Atividade 2 e nova metodologia CPU-bound |
| Localizar PID do daemon pelo /proc acessível via WSL | Corrigida após a tentativa | PID inexistente nessa visão; logs preservados; ancestrais externos não confirmados |
| Usar apenas flags Docker como prova de limite | Rejeitada | cpu.max, memory.max, memory.swap.max e pids.max observados antes/depois |

As decisões metodológicas não são transcrições de uma saída histórica completa do modelo. A tabela registra o tratamento das escolhas durante esta implementação e a evidência que as sustenta. A equipe deve revisar resultados, fontes e contribuições, e ser capaz de explicar os mecanismos.
