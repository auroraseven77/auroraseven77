# AURORA EXECUTOR 01 / TELOS — Triagem de projetos

**Data:** 2026-10-26  
**Escopo do executor:** sandbox desta sessão e APIs/conectores explicitamente disponíveis. Não presumir acesso ao Termux, Snowflake, outros repositórios privados ou execução no dispositivo do usuário.

## Inventário e classificação

| Projeto | Estado atual baseado na evidência disponível | O que falta | Viabilidade | Definição de done | Dependências | Esforço estimado |
|---|---|---|---|---|---|---|
| Aurora Evidence Ledger v0.1.0 | Pacote existente no sandbox; CLI, esquema, exemplo e suíte de testes presentes; reexecução local de 16 testes passou | Registrar este run TELOS, validar cadeia, reempacotar e calcular hashes finais | **VIAVEL** | Fonte, esquema, README, exemplo, log de teste; suíte de testes passa; ledger do run verifica; ZIP e SHA-256 finais disponíveis | Nenhuma | Baixo |
| TELOS — relatório de execução e ledger do run | Trilha TELOS parcial até a fase atual | Produzir triagem, capturar inventário confirmado, registrar execução e avaliação no ledger | **VIAVEL_COM_DEPENDENCIA** | Triagem completa; eventos DECLARADO/EXECUÇÃO/EVIDÊNCIA/AVALIAÇÃO encadeados; verificador passa; cada artefato de execução tem hash | Evidence Ledger v0.1.0 | Baixo |
| Aurora/TUU — estado de auditoria documental | Repositório `auroraseven77/auroraseven77` acessível por GitHub; `STATUS.md`, `COMPONENT-STATUS.md`, `EVIDENCE-INDEX.md` e `REPRODUCIBILITY.md` lidos; PR #30 aberto no momento do inventário | Checkout de teste e execução de CI não foram feitos neste ambiente; atualizações de estado exigem nova evidência | **VIAVEL_COM_DEPENDENCIA** | Snapshot só é atualizado com saída reproduzível, commit e hashes verificáveis; nenhuma mudança em `main` | Checkout isolado e artefatos originais | Médio |
| Cognitive Core B7/B8 / predição e temporalidade | PRs e registros de verificação existem no histórico do GitHub; testes são relatados nos PRs/documentos | Reproduzir testes a partir de checkout e fixar commit/ambiente | **NAO_VIAVEL** nesta rodada de execução local | Checkout íntegro no commit definido, testes direcionados e suíte relevante passam; relatório liga saída e hash ao commit | Checkout do repositório, ambiente Python/dependências | Médio/alto |
| B1 motor / MPS / B1.2 | Código e contratos são referenciados na documentação TUU; política documental declara `b1_motor/` congelado para a auditoria | Ambiente de testes reproduzível e artefatos de execução originais; não alterar código de produção nesta rodada | **VIAVEL_COM_DEPENDENCIA** | Testes permitidos passam em ambiente identificado e artefatos têm manifesto/hash; nenhuma alteração fora do escopo aprovado | Checkout e ambiente compatível; preservar congelamento do núcleo | Alto |
| B1.3 — validação de energia | Branch `feat/b1.3-energy-validation-harness` aparece no inventário do GitHub; 34 testes são resultado reportado, não reproduzido nesta sessão | Recuperar branch/artefatos originais e executar a suíte em ambiente documentado | **VIAVEL_COM_DEPENDENCIA** | Testes da branch exata passam; relatório inclui commit, Python, saída e hashes; nenhuma inferência para N=64 ou vantagem quântica | Checkout correto e dependências | Médio/alto |
| B1-GEN-01A — síntese por consultas | Documentação publicada indica BLOQUEADO: faltam `target-manifest.json`, `TARGET-MANIFEST-SHA256SUMS` e diretório de testes esperado | Obter artefatos originais sem alterar bytes, verificar hashes, integrar runner/oráculo/avaliador independente | **VIAVEL_COM_DEPENDENCIA** | Manifesto e hashes validados; testes isolados passam; protocolo congelado antes de qualquer benchmark | Artefatos originais e ambiente limpo | Alto |
| AC4-R2 — episódio histórico | A integridade do ledger foi reportada, mas recuperação histórica não demonstrada | Localizar artefatos v0–v08 e proveniência original | **NAO_VIAVEL** | Episódio reconstruído a partir de artefatos originais e cadeia de proveniência verificada independentemente | Arquivos históricos ausentes | Alto |
| B11 — Navier–Stokes P14–P19 | Documentação afirma que artefatos P14–P19 não foram confirmados; prova global não demonstrada | Localizar originais, versões, hashes e dependências matemáticas | **NAO_VIAVEL** | Cada argumento é rastreável a fonte e revisão matemática independente; nenhuma alegação global sem prova válida | Artefatos originais e revisão independente | Muito alto |
| RCS Nighthawk — circuitos | Correspondência/regeneração foi relatada, não reproduzida independentemente | Job IDs, logs, entradas, saídas e ambiente | **NAO_VIAVEL** | Execução independente reproduz a correspondência ou explica a divergência, com artefatos hashados | Logs/job IDs ausentes | Alto |
| `aurora_phase1/` — laboratório cognitivo multiagente | Documentação e testes são referenciados no repositório; estado operacional atual não reproduzido aqui | Checkout e execução direcionada; confirmar parâmetros/logs atuais | **VIAVEL_COM_DEPENDENCIA** | Testes relevantes reproduzidos com commit/ambiente registrados; limitações preservadas | Checkout isolado | Médio/alto |
| `osint-toolkit/` | README e testes são referenciados no inventário do repositório, mas não há alvo/deliverable operacional especificado nesta rodada | Definir artefato final e escopo autorizado; executar somente testes locais, não reconhecimento externo | **REQUER_DECISAO** | Entregável e critérios escolhidos pelo usuário; testes locais passam; nenhum alvo externo sondado sem autorização | Decisão de escopo | Médio |
| MCP Aurora / servidor e integração Android-Termux | O histórico registra projeto MCP read-only e um protótipo; não há conexão direta ao Termux nesta sessão | Executar comandos no Samsung e devolver saídas sanitizadas; confirmar endpoint/transport real | **FORA_DE_ESCOPO** | Handoff executado pelo usuário; transcript sanitizado e hashes verificáveis; nenhuma endpoint presumida | Handoff Termux; acesso físico do usuário | Médio/alto |
| Snowflake / RBAC / histórico administrativo | O histórico indica conexão previamente indisponível; nenhum acesso ao tenant foi observado nesta rodada | Executar consultas de leitura pelo operador autorizado e exportar grants/history sanitizados | **FORA_DE_ESCOPO** | Resultados de role/grants e histórico com timestamp/escopo, mais prova de permissões efetivas, revisados sem acesso a segredos | Sessão Snowflake autorizada pelo usuário | Médio |
| Aurora Assistant — plugin privado | Plugin Creator lista `aurora-assistant` privado, versão 0.4.0; arquivos/versão foram inventariados sem mutação | Definir se o plugin deve receber alteração de produto ou apenas documentação; mudança externa ao repositório exige escopo específico | **REQUER_DECISAO** | Escopo e release-alvo confirmados; atualização de versão e regressão verificadas; URL/release registrados | Decisão sobre mutação do plugin | Médio |
| CERBERUS-3 / KRONOS | Há relatórios de sondagens anteriores, mas não foi criada nesta rodada uma nova execução no ambiente-alvo; KRONOS permanece sem execução confirmada | Vincular cada resultado a transcript do ambiente real e executar handoff permitido | **FORA_DE_ESCOPO** para ambiente-alvo; documentação local é viável | Log real sanitizado, ambiente e comando identificados, estados epistêmicos corretos e hashes verificados | Handoff ao ambiente real | Médio |
| AEGIS — análise sintética de aquisição | Existem resultados resumidos no contexto, mas não o script/entrada completos para reprodução independente da análise original | Recuperar premissas, fórmulas e dados de origem | **NAO_VIAVEL** para reproduzir a análise original nesta rodada | Script e dados reproduzem os resultados originais; testes e relatório de premissas completos | Entrada/fórmulas originais | Médio |
| Comparação TUU × Aurora Program externo | O contexto contém referências e alegações resumidas, mas não um corpus completo e versionado de fontes | Organizar fontes primárias, hashes, data e matriz de similaridade com limites explícitos | **VIAVEL_COM_DEPENDENCIA** | Matriz de alegações vinculada a fontes primárias, com datas, hashes e distinção entre coincidência conceitual e evidência de cópia | Corpus/source list verificável | Médio |
| Repositórios auxiliares citados no histórico (`*-test`, `*-v21-validation`, `*-b12-audit`, `*-b13-repro`, `*-b13-energy`, `mcp-aurora*`) | Chamadas GitHub a esses nomes retornaram 404 no conector desta sessão | Confirmar URL/owner correto ou fornecer acesso; 404 aqui não prova que não existam em outro escopo | **NAO_VIAVEL** via conector atual | Repositório correto fica acessível, branch/commit identificados e arquivos recuperados sem segredos | Identificador/acesso correto | Baixo após desbloqueio |

