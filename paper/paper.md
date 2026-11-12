# An Audit of the Code Graphs and Embeddings Provided for Gemma 4

### An offline, model-free localization test against gold patches, with leaderboard ablations and a failure analysis of agent runs

## ABSTRACT

The following study investigates whether the code graphs and embeddings provided with the Gemma 4 Developer Agent competition help a small, locally served coding agent find the code that must change, and where the agent fails instead. The agent is Gemma 4 31B in the competition's fixed harness, with 8 minutes and 28 tool calls per task. Three kinds of evidence are reported: nine leaderboard submissions, a failure analysis of 20 traced runs, and an offline, model-free localization test on the 129 public tasks in which every retrieval method is compared with a random set of the same size. It is found that embedding search is close to chance once its output size is accounted for, that the graphs contain none of the 1,918 `async` functions, and that the graph tools add a find in only 3 of 63 tasks. The issue text is the strongest signal, since its names are the fixed function, or one step from it, in 84% of the tasks that name code. The agent rarely edits the wrong file. It fails by running out of budget or by writing a wrong fix.

**Keywords:** coding agents, fault localization, code graphs, code embeddings, Gemma 4, evaluation noise.

## 1. INTRODUCTION

Autonomous coding agents that resolve real GitHub issues are mostly built on large models served from the cloud. The Gemma 4 Developer Agent competition asks whether an open model on modest hardware can do the same. Gemma 4 is served by vLLM on four L4 GPUs, and each submission is scored by the hidden tests of about 120 tasks from private repositories. A submission can change only the prompt, settings, sub-agents, skills and LoRA adapters.

Under such a budget, an agent has to find the code that must change and edit it before its time or tool calls run out. To help with the first step, the organizers provide a code graph and node embeddings for every repository snapshot, exposed through three tools: `get_code_neighbors`, `search_similar_code` and `get_code_subgraph`. Before an agent is trained or prompted to rely on these tools, it is necessary to know whether they point to the right code, and whether finding the code is where the agent fails at all. Hence, this study measures both.

The contributions of this paper are:

1. An audit of the provided graphs and embeddings, including what they omit.
2. An offline, model-free localization test on all 129 public tasks, with the tools re-implemented as the harness runs them and every method compared with a random set of the same size. It runs on a CPU in minutes and suits any retrieval tool.
3. A measurement of where the localization signal lies, which is in the names the issue mentions.
4. Measured harness costs and leaderboard ablations, which plateau within the leaderboard's standard error.

## 2. LITERATURE REVIEW AND OBJECTIVE

Notable research on repository-level issue resolution starts with SWE-bench (Jimenez et al., 2024), which defined the task format used here. SWE-agent (Yang et al., 2024) showed that the agent-computer interface, including how much output each tool returns, changes the success rate. Agentless (Xia et al., 2024) localizes hierarchically (file, function, line) without an agent loop, and AutoCodeRover (Zhang et al., 2024) searches the code through its syntax tree. RepoGraph (Ouyang et al., 2025), CodexGraph (Liu et al., 2025) and LocAgent (Chen et al., 2025) report gains from repository graphs used with strong models. Embeddings learned from graph structure, such as node2vec (Grover & Leskovec, 2016), encode a node's position rather than what its code does. SWE-Gym (Pan et al., 2024) trained agents by rejection-sampling fine-tuning on their own successful runs.

Studies that compare each retrieval tool with a random set of the same size, or that measure what a provided code graph omits, are scarcely reported. Therefore, the objective of this paper is to measure, without running the model, how much each provided signal narrows the search for the code that must change, and to relate this to how the agent actually fails under the competition's budget.

## 3. PROBLEM DESCRIPTION

**Tasks**

The public data has 129 tasks from fastapi (67), rich (48), requests (13) and httpx (1). Each gives the issue text and base commit, and the gold patch is used here only as the answer key. No task has hints, and 38 issues are shorter than 200 characters, typically a pull-request title and a "Fixes #NNNN" link that the offline sandbox cannot open. The fixes are small: 89 of the 129 gold patches change exactly one Python source file, and the median patch adds 8 lines. The public leaderboard scores about 58 tasks, so one task is worth about 0.017.

