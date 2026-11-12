"""Numbers quoted in Sections 3 and 5.3 of the paper: issue length, fix size, and graph size.

Run from the repository root after scripts/fetch_data.sh:  python scripts/task_and_graph_stats.py
"""
import glob
import json
import re
import statistics

tasks = [json.loads(line) for line in open("competition_data/tasks.jsonl", encoding="utf-8")]

# Issues and fixes
short = sum(len(t["problem_statement"].strip()) < 200 for t in tasks)
hints = sum(bool((t.get("hints_text") or "").strip()) for t in tasks)


def source_files(patch):
    files = set(re.findall(r"^\+\+\+ b/(\S+)", patch, re.M))
    return [f for f in files if f.endswith(".py") and not f.startswith(("docs", "docs_src", "tests"))]


one_file = sum(len(source_files(t["patch"])) == 1 for t in tasks)
added = [sum(1 for l in t["patch"].split("\n") if l.startswith("+") and not l.startswith("+++")) for t in tasks]
print(f"tasks: {len(tasks)}")
print(f"issues shorter than 200 characters: {short} | tasks with hints: {hints}")
print(f"gold patches changing exactly one Python source file: {one_file}")
print(f"median lines added per patch: {statistics.median(added)}")

# Graphs
nodes = edges = 0
edge_types = {}
for f in glob.glob("competition_data/graphs/*.json"):
    g = json.load(open(f, encoding="utf-8"))
    nodes += len(g["nodes"])
    for e in g["edges"]:
        edges += 1
        edge_types[e.get("type")] = edge_types.get(e.get("type"), 0) + 1
print(f"graph snapshots: {len(glob.glob('competition_data/graphs/*.json'))}")
print(f"nodes: {nodes} | edges: {edges} | edge types: {edge_types}")
