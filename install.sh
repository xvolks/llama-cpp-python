#!/usr/bin/env bash

if [[ -d venv ]]; then
  echo "venv directory found, let's roll!"
else
  PY_VER=3.11
  PYTHON=python$PY_VER
  $PYTHON --version || brew install python@$PY_VER
  $PYTHON -m venv venv || exit 3
  . ./venv/bin/activate
  pip install itsdangerous dataclasses dataclasses-json
fi
deactivate || echo "No previous venv was active"
. ./venv/bin/activate
VENV=$(python -c "import sys; print(sys.prefix)")
if [[ -d $VENV ]]; then
  echo "$VENV is now the current python venv"
else
  echo "Failed to activate the venv, please manually check it."
  exit 2
fi

pushd vendor/llama.cpp || exit 2
mkdir build
pushd build || exit 3
echo "Building native llama.cpp"
export CMAKE_ARGS="-DLLAMA_METAL=on" 
cmake -DLLAMA_METAL=ON -DCMAKE_OSX_ARCHITECTURES="arm64" -DBUILD_SHARED_LIBS=ON ..
CMAKE_BUILD_PARALLEL_LEVEL=10 cmake --build . --config Release -- -j 10
popd
popd
FORCE_CMAKE=1 pip install --force-reinstall --upgrade --no-cache-dir -e '.' --no-cache-dir && pip install --force-reinstall --upgrade --no-cache-dir -e '.[server]'


# This file : ggml-metal.metal is mandatory to be in the same directory than the executable.
# ???
