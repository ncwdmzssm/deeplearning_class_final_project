#!/usr/bin/env bash
set -euo pipefail

RUN_NAME="${RUN_NAME:?missing RUN_NAME}"
MODE="${MODE:?missing MODE}"   # baseline_sft or domain_pretrain_sft
HIDDEN_SIZE="${HIDDEN_SIZE:-128}"
NUM_LAYERS="${NUM_LAYERS:-2}"
MAX_SEQ_LEN="${MAX_SEQ_LEN:-512}"
BATCH_SIZE="${BATCH_SIZE:-2}"
PRETRAIN_BATCH_SIZE="${PRETRAIN_BATCH_SIZE:-4}"
LR="${LR:-3e-4}"
PRETRAIN_LR="${PRETRAIN_LR:-5e-4}"
EPOCHS="${EPOCHS:-3}"
PRETRAIN_EPOCHS="${PRETRAIN_EPOCHS:-2}"
DEVICE="${DEVICE:-cuda:0}"
EVAL_DEVICE="${EVAL_DEVICE:-cuda}"
TEMPERATURE="${TEMPERATURE:-0.01}"

mkdir -p logs results experiments

echo "RUN_NAME=$RUN_NAME" > "experiments/${RUN_NAME}.env"
echo "MODE=$MODE" >> "experiments/${RUN_NAME}.env"
echo "HIDDEN_SIZE=$HIDDEN_SIZE" >> "experiments/${RUN_NAME}.env"
echo "NUM_LAYERS=$NUM_LAYERS" >> "experiments/${RUN_NAME}.env"
echo "MAX_SEQ_LEN=$MAX_SEQ_LEN" >> "experiments/${RUN_NAME}.env"
echo "BATCH_SIZE=$BATCH_SIZE" >> "experiments/${RUN_NAME}.env"
echo "LR=$LR" >> "experiments/${RUN_NAME}.env"
echo "EPOCHS=$EPOCHS" >> "experiments/${RUN_NAME}.env"
echo "TEMPERATURE=$TEMPERATURE" >> "experiments/${RUN_NAME}.env"

if [[ "$MODE" == "baseline_sft" ]]; then
  echo "=== Training baseline SFT: $RUN_NAME ==="
  (
    cd minimind/trainer
    python train_full_sft.py \
      --data_path ../../fire-dsl-data/train/fire_operator_dsl_sft_code.jsonl \
      --epochs "$EPOCHS" \
      --batch_size "$BATCH_SIZE" \
      --learning_rate "$LR" \
      --num_workers 0 \
      --device "$DEVICE" \
      --dtype float16 \
      --hidden_size "$HIDDEN_SIZE" \
      --num_hidden_layers "$NUM_LAYERS" \
      --max_seq_len "$MAX_SEQ_LEN" \
      --from_weight none \
      --save_dir ../out \
      --save_weight "$RUN_NAME" \
      2>&1 | tee "../../logs/train_${RUN_NAME}.log"
  )

  FROM_WEIGHT="none"
  MODEL_TYPE="full_sft"

elif [[ "$MODE" == "domain_pretrain_sft" ]]; then
  PRETRAIN_NAME="${RUN_NAME}_pretrain"

  echo "=== Domain pretrain: $PRETRAIN_NAME ==="
  (
    cd minimind/trainer
    python train_pretrain.py \
      --data_path ../../fire-dsl-data/train/fire_operator_dsl_pretrain_domain.jsonl \
      --epochs "$PRETRAIN_EPOCHS" \
      --batch_size "$PRETRAIN_BATCH_SIZE" \
      --learning_rate "$PRETRAIN_LR" \
      --num_workers 0 \
      --device "$DEVICE" \
      --dtype float16 \
      --hidden_size "$HIDDEN_SIZE" \
      --num_hidden_layers "$NUM_LAYERS" \
      --max_seq_len "$MAX_SEQ_LEN" \
      --from_weight none \
      --save_dir ../out \
      --save_weight "$PRETRAIN_NAME" \
      2>&1 | tee "../../logs/train_${PRETRAIN_NAME}.log"
  )

  echo "=== SFT from domain pretrain: $RUN_NAME ==="
  (
    cd minimind/trainer
    python train_full_sft.py \
      --data_path ../../fire-dsl-data/train/fire_operator_dsl_sft_code.jsonl \
      --epochs "$EPOCHS" \
      --batch_size "$BATCH_SIZE" \
      --learning_rate "$LR" \
      --num_workers 0 \
      --device "$DEVICE" \
      --dtype float16 \
      --hidden_size "$HIDDEN_SIZE" \
      --num_hidden_layers "$NUM_LAYERS" \
      --max_seq_len "$MAX_SEQ_LEN" \
      --from_weight "$PRETRAIN_NAME" \
      --save_dir ../out \
      --save_weight "$RUN_NAME" \
      2>&1 | tee "../../logs/train_${RUN_NAME}.log"
  )

  FROM_WEIGHT="$PRETRAIN_NAME"
  MODEL_TYPE="domain_pretrain_plus_sft"

else
  echo "Unknown MODE: $MODE"
  exit 2
fi

echo "=== Eval public ==="
RUN_NAME="$RUN_NAME" \
WEIGHT="$RUN_NAME" \
MODEL_TYPE="$MODEL_TYPE" \
TRAIN_DATA="fire_operator_dsl_sft_code.jsonl" \
FROM_WEIGHT="$FROM_WEIGHT" \
HIDDEN_SIZE="$HIDDEN_SIZE" \
NUM_LAYERS="$NUM_LAYERS" \
MAX_SEQ_LEN="$MAX_SEQ_LEN" \
BATCH_SIZE="$BATCH_SIZE" \
LEARNING_RATE="$LR" \
EPOCHS="$EPOCHS" \
DEVICE="$EVAL_DEVICE" \
TEMPERATURE="$TEMPERATURE" \
EVAL_SET=public \
NOTES="$MODE auto pipeline" \
bash scripts/run_fire_eval.sh

echo "=== Eval generalization ==="
RUN_NAME="$RUN_NAME" \
WEIGHT="$RUN_NAME" \
MODEL_TYPE="$MODEL_TYPE" \
TRAIN_DATA="fire_operator_dsl_sft_code.jsonl" \
FROM_WEIGHT="$FROM_WEIGHT" \
HIDDEN_SIZE="$HIDDEN_SIZE" \
NUM_LAYERS="$NUM_LAYERS" \
MAX_SEQ_LEN="$MAX_SEQ_LEN" \
BATCH_SIZE="$BATCH_SIZE" \
LEARNING_RATE="$LR" \
EPOCHS="$EPOCHS" \
DEVICE="$EVAL_DEVICE" \
TEMPERATURE="$TEMPERATURE" \
EVAL_SET=generalization \
NOTES="$MODE auto pipeline" \
bash scripts/run_fire_eval.sh

echo "=== Done: $RUN_NAME ==="
tail -n 5 results/summary_table.csv
