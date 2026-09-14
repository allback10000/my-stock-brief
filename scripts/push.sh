#!/usr/bin/env bash
# 세 워크플로가 같은 저장소에 커밋하므로 충돌 시 리베이스 후 재시도한다.
set -euo pipefail
MSG="${1:-update}"

git config user.name  "stock-brief"
git config user.email "actions@users.noreply.github.com"

git add docs state watchlist.json 2>/dev/null || true
if git diff --staged --quiet; then
  echo "변경사항 없음"
  exit 0
fi
git commit -m "$MSG $(date -u +%Y-%m-%dT%H:%MZ)"

for i in 1 2 3; do
  if git push; then
    exit 0
  fi
  echo "push 충돌, 재시도 $i"
  git pull --rebase --autostash
  sleep 3
done

echo "push 실패"
exit 1