## Ordem de execução selecionada

1. Revalidar o Evidence Ledger v0.1.0 localmente e produzir prova de execução nesta rodada.
2. Gerar a trilha TELOS em JSONL usando o próprio ledger, validar a cadeia e empacotar os artefatos.
3. Publicar um relatório de triagem em branch de feature e abrir PR draft no único repositório GitHub confirmado, sem alterar `main`.
4. Produzir handoffs para itens fora de escopo; não executar operações no Termux/Snowflake.

## Limite de evidência

GitHub confirmou acesso a `auroraseven77/auroraseven77` e a `main` com HEAD observado durante a inspeção: `09664068c68d0a2c7f31128e0a9a3ba164b5cd97`. Os outros repositórios consultados foram `NOT_FOUND` pelo conector; isso não prova sua inexistência em outro escopo. O plugin privado `aurora-assistant` foi observado em v0.4.0. Os resultados de teste desta rodada são distintos dos resultados históricos apenas relatados.


## Adendo de estado remoto — 2026-10-28

Esta seção complementa a triagem datada de 2026-10-26; não substitui os registros históricos nem afirma que os testes foram executados nesta sessão.

- **Base consultada:** branch `main`, HEAD `a3f51c544400ce1be49dc2b098d4b6a7600bd5b9` (commit de 2026-10-27: `fix(mps): return normalized observable expectations after truncation (#53)`).
- **TELOS H1:** a saída Termux fornecida pelo operador reporta CRC/caminhos aprovados, 16/16 testes depois de definir `PYTHONPATH` e ledger exemplo válido. Esta atualização documental classifica essa evidência como reportada pelo operador, não como execução independente.
- **PR #31 e #32:** ambas mescladas. A presente atualização não reabre nem altera essas PRs; é proposta nova em branch documental.
- **PR #1 — invariantes v2.1:** aberto, branch `feat/tuu-v2.1-invariants`, HEAD `95706329ad7ecb95d8f3176024c511ee8d98e446`; comparação de refs: 14 commits à frente e 128 atrás de `main`; GitHub reportou `mergeable_state=dirty`. O HEAD consultado não tinha check-runs associados. Não deve ser integrado sem reconciliar o delta e validar toda a suite.
- **PR #2 — packaging:** aberto, branch `fix/tuu-package-foundation-v2`, 1 commit à frente e 128 atrás de `main`; seus check-runs históricos em 2026-09-18 falharam durante coleta por `RecursionError` no alias recursivo de `JsonValue`. O `main` atual usa `TypeAliasType` em `TUU/authorization.py`, então a correção desse ponto não deve ser aplicada novamente sem reprodução atual. A branch também remove testes de integração preexistentes; preservar cobertura é requisito.
- **PR #3 — contrato MPS/HERMES:** mesclada em 2026-10-26.
- **PR #30 — fixture de ciclo de vida:** aberto, branch `audit/pr4-test-migration`, 3 commits à frente e 118 atrás de `main`. O check Core mais recente registrado para esse head foi sucesso, mas o pipeline de integração de 2026-10-16 falhou na coleta: os testes legados tentaram importar `TUUCore` que não existe no módulo `tuu_core` atual. Tratar como falha real de compatibilidade de testes, não como prova de falha de todo o core.
- **Limite de acesso:** esses resultados foram lidos via GitHub API/conector. Nenhum checkout local, teste TUU nesta sessão, alteração do Termux ou acesso ao banco SQLite foi executado.

