#!/usr/bin/env bash
# 第16章（CDK 側）の合格判定。型チェックと synth の結果を検査する。
# アプリ側（fetch / tools のロジック）は `uv run pytest -q` で判定する。
set -uo pipefail

CHAPTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$CHAPTER_DIR"
FAILED=0

ok() { printf '  \033[32mOK\033[0m    %s\n' "$1"; }
ng() { printf '  \033[31mNG\033[0m    %s\n' "$1"; FAILED=1; }

echo "1. 前提"
if [ ! -d node_modules ]; then
  ng "依存が入っていません。16-news-kb-mcp で npm ci を実行してください"
  exit 1
fi
for f in knowledge-base-stack gateway-stack; do
  if [ ! -f "lib/$f.ts" ]; then
    ng "lib/$f.ts がありません。exercises/$f.ts をコピーして TODO を埋めてください（README 16.5.1）"
    exit 1
  fi
  if grep -q "TODO" "lib/$f.ts"; then
    ng "lib/$f.ts に TODO が残っています。README に沿って実装し、終わったら TODO コメントを消してください"
    exit 1
  fi
done
ok "lib/ の 2 ファイルがある"
if [ ! -f lambda_src/tools/tools_handler.py ]; then
  ng "lambda_src/tools/tools_handler.py がありません。pytest 合格後に exercises/tools_handler.py をコピーしてください（16.5.1）"
elif grep -q "TODO" lambda_src/tools/tools_handler.py; then
  ng "lambda_src/tools/tools_handler.py に TODO が残っています"
else
  ok "ツール Lambda にロジックが配置されている"
fi

echo "2. 型チェック"
if npx tsc --noEmit >/dev/null 2>&1; then
  ok "tsc --noEmit"
else
  ng "型エラーがあります。npx tsc --noEmit で確認してください"
fi

echo "3. synth"
CDK_DEFAULT_ACCOUNT=111111111111 npx cdk synth >/dev/null 2>&1 || true
SYNTH="$(cat cdk.out/*.template.json 2>/dev/null || true)"
echo "$SYNTH" | grep -q "AWS::S3Vectors::Index" && ok "S3 Vectors のインデックスがある" \
  || ng "CfnVectorBucket / CfnIndex を作ってください（16.5.1 knowledge-base-stack.ts の TODO(1)）"
echo "$SYNTH" | grep -q "S3_VECTORS" && ok "KB のストアが S3_VECTORS" \
  || ng "CfnKnowledgeBase の storageConfiguration を S3_VECTORS にしてください（16.5.1 knowledge-base-stack.ts の TODO(2)）"
echo "$SYNTH" | grep -q "FLOAT32" && ok "埋め込みの次元数を KB に明示している" \
  || ng "vectorKnowledgeBaseConfiguration に embeddingModelConfiguration を足してください（16.5.1 knowledge-base-stack.ts の TODO(2)）"
echo "$SYNTH" | grep -q "AWS::Bedrock::DataSource" && ok "データソースがある" \
  || ng "CfnDataSource を作ってください（16.5.1 knowledge-base-stack.ts の TODO(3)）"
echo "$SYNTH" | grep -q "AWS::BedrockAgentCore::Gateway" && ok "Gateway がある" \
  || ng "CfnGateway を作ってください（16.5.1 gateway-stack.ts の TODO(1)）"
echo "$SYNTH" | grep -q "CUSTOM_JWT" && ok "JWT インバウンド認可がある" \
  || ng "authorizerType CUSTOM_JWT と customJwtAuthorizer を設定してください（16.5.1 gateway-stack.ts の TODO(1)）"
echo "$SYNTH" | grep -q "search_aws_updates" && ok "ツール定義が公開されている" \
  || ng "CfnGatewayTarget の toolSchema に 2 ツールを定義してください（16.5.1 gateway-stack.ts の TODO(2)）"
echo "$SYNTH" | grep -q "AWS::Scheduler::Schedule" && ok "取り込みのスケジュールがある（完成品）" \
  || ng "ingestion-stack が synth されていません。bin/app.ts を変更していないか確認してください"

echo
if [ "$FAILED" = "0" ]; then
  printf '\033[32m第16章（CDK 側）合格。アプリ側は uv run pytest -q で判定してください。\033[0m\n'
else
  printf '\033[31m未達の項目があります。\033[0m\n'
fi
exit "$FAILED"