**Harness**

`swegemma` 0.2.11 serves the model with vLLM 0.19.1 on 4× L4 with a 32,768-token context and nine tools, including shell commands, file reading and editing, and the three graph tools. The whole run has a 12-hour limit.

**Measured constraints**

1. vLLM rejects any request whose prompt plus `max_output_tokens` exceeds 32,768, and the task crashes. With the sample's 16,384 output tokens, the conversation is capped at 16k.
2. Over 426 consecutive call pairs, the prompt grew by 1.00 × reply tokens + 0.281 × tool-output characters + 13 (R² = 0.91). Hence, the whole reply, thinking included, stays in the context.
3. Context compaction fires inside a task once prompt plus reply passes 14,336 tokens. It fired 35 times in 20 traced tasks, and that step took a median 19.7 s against 2.7 s for a normal step.

## 4. METHODOLOGY

### 4.1 Leaderboard experiments

Each submission changed one factor relative to an earlier one, except 004 and 009 (stated in Table 1). The hypothesis and a decision rule were recorded before each score came back. The settings of every configuration are given in Appendix A.

### 4.2 Offline localization test

**Gold functions**

The lines changed by each gold patch were mapped onto the functions and methods (including `async` ones) whose line span contains them, by parsing the source at the base commit with Python's `ast` module. This mapping is independent of the provided graph, so a function missing from the graph shows up as a miss, not a labelling error. 122 of the 129 tasks have a gold function.

**Clues**

Code-like names were taken from the issue text (backticked code, dotted, `snake_case` and `CamelCase` tokens) and resolved as the harness resolves a node query, by dotted path or suffix. Only 64 of the 129 issues name a symbol that resolves, and the 63 of these with a gold function form the main test set.

**Methods**

Each method was copied from the harness source:

- *named in issue*: the resolved symbols themselves.
- *embeddings*: top 5 or top 10 nodes by raw cosine similarity per named symbol (`search_similar_code`).
- *graph neighbours*: all one-hop neighbours of each named symbol, alphabetical, capped at 50 (`get_code_neighbors`).
- *grep*: all functions whose code contains a named symbol as a whole word.
- *keyword fallback*: `search_similar_code` with the issue title as free text, which the harness scores by keyword overlap.
- unions of two methods.

**Metric and baseline**

A method scores a hit when its returned set contains any gold function, and its cost is the median number of functions returned. As a baseline, the probability that a random set of the same size, drawn from the snapshot's non-test functions, contains a gold function was computed per task and averaged. A method is useful only if it beats this baseline at its own size.

### 4.3 Trace analysis

Ten tasks, sampled in proportion to the repositories, were run in a Kaggle 4× L4 notebook with the configuration of submission 002, once with the 31B and once with the 12B model. Each task was given one label by the first matching rule (Table 4).

## 5. RESULTS AND DISCUSSION

### 5.1 Validation

The results rest on three checks. First, the tool logic was copied from the harness source, and the gold functions were mapped without the graph. Second, the resolution of the leaderboard was estimated. A score p measured on n = 58 tasks has a standard error of √(p(1−p)/n), which is about 0.05 at p = 0.16. Hence, differences smaller than about three tasks (0.05) are not resolved, and every comparison below is read in this light. Third, a share measured on the 63 offline tasks has a 95% range of about ±0.10-0.12.

### 5.2 Scaffold and model experiments

**Table 1: Public leaderboard scores (thinking on, temperature 0.2 unless stated). Full settings in Appendix A.**