## Próximos gates de caracterização TUU

Antes de portar qualquer código dos PRs antigos, adicionar testes contra o `main` atual e executar os testes no checkout isolado com commit e ambiente registrados:

1. **Score negativo:** caracterizar a rejeição de `raw_score < 0` e confirmar que a validação não converte silenciosamente score inválido em zero.
2. **Desempate:** igualdade exata deve continuar determinística por SHA-256; decidir explicitamente se a regra normativa também define empate por `abs(delta) < 1e-9`. Testar abaixo, exatamente no limite e acima do limite, incluindo permutação da ordem de candidatos.
3. **Bruto versus arredondado:** testar a diferença entre `H_N/K_N` em precisão bruta e os campos de apresentação arredondados; validar qual representação alimenta a decisão antes de portar a implementação RAW-first.
4. **Isolamento da autorização:** provar que consenso/score nunca chama executor quando a autorização nega, e que score alto ou consenso unânime não altera a decisão do gate.

Critério de conclusão: testes passam na base escolhida ou demonstram, com falha reproduzível, uma divergência contratual. Nenhum resultado desta triagem substitui essa execução.


## Decisão de portabilidade após caracterização — 2026-10-28

### Evidência desta rodada

- Base testada: branch *main*, HEAD `a3f51c544400ce1be49dc2b098d4b6a7600bd5b9`.
- Caracterização: PR #57, HEAD `d872bc39e1be60d777e5087a9926d67f49d01f94`; 7/7 check-runs concluídos com sucesso.
- Logs do GitHub Actions: `pytest tests/` coletou e passou **61 testes** em Python 3.11 (0,58 s) e **61 testes** em Python 3.12 (0,69 s). `pytest tests/ TUU/tests/` coletou e passou **80 testes** (0,53 s). O log confirma execução de todos os testes em `tests/test_tuu_main_characterization.py`.
- A suíte caracteriza o comportamento atual; ela não decide, por si só, qual regra normativa futura deve ser escolhida.

