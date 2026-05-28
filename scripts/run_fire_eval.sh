#!/usr/bin/env bash
set -euo pipefail

RUN_NAME="${RUN_NAME:?missing RUN_NAME}"
WEIGHT="${WEIGHT:?missing WEIGHT}"
EVAL_SET="${EVAL_SET:?missing EVAL_SET}"   # public or generalization

MODEL_TYPE="${MODEL_TYPE:-full_sft}"
TRAIN_DATA="${TRAIN_DATA:-fire_operator_dsl_sft_code.jsonl}"
FROM_WEIGHT="${FROM_WEIGHT:-none}"
HIDDEN_SIZE="${HIDDEN_SIZE:-128}"
NUM_LAYERS="${NUM_LAYERS:-2}"
MAX_SEQ_LEN="${MAX_SEQ_LEN:-512}"
BATCH_SIZE="${BATCH_SIZE:-2}"
LEARNING_RATE="${LEARNING_RATE:-3e-4}"
EPOCHS="${EPOCHS:-1}"
DEVICE="${DEVICE:-cuda}"
TEMPERATURE="${TEMPERATURE:-0.1}"
LORA_WEIGHT="${LORA_WEIGHT:-None}"
NOTES="${NOTES:-}"

if [[ "$EVAL_SET" == "public" ]]; then
  EVAL_JSONL="fire-dsl-data/eval/fire_operator_dsl_eval_code_public.jsonl"
elif [[ "$EVAL_SET" == "generalization" ]]; then
  EVAL_JSONL="fire-dsl-data/eval/fire_operator_dsl_eval_code_generalization.jsonl"
else
  echo "EVAL_SET must be public or generalization"
  exit 2
fi

mkdir -p logs results experiments

PRED_CSV="results/${RUN_NAME}_${EVAL_SET}_predictions.csv"
SCORE_LOG="logs/${RUN_NAME}_${EVAL_SET}_score.log"
INFER_LOG="logs/${RUN_NAME}_${EVAL_SET}_infer.log"
ERROR_CSV="results/${RUN_NAME}_${EVAL_SET}_errors.csv"
ERROR_LOG="logs/${RUN_NAME}_${EVAL_SET}_errors.log"

echo "=== Batch inference: $RUN_NAME / $EVAL_SET ==="
python scripts/batch_fire_infer.py \
  --eval_jsonl "$EVAL_JSONL" \
  --output_csv "$PRED_CSV" \
  --save_dir minimind/out \
  --weight "$WEIGHT" \
  --lora_weight "$LORA_WEIGHT" \
  --hidden_size "$HIDDEN_SIZE" \
  --num_hidden_layers "$NUM_LAYERS" \
  --device "$DEVICE" \
  --temperature "$TEMPERATURE" \
  2>&1 | tee "$INFER_LOG"

echo "=== Score: $RUN_NAME / $EVAL_SET ==="
python scripts/score_fire_predictions.py "$PRED_CSV" \
  2>&1 | tee "$SCORE_LOG"

echo "=== Error analysis: $RUN_NAME / $EVAL_SET ==="
python scripts/analyze_fire_errors.py "$PRED_CSV" "$ERROR_CSV" \
  2>&1 | tee "$ERROR_LOG"

echo "=== Append summary ==="
python scripts/append_score_summary.py \
  --score_log "$SCORE_LOG" \
  --prediction_csv "$PRED_CSV" \
  --run_name "$RUN_NAME" \
  --model_type "$MODEL_TYPE" \
  --train_data "$TRAIN_DATA" \
  --from_weight "$FROM_WEIGHT" \
  --hidden_size "$HIDDEN_SIZE" \
  --num_layers "$NUM_LAYERS" \
  --max_seq_len "$MAX_SEQ_LEN" \
  --batch_size "$BATCH_SIZE" \
  --learning_rate "$LEARNING_RATE" \
  --epochs "$EPOCHS" \
  --eval_set "$EVAL_SET" \
  --notes "$NOTES"

echo "Done."
echo "Prediction CSV: $PRED_CSV"
echo "Score log:      $SCORE_LOG"
echo "Error CSV:      $ERROR_CSV"