| # | Change | Model | Score |
|---|---|---|---|
| 001 | Organizers' sample (1 min, 10 tool calls) | 31B | 0.03 |
| 002 | Budget only: 5 min, 30 calls | 31B | 0.15 |
| 003 | 002 on 12B | 12B | 0.05 |
| 004 | Budget-aware scaffold (8 min, 28 calls, call plan, graph tools banned) | E4B | 0.08 |
| 005 | 004 on E2B | E2B | 0.03 |
| 006 | 004 on 31B | 31B | **0.18** |
| 007 | 006 with the sample prompt | 31B | 0.15 |
| 008 | 006 with temperature 0.7 | 31B | 0.15 |
| 009 | 006 + thinking 2,048, two graph tools removed, search steps in prompt | 31B | 0.15 |

The budget is the first lever, since raising the limits alone moved the score from 0.03 to 0.15. Under a fixed time budget the larger model wins. With the same scaffold, E2B, E4B and 31B scored 0.03, 0.08 and 0.18, and the 12B's faster decoding did not make up for its weaker reasoning (0.05 against 0.15). Beyond this point the scores plateau. Submissions 007, 008 and 009 changed the prompt, the temperature and the search procedure, and all three scored 0.15, the same as 002. The 0.18 of 006 lies within one standard error of these scores, so it cannot be read as a gain.

### 5.3 Audit of the provided graphs and embeddings

The 127 graph snapshots hold 367,985 nodes, about 300k functions and methods and 68k classes, with no module or file nodes. All 452,588 edges are labelled `calls` and stored in both directions, so callers and callees cannot be told apart, and class-to-method links are also labelled `calls`. Each node has one 256-dimensional vector.

None of the 1,918 `async def` functions in the package sources is a node, nor are nested functions, while every plain `def` and 16,365 of 16,441 classes are present. As a result, 16 tasks have a gold function that the graph tools cannot return (11 partly, 5 entirely), almost all from FastAPI, which uses `async` functions heavily.

The embeddings behave like graph-position embeddings (Grover & Leskovec, 2016). In an earlier probe, connected pairs had a cosine similarity of about 0.90 after centring, against about 0 for random pairs. Yet only 7% of an embedding top-10 are direct neighbours of the query. `search_similar_code` uses no language model. A symbol query is raw cosine over the stored vectors, and free text falls back to keyword scoring.

### 5.4 Offline localization results

**Table 2: Share of the 63 tasks in which each method returns a gold function, its cost, and the chance of a random set of the same size.**

| Method | Hit rate | Functions returned (median) | Random, same size |
|---|---|---|---|
| Named in issue (no tool) | **0.46** | 4 | 0.06 |
| Embeddings, top 5 | 0.17 | 10 | 0.11 |
| Embeddings, top 10 | 0.22 | 20 | 0.16 |
| Graph neighbours | 0.25 | 12 | 0.15 |
| Grep | 0.51 | 73 | 0.28 |
| Keyword fallback (issue title) | **0.40** | 10 | 0.07 |
| Named + embeddings top 10 | 0.56 | 24 | 0.18 |
| Named + neighbours | 0.56 | 18 | 0.18 |
| Named + grep | **0.71** | 75 | 0.30 |

The names in the issue reach a gold function in 46% of tasks at a cost of four functions. The embedding top-10 (0.22) cannot be told apart from a random set of the same size (0.16), while neighbours (0.25 against 0.15) and grep (0.51 against 0.28) are clearly above chance. The keyword fallback gives the best value per function read: 0.40 for ten functions, and 0.30 against 0.06 on all 122 tasks with a gold function, where no issue names are needed. The graph tools find a gold function that neither the names nor grep reach in only 3 of the 63 tasks. Restricted to the 52 tasks whose gold functions are all in the graph, the ordering is unchanged (named 0.44, embeddings 0.17, neighbours 0.21, grep 0.46). At the file level the methods are closer: named 0.62, embeddings 0.68, neighbours 0.67, grep 0.83.

Hence, the graph neighbourhood behaves as a smaller, weaker version of grep, and the embeddings add little beyond what their output size would find by chance.

### 5.5 Where the issue's names point

When the issue's names miss the gold function, they rarely miss by much (Table 3).

