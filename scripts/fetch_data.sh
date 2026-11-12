#!/usr/bin/env bash
# Downloads what the analysis needs but this repository does not include:
#   competition_data/  tasks.jsonl, graphs/ and embeddings/ for the 129 public tasks (~0.9 GB)
#   reference/repos/   partial clones of the four source repositories (history only, files fetched on demand)
# Needs the Kaggle CLI logged in (~/.kaggle/kaggle.json) and the competition rules accepted.
# Run from the repository root:  bash scripts/fetch_data.sh
set -euo pipefail

COMP=gemma-4-developer-agent
KAGGLE="python -m kaggle"

mkdir -p competition_data
[ -s competition_data/tasks.jsonl ] || $KAGGLE competitions download "$COMP" -f tasks.jsonl -p competition_data -q

echo "== Graphs and embeddings (127 snapshots)"
python - <<'EOF' > competition_data/needed_files.txt
import json
for line in open("competition_data/tasks.jsonl", encoding="utf-8"):
    t = json.loads(line)
    name = f"{t['repo'].split('/')[-1]}_{t['base_commit']}"
    print(f"graphs/{name}.json"); print(f"embeddings/{name}.npz")
EOF
tr -d '\r' < competition_data/needed_files.txt | sort -u | while read -r f; do
  [ -s "competition_data/$f" ] && continue
  mkdir -p "competition_data/$(dirname "$f")"
  $KAGGLE competitions download "$COMP" -f "$f" -p "competition_data/$(dirname "$f")" -q || echo "FAILED: $f"
done

echo "== Source repositories"
mkdir -p reference/repos
for r in fastapi/fastapi Textualize/rich psf/requests encode/httpx; do
  [ -d "reference/repos/$(basename "$r").git" ] || \
    git clone -q --bare --filter=blob:none "https://github.com/$r.git" "reference/repos/$(basename "$r").git"
done
echo "Done."
