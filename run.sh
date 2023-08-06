#!/usr/bin/env bash

MESSAGE_DIRECTORY=~/chat_messages
if [[ $MESSAGE_DIRECTORY == "" ]]; then
  echo The messages will not be stored
else
  mkdir -p $MESSAGE_DIRECTORY || exit 2
  STORAGE_OPTION=--storage
fi

if [[ -d venv ]]; then
  echo "venv directory found, let's roll!"
else
  python3.10 -m venv venv
fi
deactivate 2>/dev/null || echo "No previous venv was active"
. ./venv/bin/activate
VENV=$(python -c "import sys; print(sys.prefix)")
if [[ -d $VENV ]]; then
  echo "$VENV is now the current python venv"
else
  echo "Failed to activate the venv, please manually check it."
  exit 2
fi
if [[ -f $1 ]]; then
  MODEL=$1
else
  MODEL=../model/vicuna-33B-GGML/vicuna-33b.ggmlv3.q4_0.bin
fi
echo Loading model $MODEL
export LLAMA_CPP_LIB=$(find . -name '*llama*' | grep dylib | head -n 1)
echo "Will load $LLAMA_CPP_LIB"
# python -m llama_cpp.server --port 8888 --model $MODEL --n_gpu_layers 32 --n_threads 8
export GGML_METAL_PATH=$(find . -name 'ggml-metal.metal' | head -n 1)
echo "Will set $GGML_METAL_PATH for ggml-metal.metal file path"

# This value works with my MBP 32GB RAM and nothing else running
MAX_TOKENS=2048
python -m llama_cpp.server --port 8888 --n_threads 8 --n_gpu_layers 40 --n_ctx $MAX_TOKENS --model $MODEL --cache_type disk --cache true $STORAGE_OPTION $MESSAGE_DIRECTORY
