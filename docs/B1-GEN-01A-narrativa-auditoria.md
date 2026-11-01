# Aurora × TUU — B1-GEN-01A
## A história de uma hipótese que precisou prestar contas à evidência

**Status deste documento:** narrativa para revisão; não é um relatório de nova execução experimental.

Todo projeto científico começa com uma pergunta. O B1-GEN-01A investiga se um sistema consegue identificar funções booleanas desconhecidas por meio de consultas limitadas e, igualmente importante, se consegue reconhecer quando as evidências não sustentam uma identificação exata.

No Aurora × TUU, essa pergunta faz parte de um compromisso mais amplo: manter hipóteses, observações, interpretações e conclusões distinguíveis. Não basta produzir uma resposta convincente. É necessário registrar como ela foi obtida, quais controles foram aplicados e quais limites permanecem.

### Aprender sob orçamento limitado

O desenho descrito no histórico usa 70 tabelas-verdade booleanas distintas, cada uma definida em um domínio de 16 entradas, com orçamento máximo de oito consultas por ensaio. São comparadas três estratégias: `active`, `random` e `fixed`. O plano relatado totaliza 490 ensaios: 70 ativos, 350 aleatórios (cinco sementes por alvo) e 70 fixos.

Os resultados anteriormente relatados foram: identificação exata de 70/70 ensaios para `active`, 262/350 para `random` e 30/70 para `fixed`; os demais casos foram descritos como abstenções. **Esses números são reproduzidos aqui como resultados registrados na conversa anterior; não foram recalculados nem verificados independentemente durante a preparação deste documento.**

O escopo é deliberadamente limitado. Desempenho numa família finita de alvos, sob um orçamento específico, não demonstra generalização universal para qualquer função ou domínio.

### Quando o experimento passou a auditar seus próprios controles

A análise posterior comparou os executores Linux e Termux. Segundo o relatório anterior, os 490 registros comparados tinham zero divergências nos seis campos semânticos selecionados. Essa afirmação significa concordância nos campos examinados, não identidade dos executores nem equivalência completa dos procedimentos.

O código Termux fornecido no diálogo contém verificações da trilha de consultas contra o oráculo, de consultas duplicadas, do orçamento, do contador de consultas e da candidata nos 16 pontos do domínio quando declara identificação exata. Também verifica o hash do manifesto e exige 70 tabelas-verdade distintas.

A leitura estática identificou diferenças de controle relevantes: o executor apresentado não verifica diretamente o hash de `PREREG-v2.md`; registra os resultados brutos sem reproduzir as mesmas rotinas de agregação e curvas atribuídas ao executor Linux; e permite que informações de proveniência do repositório sejam registradas como `UNAVAILABLE` quando variáveis de ambiente não estão definidas. O código registra `expected_trials` e `actual_trials`, mas o trecho examinado não mostra uma interrupção explícita caso esses valores divirjam.

Esses achados delimitam o que o código apresentado faz. Não demonstram que o estudo original jamais tenha tido pré-registro, nem invalidam automaticamente resultados existentes. Demonstram que a equivalência integral dos controles não está estabelecida pelo código analisado.

### Reprodução corretiva não é pré-registro prospectivo

O próprio executor Termux identifica a saída como `RAW_CORRECTIVE_AUDIT_RESULTS` e declara que se trata de reprodução corretiva, não de pré-registro prospectivo do estudo original. Essa distinção deve permanecer explícita: uma reconstrução retrospectiva não pode ser apresentada como se todas as decisões tivessem sido fixadas antes da execução original.

A decisão de não repetir os 490 ensaios preserva os artefatos existentes e evita uma nova execução desnecessária para responder a uma pergunta que é, neste momento, principalmente procedimental. O trabalho prioritário é documentar a proveniência, comparar os controles e registrar as pendências.

### O significado para Aurora × TUU

A auditabilidade não é um adorno documental. É o mecanismo pelo qual uma conclusão pode ser questionada, reproduzida e, quando necessário, limitada. Uma cadeia responsável distingue:

- o que foi observado diretamente;
- o que foi relatado por uma execução anterior;
- o que foi calculado ou verificado independentemente;
- o que é interpretação;
- o que permanece em aberto.

A mesma disciplina vale para acesso e execução. Conhecer o caminho de um arquivo não significa conseguir lê-lo; ler um arquivo não significa ter autorização para alterá-lo; executar uma operação não significa que ela tenha sido bem-sucedida; e uma saída sem erro de infraestrutura não comprova, por si só, a hipótese científica.

O Aurora × TUU procura estruturar esse rigor em torno de observação, execução e comunicação, com limites explícitos e supervisão humana. O objetivo não é tornar as conclusões imunes a questionamentos, mas criar condições para que os questionamentos sejam respondidos com evidências e critérios verificáveis.

### Conclusão delimitada

A conclusão sustentada pelo material analisado é: **os resultados comparados anteriormente foram relatados como concordantes nos campos semânticos examinados; foram identificadas diferenças entre os controles dos executores; a equivalência integral dos procedimentos de auditoria permanece não demonstrada.** A reprodução corretiva não deve ser interpretada como validação universal da generalização.

O valor desta etapa está em preservar simultaneamente o achado positivo e a divergência ainda aberta. Uma hipótese torna-se investigação; a investigação, evidência organizada; e a evidência, uma base mais confiável para a próxima decisão.

---

## Registro de proveniência disponível nesta revisão

Os valores abaixo foram fornecidos no histórico da conversa. Eles identificam os artefatos referidos, mas não substituem uma nova verificação dos arquivos originais.

| Artefato | SHA-256 relatado |
|---|---|
| `AMENDMENT-001.md` | `f4b8550b89f598a6e10b5a65896e5e65934220400ac01b4910f213069be4b1ab` |
| Executor Linux dentro do pacote Linux | `82a61fcb520f9197daee168576f9796252d056ed0c96e239159b9de792ba323a` |
| `B1-GEN-01A-termux-runner_v2.py` | `ab4c3ead8491d32df7d0b125f842b91aa3c27e385f0e9f709747b945baa47f21` |

### Pendências

1. Revalidar diretamente os conjuntos originais de resultados e documentar os seis campos comparados.
2. Comparar os dois executores completos, não apenas a análise estática do runner Termux.
3. Definir se a validação do pré-registro, a integridade do repositório e a validação dos agregados são critérios obrigatórios de aceitação.
4. Preservar a distinção entre evidência histórica relatada e verificações realizadas nesta revisão.
5. Não repetir os 490 ensaios sem uma justificativa técnica específica e um plano aprovado.

**Estado:** narrativa adicionada para revisão; nenhum benchmark foi executado por esta alteração e nenhuma mudança foi mesclada em `main`.
