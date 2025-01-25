#!/bin/bash

# Set variables
DB_DIR="db"
DB_FILE="$DB_DIR/lichess_db_puzzle.csv"
ZST_FILE="$DB_DIR/lichess_db_puzzle.csv.zst"
URL="https://database.lichess.org/lichess_db_puzzle.csv.zst"

# Ensure the db directory exists
mkdir -p "$DB_DIR"

# Step 1: Download the file only if it's missing
if [ ! -f "$ZST_FILE" ]; then
    echo "Downloading database..."
    curl -o "$ZST_FILE" "$URL"
else
    echo "Database file already downloaded."
fi

# Step 2: Decompress only if the CSV is missing
if [ ! -f "$DB_FILE" ]; then
    echo "Decompressing database..."
    zstd -d "$ZST_FILE" -o "$DB_FILE"
else
    echo "Database already decompressed."
fi

# Step 3: Generate the smaller datasets only if they are missing
if [ ! -f "$DB_DIR/lichess_db_puzzle_50.csv" ]; then
    echo "Generating smaller dataset (50 puzzles)..."
    head -n 50 "$DB_FILE" > "$DB_DIR/lichess_db_puzzle_50.csv"
else
    echo "Smaller dataset (50 puzzles) already exists."
fi

if [ ! -f "$DB_DIR/lichess_db_puzzle_500.csv" ]; then
    echo "Generating smaller dataset (500 puzzles)..."
    head -n 500 "$DB_FILE" > "$DB_DIR/lichess_db_puzzle_500.csv"
else
    echo "Smaller dataset (500 puzzles) already exists."
fi

echo "All steps complete."