**Table 3: Relation between the symbols named in the issue and the gold function (first match wins).**

| The issue names... | Tasks |
|---|---|
| a gold function itself | 29 |
| its class, or another method of the same class | 5 |
| a function that calls it, or that it calls | 9 |
| something the gold function's code uses (e.g. a type) | 10 |
| an unrelated function in the same file | 1 |
| nothing related | 9 |

Thus, 53 of the 63 tasks (84%) name the gold function or something one step from it, and 39 (62%) name something in a gold file. Seven of the nine unrelated cases are FastAPI issues naming only public objects from the reporter's reproduction code, such as `FastAPI` or `Body`. Issues name what the user called, while the fix usually sits in an internal helper one step away.

### 5.6 Failure analysis of agent runs

**Table 4: How the 10 traced tasks ended (configuration of submission 002).**

| Label | 31B | 12B |
|---|---|---|
| Solved | 2 | 0 |
| Wrong fix (right file, tests fail) | 3 | 0 |
| Right file, out of budget | 2 | 3 |
| Never edited | 3 | 3 |
| Edits all failed | 0 | 1 |
| Context overflow | 0 | 3 |

Editing the wrong file never happened, since every task that made an edit touched a gold file. The failures are budget and fix correctness, not finding the file. `read_file` produced 89% of all tool-output characters, so reading whole files is the largest drain on the context. There were 18 `edit_file` calls whose `old_string` did not match, and the 12B overflowed its context in 3 tasks.

## 6. LIMITATIONS

Each configuration was scored once on the leaderboard. The offline test measures the tools at their best, with exact names supplied, not how the model uses them. The gold patch is one valid fix among possibly several. The failure labels come from only 20 runs (2 of 10 solved has a 95% range of about 6-51%), and the hidden tasks come from other repositories.

## 7. CONCLUSIONS

The major findings of this study are:

1. Embedding search is close to chance once its output size is accounted for (0.22 against 0.16), and the graph tools add a find in only 3 of 63 tasks.
2. The graphs contain none of the 1,918 `async` functions, so 16 tasks have a gold function the graph tools cannot return.
3. The issue text is the strongest signal. Its names reach a gold function in 46% of tasks and are the fix or one step from it in 84%. The harness's keyword fallback is the best value per function read.
4. The budget is the first lever (0.03 to 0.15), and the larger model wins under a fixed time budget. Beyond that, prompt and configuration changes plateau at 0.15, within one standard error (about 0.05).
5. The agent rarely fails to find the file. It fails by running out of budget, by writing a wrong fix, or by never editing, in a conversation capped at 16k tokens where compaction fires repeatedly.
6. Any retrieval tool can be checked offline against gold patches, with a random baseline of the same size, in minutes on a CPU, before it is given to an agent.

In future, we intend to post-train the agent with rejection-sampling fine-tuning on its own successful runs, favouring runs that read the named function and follow one step, and to measure the gain with a local evaluation large enough to resolve a three-task difference.

## ACKNOWLEDGEMENTS

The author acknowledges Kaggle for the notebook compute used for the traced runs.

## CODE AND DATA

The analysis code, the paper source and a short guide to reproducing every table are available at https://github.com/RishabhPrakash5/gemma4-code-graph-audit. The competition data is not redistributed there, as the competition rules require.

## REFERENCES

Chen, Z., Tang, R., Deng, G., Wu, F., Wu, J., Jiang, Z., ... & Wang, X. (2025, July). Locagent: Graph-guided llm agents for code localization. In Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers) (pp. 8697-8727).

Grover, A., & Leskovec, J. (2016, August). node2vec: Scalable feature learning for networks. In Proceedings of the 22nd ACM SIGKDD international conference on Knowledge discovery and data mining (pp. 855-864).

Jimenez, C. E., Yang, J., Wettig, A., Yao, S., Pei, K., Press, O., & Narasimhan, K. (2024, May). Swe-bench: Can language models resolve real-world github issues?. In International Conference on Learning Representations (Vol. 2024, pp. 54107-54157).

