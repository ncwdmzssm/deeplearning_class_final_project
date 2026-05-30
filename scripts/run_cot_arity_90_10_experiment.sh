#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

RUN_NAME="${RUN_NAME:-fire_dsl_domain_mixed_cot_arity_90_10}"
TRAIN_DATA="${TRAIN_DATA:-fire_operator_dsl_sft_mixed_cot_arity_90_10.jsonl}"
FROM_WEIGHT="${FROM_WEIGHT:-fire_dsl_domain_pretrain}"
HIDDEN_SIZE="${HIDDEN_SIZE:-128}"
NUM_LAYERS="${NUM_LAYERS:-2}"
MAX_SEQ_LEN="${MAX_SEQ_LEN:-512}"
BATCH_SIZE="${BATCH_SIZE:-2}"
LEARNING_RATE="${LEARNING_RATE:-3e-4}"
EPOCHS="${EPOCHS:-3}"
TRAIN_DEVICE="${TRAIN_DEVICE:-cuda:0}"
EVAL_DEVICE="${EVAL_DEVICE:-cuda}"
TEMPERATURE="${TEMPERATURE:-0.01}"
EVAL_SET="${EVAL_SET:-generalization}"
RUN_RERANK="${RUN_RERANK:-0}"
RERANK_TEMPERATURE="${RERANK_TEMPERATURE:-0.2}"
NUM_CANDIDATES="${NUM_CANDIDATES:-5}"

if [[ ! -f "$ROOT/minimind/trainer/train_full_sft.py" ]]; then
  echo "Missing minimind/trainer/train_full_sft.py under $ROOT"
  echo "Run this script on the server/workspace that contains the MiniMind checkout and out/ weights."
  exit 2
fi

if [[ "$EVAL_SET" == "generalization" ]]; then
  EVAL_JSONL="fire-dsl-data/eval/fire_operator_dsl_eval_code_generalization.jsonl"
else
  EVAL_JSONL="fire-dsl-data/eval/fire_operator_dsl_eval_code_public.jsonl"
fi

mkdir -p "$ROOT/logs" "$ROOT/results" "$ROOT/experiments"

cat > "$ROOT/experiments/${RUN_NAME}.env" <<EOF
RUN_NAME=$RUN_NAME
MODEL_TYPE=domain_pretrain_plus_sft
TRAIN_DATA=$TRAIN_DATA
FROM_WEIGHT=$FROM_WEIGHT
HIDDEN_SIZE=$HIDDEN_SIZE
NUM_LAYERS=$NUM_LAYERS
MAX_SEQ_LEN=$MAX_SEQ_LEN
BATCH_SIZE=$BATCH_SIZE
LEARNING_RATE=$LEARNING_RATE
EPOCHS=$EPOCHS
TRAIN_DEVICE=$TRAIN_DEVICE
EVAL_DEVICE=$EVAL_DEVICE
TEMPERATURE=$TEMPERATURE
EVAL_SET=$EVAL_SET
RUN_RERANK=$RUN_RERANK
EOF

echo "=== Train $RUN_NAME ==="
(
  cd "$ROOT/minimind/trainer"
  python train_full_sft.py \
    --data_path "../../fire-dsl-data/train/${TRAIN_DATA}" \
    --epochs "$EPOCHS" \
    --batch_size "$BATCH_SIZE" \
    --learning_rate "$LEARNING_RATE" \
    --num_workers 0 \
    --device "$TRAIN_DEVICE" \
    --dtype float16 \
    --hidden_size "$HIDDEN_SIZE" \
    --num_hidden_layers "$NUM_LAYERS" \
    --max_seq_len "$MAX_SEQ_LEN" \
    --from_weight "$FROM_WEIGHT" \
    --save_dir ../out \
    --save_weight "$RUN_NAME" \
    2>&1 | tee "$ROOT/logs/train_${RUN_NAME}.log"
)

RAW_CSV="results/${RUN_NAME}_${EVAL_SET}_raw_predictions.csv"
EXTRACT_CSV="results/${RUN_NAME}_${EVAL_SET}_extract_predictions.csv"
EXTRACT_SCORE="logs/${RUN_NAME}_${EVAL_SET}_extract_score.log"

echo "=== Raw inference: $EVAL_SET ==="
python "$ROOT/scripts/batch_fire_infer.py" \
  --eval_jsonl "$ROOT/$EVAL_JSONL" \
  --output_csv "$ROOT/$RAW_CSV" \
  --weight "$RUN_NAME" \
  --hidden_size "$HIDDEN_SIZE" \
  --num_hidden_layers "$NUM_LAYERS" \
  --temperature "$TEMPERATURE" \
  --device "$EVAL_DEVICE" \
  2>&1 | tee "$ROOT/logs/${RUN_NAME}_${EVAL_SET}_raw_infer.log"

echo "=== Extract first DSL block ==="
python "$ROOT/scripts/extract_first_dsl_block.py" \
  --input_csv "$ROOT/$RAW_CSV" \
  --output_csv "$ROOT/$EXTRACT_CSV"

echo "=== Score extract predictions ==="
python "$ROOT/scripts/score_fire_predictions.py" "$ROOT/$EXTRACT_CSV" \
  2>&1 | tee "$ROOT/$EXTRACT_SCORE"

if [[ "$RUN_RERANK" == "1" ]]; then
  RERANK_CSV="results/${RUN_NAME}_${EVAL_SET}_rerank${NUM_CANDIDATES}_t02_predictions.csv"
  RERANK_SCORE="logs/${RUN_NAME}_${EVAL_SET}_rerank${NUM_CANDIDATES}_t02_score.log"

  echo "=== Rerank inference: $EVAL_SET ==="
  python "$ROOT/scripts/batch_fire_rerank_infer.py" \
    --eval_jsonl "$ROOT/$EVAL_JSONL" \
    --output_csv "$ROOT/$RERANK_CSV" \
    --weight "$RUN_NAME" \
    --hidden_size "$HIDDEN_SIZE" \
    --num_hidden_layers "$NUM_LAYERS" \
    --temperature "$RERANK_TEMPERATURE" \
    --num_candidates "$NUM_CANDIDATES" \
    --device "$EVAL_DEVICE" \
    2>&1 | tee "$ROOT/logs/${RUN_NAME}_${EVAL_SET}_rerank${NUM_CANDIDATES}_t02_infer.log"

  echo "=== Score rerank predictions ==="
  python "$ROOT/scripts/score_fire_predictions.py" "$ROOT/$RERANK_CSV" \
    2>&1 | tee "$ROOT/$RERANK_SCORE"
fi

echo "=== Done ==="
echo "extract_csv=$ROOT/$EXTRACT_CSV"
echo "extract_score=$ROOT/$EXTRACT_SCORE"
