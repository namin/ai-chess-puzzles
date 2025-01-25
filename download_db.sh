#!/bin/bash

# Set variables
DB_DIR="db"
DB_FILE="$DB_DIR/lichess_db_puzzle.csv"
ZST_FILE="$DB_DIR/lichess_db_puzzle.csv.zst"
URL="https://database.lichess.org/lichess_db_puzzle.csv.zst"

# Check if db directory exists
if [ ! -d "$DB_DIR" ]; then
    echo "Creating db directory..."
    mkdir -p "$DB_DIR"
    
    # Download the database file
    echo "Downloading database..."
    curl -o "$ZST_FILE" "$URL"

    # Decompress the file
    echo "Decompressing database..."
    zstd -d "$ZST_FILE" -o "$DB_FILE"

    # Create smaller versions
    echo "Creating smaller datasets..."
    head -n 50 "$DB_FILE" > "$DB_DIR/lichess_db_puzzle50.csv"
    head -n 500 "$DB_FILE" > "$DB_DIR/lichess_db_puzzle500.csv"

    echo "Download and extraction complete."
else
    echo "Database directory already exists. Skipping download."
fi