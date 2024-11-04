#!/bin/bash

# alias obsigo='/path to where you have the obsigo repo/obsigo/obsigo.sh'

script_path=$(dirname "$(realpath "$0")")
echo "The script is located at: $script_path"

# Display current working directory
echo "Current working directory: $(pwd)"

# Activate python venv
source $script_path/venv/bin/activate

# Run the python script
python $script_path/obsigo.py

# Deactivate python venv
deactivate

# check if any of the params is '-lhs'
if [[ "$@" == *"-lhs"* ]]; then
    echo
    echo "Starting local hugo server..."
    ./hugo server
fi
