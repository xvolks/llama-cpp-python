#!/usr/bin/env bash

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
python -m llama_cpp.server --port 8888 --n_threads 8 --n_gpu_layers 40 --model $MODEL
