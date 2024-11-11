#!/bin/bash

# alias obsigo='/path to where you have the obsigo repo/obsigo/obsigo.sh'

script_path=$(dirname "$(realpath "$0")")
echo "The script is located at: $script_path"

# Display current working directory
echo "Current working directory: $(pwd)"

# Activate python venv
source $script_path/venv/bin/activate

# Run the python script and pass any arguments
python $script_path/obsigo.py "$@"

# Store the exit code
exit_code=$?

# Check if python script failed
if [ $exit_code -ne 0 ]; then
    echo "Error: obsigo.py failed with exit code $exit_code"
    deactivate  # Make sure to deactivate venv before exiting
    exit $exit_code
fi

# Deactivate python venv
deactivate

# check if any of the params is '-i' for imagego:
if [[ "$@" == *"-i"* ]]; then
    echo
    OBSIGO_DEST=$(cat ./obsigo_dest.txt)
    echo "Running imagego on $OBSIGO_DEST"
    $script_path/imagego.sh "$OBSIGO_DEST"
fi

# check if any of the params is '-lhs'
if [[ "$@" == *"-lhs"* ]]; then
    echo
    echo "Starting local hugo server..."
    ./hugo server
fi