### Decisão por PR antigo

| PR | Decisão | Fundamentação e porta de entrada |
|---|---|---|
| **#1 — invariantes v2.1 / RAW-first** | **Não integrar inteiro. Avaliar portabilidade seletiva após congelar contrato.** | A branch está divergente e a main atual rejeita score bruto negativo. O PR #1 muda esse comportamento para clamp em zero; esse trecho não deve ser portado. A tolerância de desempate `< 1e-9` e a decisão usando `K_N` bruto diferem do comportamento atual caracterizado; exigem decisão normativa antes da implementação. `InvariantEngine` e testes independentes podem ser avaliados em patch mínimo depois desse contrato, sem quarantinar a suíte de integração atual. |
| **#2 — packaging** | **Não integrar inteiro. Separar possível mudança de empacotamento.** | A main consultada não contém `pyproject.toml`; existe uma necessidade legítima a avaliar. Porém a branch #2 remove dois testes de integração existentes e os check-runs históricos falharam durante coleta por `RecursionError` em `JsonValue`. A main atual já usa `typing_extensions.TypeAliasType`; não reaplicar essa correção sem reproduzir. Um novo patch de packaging deve preservar a suite atual, incluir descoberta para `TUU*` e `Tuu_panel*` e declarar dependências diretas usadas pelo pacote; testar wheel/editable install em Python 3.11/3.12. |
| **#3 — contrato MPS/HERMES** | **Já mesclado; nenhuma portabilidade pendente.** | GitHub confirma merge em 2026-10-26. |
| **#30 — fixture/concurrency/lifecycle** | **Não integrar inteiro.** | A branch está 118 commits atrás da main. Seu diff troca o teste de score negativo de rejeição para clamp em zero, contradizendo a caracterização atual. As atualizações da API de lifecycle e o isolamento por `LifecycleResult.events` já aparecem nos testes da main; a integração da branch antiga falhou ao coletar testes que importavam `TUUCore`, ausente da API atual. Só reconsiderar asserções que se provarem únicas e ainda necessárias após comparação individual. |

