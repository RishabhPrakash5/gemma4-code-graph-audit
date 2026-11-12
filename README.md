# An Audit of the Code Graphs and Embeddings Provided for Gemma 4

Code and paper for a submission to the paper track of the Kaggle competition
"Google - The Gemma 4 Developer Agent Competition".

The competition gives a coding agent three tools that search a code graph and node embeddings. This work checks,
without running any model, whether those tools find the function that the real fix changes, and compares them with
reading the names in the issue, with grep, and with a random pick of the same size. It also reports nine leaderboard
submissions and how 20 traced agent runs failed.

The paper is in [`paper/paper.md`](paper/paper.md).

## What is here

| Path | What it does |
|---|---|
| `paper/paper.md` | The paper |
| `experiments/graph-localization/localization.ipynb` | The offline localization test (Table 2, Section 5.3). Outputs are saved, so the numbers can be read without running it |
| `experiments/graph-localization/where_names_point.py` | Table 3: how the names in each issue relate to the fixed function |
| `experiments/trace-analysis/trace_analysis.ipynb` | Table 4 and the context measurements in Section 3, with saved outputs |
| `scripts/fetch_data.sh` | Downloads the competition data and the four source repositories |
| `scripts/task_and_graph_stats.py` | The task and graph counts quoted in Sections 3 and 5.3 |

## How to reproduce

You need Python 3.11+ with `numpy` and `pandas`, `git`, and the Kaggle CLI logged in with the competition rules
accepted. Everything runs on a CPU.

```bash
bash scripts/fetch_data.sh
python scripts/task_and_graph_stats.py
```

Then run `experiments/graph-localization/localization.ipynb` from top to bottom. The first run builds a source index
for every snapshot and takes about five minutes; later runs take about a minute. After it, run
`python where_names_point.py` from the same folder.

## What is not here

- The competition data (tasks, gold patches, graphs, embeddings). The competition rules do not allow
  redistributing it, so `scripts/fetch_data.sh` downloads it from Kaggle instead.
- The agent traces behind Table 4. They contain task text and repository code, so only the analysis notebook and
  its saved outputs are included.
