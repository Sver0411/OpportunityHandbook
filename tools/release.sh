#!/bin/bash
# 用法：oh_finish.sh /tmp/msg.txt
# 流程：重建导航 → 严格构建（含内部链接）→ 内容测试 → 发布校验（快速）
#       全部通过才提交并推送；任一失败则打印失败项并停在原处。
set -o pipefail
cd /Users/mac/WorkBuddy/OpportunityHandbook || exit 1
MSG="$1"

echo "== 资源版本 =="
python3 tools/stamp_assets.py

echo "== 重建导航 =="
python3 tools/build_navigation.py >/dev/null 2>&1 || { echo "导航生成失败"; exit 1; }

echo "== 严格构建（含链接校验）=="
if ! python3 tools/build.py --strict > /tmp/oh_build.log 2>&1; then
  grep -E "^\s+[x!]" /tmp/oh_build.log | head -10
  echo "构建失败 → 停止"
  exit 1
fi

echo "== 路线图 =="
python3 tools/build_roadmap.py >/dev/null 2>&1

echo "== 内容测试 =="
if ! python3 tools/run_tests.py > /tmp/oh_tests.log 2>&1; then
  tail -20 /tmp/oh_tests.log
  echo "测试失败 → 停止"
  exit 1
fi

echo "== 发布校验（快速）=="
if ! python3 tools/validate_release.py --quick > /tmp/oh_validate.log 2>&1; then
  tail -20 /tmp/oh_validate.log
  echo "发布校验失败 → 停止"
  exit 1
fi
tail -2 /tmp/oh_validate.log

echo "== 提交与推送 =="
git add -A || exit 1
git commit -F "$MSG" -q || { echo "没有改动或提交失败"; exit 1; }
export HTTPS_PROXY=http://127.0.0.1:7897 HTTP_PROXY=http://127.0.0.1:7897 \
       https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897 GIT_TERMINAL_PROMPT=0
# 本机走 Clash 代理，偶发 SSL_ERROR_SYSCALL（网络抖动）→ 最多重试 5 次
for i in 1 2 3 4 5; do
  if git push origin main > /tmp/oh_push.log 2>&1; then
    echo "push ok (try $i)"
    break
  fi
  echo "push try $i failed: $(tail -1 /tmp/oh_push.log)"
  sleep 5
done
git log --oneline -1
git status -sb | head -1