### Contratos caracterizados e proposta de destino

1. **Score negativo:** preservar o comportamento atual de rejeitar `raw_score < 0`; não portar clamp implícito.
2. **Desempate:** a main usa igualdade exata para acionar SHA-256. O conjunto caracterizado testa diferenças de 0.5e-9, 1e-9 e 2e-9. A proposta v2.1 trata apenas `abs(delta) < 1e-9` como empate. Antes de alterar a produção, registrar decisão explícita: igualdade exata ou tolerância estrita inferior a (10^{-9}).
3. **Bruto versus arredondado:** a main arredonda o score calculado a 4 casas e `H_N/K_N` a 6 casas; a caracterização encontrou uma fronteira em que `K_N` bruto fica abaixo do limite, mas `K_N` arredondado alcança o limite configurado. **Recomendação técnica:** usar valores brutos para decisões e valores arredondados apenas para apresentação/telemetria, após decidir e documentar a mudança de contrato e compatibilidade da API.
4. **Autorização:** os testes confirmam que um score alto não contorna o gate: candidato rejeitado permanece `blocked`, sem execução de `execute_command_securely`. Preservar esse isolamento independentemente do algoritmo de consenso.

### Execução do gate RAW-first — 2026-10-28

O gate anterior avançou para implementação seletiva, sem integrar PRs antigos:

- PR #58: [feat(tuu): use raw precision for consensus and lifecycle gates](https://github.com/auroraseven77/auroraseven77/pull/58).
- Branch: `feat/tuu-raw-first-main-20261028`.
- Base: `main` HEAD `a3f51c544400ce1be49dc2b098d4b6a7600bd5b9`.
- HEAD do PR: `1833b6bbc41e7a4abe3eda2de6e93376a0509225`.
- Escopo: apenas `TUU/tuu_core.py` e o novo `tests/test_tuu_raw_first.py`; nenhum código B1.3 nem a branch `main) foi alterado.
- Verificação: 7/7 checks GitHub Actions passaram. `pytest tests/`: 60 testes aprovados em Python 3.11 e 60 em Python 3.12. `pytest tests/ TUU/tests/`: 79 aprovados. Os logs identificam todos os oito testes RAW-first como aprovados.
- Score negativo continua rejeitado; os scores candidatos e gates de lifecycle usam precisão bruta. A API pública `calculate_swarm_consensus` conserva a tupla de quatro valores arredondados para compatibilidade; `LifecycleResult` e eventos passam a expor campos brutos.
- O desempate continua por igualdade exata e SHA-256. A tolerância `1e-9` não foi portada nem decidida nesta mudança.
- PR #58 está aberto para revisão, sem merge. CI usa runners Linux; a validação Android/Termux não foi executada.

### Próximo gate

1. Revisar o diff e a semântica pública adicionada no PR #58; confirmar especialmente a compatibilidade dos campos `LifecycleResult` e a política para lifecycle com candidato único e score abaixo de `s_min`.
2. Decidir em separado se a norma de desempate usa igualdade exata ou `abs(delta) < 1e-9`. Não combinar essa mudança com a correção RAW-first sem aprovação de contrato.
3. Depois da revisão do PR #58, avaliar o empacotamento do PR #2 como alteração mínima independente, preservando a suíte completa. Nenhum PR antigo deve ser mesclado como atalho.
4. Validar Termux separadamente apenas se/quanto necessário; CI Linux não comprova compatibilidade Android nem integração SQLite/WAL.