Liu, X., Lan, B., Hu, Z., Liu, Y., Zhang, Z., Wang, F., ... & Zhou, W. (2025, April). Codexgraph: Bridging large language models and code repositories via code graph databases. In Proceedings of the 2025 Conference of the Nations of the Americas Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers) (pp. 142-160).

Ouyang, S., Yu, W., Ma, K., Xiao, Z., Zhang, Z., Jia, M., ... & Yu, D. (2025, May). Repograph: Enhancing ai software engineering with repository-level code graph. In International Conference on Learning Representations (Vol. 2025, pp. 30098-30121).

Pan, J., Wang, X., Neubig, G., Jaitly, N., Ji, H., Suhr, A., & Zhang, Y. (2024). Training software engineering agents and verifiers with swe-gym. arXiv preprint arXiv:2412.21139.

Xia, C. S., Deng, Y., Dunn, S., & Zhang, L. (2024). Agentless: Demystifying llm-based software engineering agents. arXiv preprint arXiv:2407.01489.

Yang, J., Jimenez, C., Wettig, A., Lieret, K., Yao, S., Narasimhan, K., & Press, O. (2024). Swe-agent: Agent-computer interfaces enable automated software engineering. Advances in Neural Information Processing Systems, 37, 50528-50652.

Zhang, Y., Ruan, H., Fan, Z., & Roychoudhury, A. (2024, September). Autocoderover: Autonomous program improvement. In Proceedings of the 33rd ACM SIGSOFT International Symposium on Software Testing and Analysis (pp. 1592-1604).

## APPENDIX A: CONFIGURATIONS

All configurations use the 31B model unless Table 1 says otherwise, top-p 0.95, and thinking on with its thoughts kept in the context.

**Table A1: Settings per configuration.**

| Setting | 001 (sample) | 002, 003 | 004-007 | 008 | 009 |
|---|---|---|---|---|---|
| Time per task | 1 min | 5 min | 8 min | 8 min | 8 min |
| Tool calls per task | 10 | 30 | 28 | 28 | 28 |
| Command timeout | 60 s | 180 s | 240 s | 240 s | 240 s |
| Maximum output tokens | 16,384 | 16,384 | 8,192 | 8,192 | 8,192 |
| Thinking budget | 4,096 | 4,096 | 4,096 | 4,096 | 2,048 |
| Temperature | 0.2 | 0.2 | 0.2 | 0.7 | 0.2 |
| Helper agent | code analyzer | code analyzer | none | none | none |
| Graph tools offered | all three | all three | all three | all three | `search_similar_code` only |

**Sample prompt (001-003, 007)**

The organizers' sample prompt asks the agent to read the issue, locate the relevant files, make the minimal fix and verify it. It suggests `search_similar_code` with keywords from the error message when the issue gives no file path.

**Budget-aware prompt (004-006, 008)**

This prompt was adapted, with the model line changed, from a public competition notebook ("Gemma 4 Budget-Aware Coding Agent v2"). It sets hard limits (28 calls and 8 minutes, never edit or run whole test suites, never use the three graph tools) and a call plan. Calls 1-8 locate and read, calls 9-12 edit, and the agent must have edited a source file by call 12. Calls 13-20 verify, and the agent then finishes with `git diff` and `submit_patch`. The procedure asks for batched `git grep` searches, reading regions of about 40 lines with `sed`, `edit_file` with an exact `old_string`, at most two targeted test runs, and a final check of the diff.

**Search steps (009)**

Submission 009 replaces the graph-tool ban with three steps derived from the offline test. If the issue names a function or class, the agent finds its definition with `git grep -w`, reads it, and follows one step to what it calls, what calls it, or a helper it uses. If the issue names several identifiers or only describes behaviour, the agent ranks candidate files with `git grep -c` before reading any. If the issue names no code at all, the agent calls `search_similar_code` once with three to six keywords from the issue title, which uses the harness's keyword fallback.
