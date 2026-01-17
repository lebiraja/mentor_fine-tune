#!/bin/bash
# ClarityMentor Fine-Tuning Pipeline
# Run this script to process datasets and train the model

set -e  # Exit on error

PROJECT_DIR="/home/lebi/projects/mentor"
SCRIPTS_DIR="$PROJECT_DIR/scripts"

echo "=========================================="
echo "ClarityMentor Fine-Tuning Pipeline"
echo "=========================================="
echo ""

# Check for required packages
echo "Checking dependencies..."
python3 -c "import pyarrow" 2>/dev/null || { echo "Installing pyarrow..."; pip install pyarrow; }
python3 -c "import yaml" 2>/dev/null || { echo "Installing pyyaml..."; pip install pyyaml; }

echo ""
echo "Step 1: Converting Empathetic Dialogues LLM..."
python3 "$SCRIPTS_DIR/converters/convert_empathetic_llm.py"

echo ""
echo "Step 2: Converting Philosophy QA..."
python3 "$SCRIPTS_DIR/converters/convert_philosophy_qa.py"

echo ""
echo "Step 3: Converting Counseling datasets..."
python3 "$SCRIPTS_DIR/converters/convert_counseling.py"

echo ""
echo "Step 4: Converting Quotes to Advice..."
python3 "$SCRIPTS_DIR/converters/convert_quotes_to_advice.py"

echo ""
echo "Step 5: Converting Conversation Starters..."
python3 "$SCRIPTS_DIR/converters/convert_conversation_starters.py"

echo ""
echo "Step 6: Converting Reddit (if available)..."
# Check if Reddit data is pulled
if [ -f "$PROJECT_DIR/reddit_dataset_170/data/train-DataEntity_chunk_0.parquet" ]; then
    python3 "$SCRIPTS_DIR/converters/convert_reddit.py"
else
    echo "  Reddit data not available. Skipping..."
    echo "  To include Reddit data, run: cd reddit_dataset_170 && git lfs pull"
fi

echo ""
echo "Step 7: Merging datasets..."
python3 "$SCRIPTS_DIR/merge_datasets.py"

echo ""
echo "=========================================="
echo "Data processing complete!"
echo "=========================================="
echo ""
echo "Training data: $PROJECT_DIR/data/final/claritymentor_train.jsonl"
echo "Eval data: $PROJECT_DIR/data/final/claritymentor_eval.jsonl"
echo ""
echo "To start training, run:"
echo "  python3 $SCRIPTS_DIR/train_qlora.py"
echo ""
