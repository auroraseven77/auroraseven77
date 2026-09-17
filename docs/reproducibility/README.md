# Resultados reproduzíveis — TUU/Aurora

Este diretório define como resultados experimentais da TUU/Aurora devem ser publicados.

## Princípios

1. **Hipótese não é fato.** Toda alegação deve indicar se é hipótese, observação, resultado experimental ou conclusão.
2. **Resultado negativo é resultado.** Falha, resultado nulo ou inconclusivo deve permanecer no registro.
3. **Reprodução independente.** Um resultado não deve ser considerado validado apenas porque foi produzido pelo próprio sistema.
4. **Proveniência.** Cada resultado deve registrar código, versão/commit, dados, parâmetros, ambiente e timestamp.
5. **Métricas antes do experimento.** Critérios de sucesso e métricas devem ser definidos antes de olhar os resultados.
6. **Ablação.** Quando possível, comparar o sistema completo com variantes que removam componentes específicos.
7. **Auditoria.** Modelos de IA são fontes de análise/recomendação; não recebem autoridade epistemológica apenas por participar do experimento.

## Registro mínimo de um experimento

```yaml
experiment_id: TUU-YYYYMMDD-NNN
hypothesis: "..."
status: planned|running|completed|failed|inconclusive
repository_commit: "..."
code_path: "..."
data_sources: []
parameters: {}
metrics: []
baseline: "..."
ablations: []
results: {}
uncertainties: []
limitations: []
reproduction_command: "..."
independent_review: "pending|completed"
```

## Publicação

Cada resultado publicado deve conter:

- objetivo e hipótese;
- ambiente de execução;
- dependências e versões;
- commit exato do código;
- dados ou instruções para obtê-los legalmente;
- parâmetros completos;
- baseline;
- métricas e intervalos/variabilidade quando aplicável;
- resultados positivos, negativos e inconclusivos;
- limitações e possíveis fontes de viés;
- comando ou procedimento de reprodução;
- identificação de qualquer componente de IA utilizado;
- revisão independente quando disponível.

## Regra de interpretação

Um resultado reproduzido demonstra apenas o fenômeno medido sob as condições descritas. Não deve ser usado para transformar automaticamente uma hipótese arquitetural ou cognitiva da TUU/Aurora em fato científico.
