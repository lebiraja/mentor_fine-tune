"""
QLoRA training script for ClarityMentor.

Uses unsloth for efficient training on RTX 4050 (6GB VRAM).
Falls back to transformers + peft if unsloth is not available.

Usage:
    python train_qlora.py
    python train_qlora.py --config config/training_config.yaml
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import yaml


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load training configuration from YAML file."""
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


def load_system_prompt(config_dir: Path) -> str:
    """Load the system prompt."""
    prompt_file = config_dir / "system_prompt.txt"
    if prompt_file.exists():
        return prompt_file.read_text().strip()
    return "You are ClarityMentor, a thoughtful philosophical mentor."


def format_messages_to_text(messages: list, tokenizer) -> str:
    """
    Format messages list to text using the tokenizer's chat template.
    """
    try:
        # Use the tokenizer's built-in chat template
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False
        )
    except Exception:
        # Fallback: manual formatting
        text_parts = []
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            if role == 'system':
                text_parts.append(f"<|im_start|>system\n{content}<|im_end|>")
            elif role == 'user':
                text_parts.append(f"<|im_start|>user\n{content}<|im_end|>")
            elif role == 'assistant':
                text_parts.append(f"<|im_start|>assistant\n{content}<|im_end|>")
        return "\n".join(text_parts)


def train_with_unsloth(
    train_file: Path,
    eval_file: Path,
    config: Dict[str, Any],
    output_dir: Path,
):
    """Train using unsloth (faster, recommended)."""
    from unsloth import FastLanguageModel
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from datasets import load_dataset
    import torch

    print("Training with unsloth...")

    # Extract config values
    model_config = config.get('model', {})
    lora_config = config.get('lora', {})
    training_config = config.get('training', {})

    base_model = model_config.get('base_model', 'Qwen/Qwen2.5-1.5B-Instruct')
    max_seq_length = training_config.get('max_seq_length', 1024)

    print(f"Loading base model: {base_model}")

    # Load model in 4-bit
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=max_seq_length,
        dtype=None,  # Auto-detect
        load_in_4bit=True,
    )

    print("Adding LoRA adapters...")

    # Add LoRA adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_config.get('r', 16),
        target_modules=lora_config.get('target_modules', [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ]),
        lora_alpha=lora_config.get('lora_alpha', 32),
        lora_dropout=lora_config.get('lora_dropout', 0.05),
        bias="none",
        use_gradient_checkpointing="unsloth",  # Optimized
        random_state=42,
    )

    print("Loading dataset...")

    # Load datasets separately to avoid schema mismatch
    train_dataset = load_dataset("json", data_files=str(train_file), split="train")
    eval_dataset = load_dataset("json", data_files=str(eval_file), split="train")

    # Remove metadata column if present (not needed for training)
    if "metadata" in train_dataset.column_names:
        train_dataset = train_dataset.remove_columns(["metadata"])
    if "metadata" in eval_dataset.column_names:
        eval_dataset = eval_dataset.remove_columns(["metadata"])

    # Ensure tokenizer has proper settings for truncation
    tokenizer.truncation_side = "right"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Format dataset with pre-truncation to avoid unsloth errors
    def format_sample(example):
        messages = example.get('messages', [])
        text = format_messages_to_text(messages, tokenizer)
        # Pre-tokenize and truncate to max_seq_length
        tokens = tokenizer(text, truncation=True, max_length=max_seq_length, return_tensors=None)
        # Decode back to get truncated text
        truncated_text = tokenizer.decode(tokens['input_ids'], skip_special_tokens=False)
        return {"text": truncated_text}

    formatted_train = train_dataset.map(format_sample, remove_columns=train_dataset.column_names)
    formatted_eval = eval_dataset.map(format_sample, remove_columns=eval_dataset.column_names)

    print(f"Training samples: {len(formatted_train)}")
    print(f"Eval samples: {len(formatted_eval)}")

    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=training_config.get('per_device_train_batch_size', 1),
        gradient_accumulation_steps=training_config.get('gradient_accumulation_steps', 16),
        warmup_ratio=training_config.get('warmup_ratio', 0.03),
        num_train_epochs=training_config.get('num_train_epochs', 2),
        learning_rate=training_config.get('learning_rate', 2e-4),
        fp16=training_config.get('fp16', False),
        bf16=training_config.get('bf16', True),
        logging_steps=training_config.get('logging_steps', 10),
        optim=training_config.get('optim', 'paged_adamw_8bit'),
        weight_decay=training_config.get('weight_decay', 0.01),
        lr_scheduler_type=training_config.get('lr_scheduler_type', 'cosine'),
        save_strategy="steps",
        save_steps=training_config.get('save_steps', 500),
        save_total_limit=training_config.get('save_total_limit', 3),
        eval_strategy="steps",
        eval_steps=training_config.get('eval_steps', 500),
        logging_dir=str(output_dir / "logs"),
        report_to="none",  # Disable wandb by default
    )

    # Create trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=formatted_train,
        eval_dataset=formatted_eval,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        packing=False,  # Disable packing to allow proper truncation
        args=training_args,
    )

    print("\nStarting training...")
    print(f"  Epochs: {training_args.num_train_epochs}")
    print(f"  Batch size: {training_args.per_device_train_batch_size}")
    print(f"  Gradient accumulation: {training_args.gradient_accumulation_steps}")
    print(f"  Effective batch size: {training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps}")
    print(f"  Learning rate: {training_args.learning_rate}")
    print()

    # Train
    trainer.train()

    # Save final model
    print("\nSaving final model...")
    model.save_pretrained(output_dir / "final")
    tokenizer.save_pretrained(output_dir / "final")

    print(f"\nTraining complete! Model saved to {output_dir / 'final'}")

    return model, tokenizer


def train_with_transformers(
    train_file: Path,
    eval_file: Path,
    config: Dict[str, Any],
    output_dir: Path,
):
    """Train using transformers + peft (fallback)."""
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer
    from datasets import load_dataset
    import torch

    print("Training with transformers + peft...")

    # Extract config values
    model_config = config.get('model', {})
    lora_config = config.get('lora', {})
    training_config = config.get('training', {})

    base_model = model_config.get('base_model', 'Qwen/Qwen2.5-1.5B-Instruct')
    max_seq_length = training_config.get('max_seq_length', 1024)

    print(f"Loading base model: {base_model}")

    # BitsAndBytes config for 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Prepare model for k-bit training
    model = prepare_model_for_kbit_training(model)

    # LoRA config
    peft_config = LoraConfig(
        r=lora_config.get('r', 16),
        lora_alpha=lora_config.get('lora_alpha', 32),
        target_modules=lora_config.get('target_modules', [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ]),
        lora_dropout=lora_config.get('lora_dropout', 0.05),
        bias="none",
        task_type="CAUSAL_LM",
    )

    # Add LoRA adapters
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    print("Loading dataset...")

    # Load datasets separately to avoid schema mismatch
    train_dataset = load_dataset("json", data_files=str(train_file), split="train")
    eval_dataset = load_dataset("json", data_files=str(eval_file), split="train")

    # Remove metadata column if present (not needed for training)
    if "metadata" in train_dataset.column_names:
        train_dataset = train_dataset.remove_columns(["metadata"])
    if "metadata" in eval_dataset.column_names:
        eval_dataset = eval_dataset.remove_columns(["metadata"])

    # Ensure tokenizer has proper settings for truncation
    tokenizer.truncation_side = "right"

    # Format dataset with pre-truncation
    def format_sample(example):
        messages = example.get('messages', [])
        text = format_messages_to_text(messages, tokenizer)
        # Pre-tokenize and truncate to max_seq_length
        tokens = tokenizer(text, truncation=True, max_length=max_seq_length, return_tensors=None)
        # Decode back to get truncated text
        truncated_text = tokenizer.decode(tokens['input_ids'], skip_special_tokens=False)
        return {"text": truncated_text}

    formatted_train = train_dataset.map(format_sample, remove_columns=train_dataset.column_names)
    formatted_eval = eval_dataset.map(format_sample, remove_columns=eval_dataset.column_names)

    print(f"Training samples: {len(formatted_train)}")
    print(f"Eval samples: {len(formatted_eval)}")

    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=training_config.get('per_device_train_batch_size', 1),
        gradient_accumulation_steps=training_config.get('gradient_accumulation_steps', 16),
        warmup_ratio=training_config.get('warmup_ratio', 0.03),
        num_train_epochs=training_config.get('num_train_epochs', 2),
        learning_rate=training_config.get('learning_rate', 2e-4),
        fp16=training_config.get('fp16', False),
        bf16=training_config.get('bf16', True),
        logging_steps=training_config.get('logging_steps', 10),
        optim=training_config.get('optim', 'paged_adamw_8bit'),
        weight_decay=training_config.get('weight_decay', 0.01),
        lr_scheduler_type=training_config.get('lr_scheduler_type', 'cosine'),
        save_strategy="steps",
        save_steps=training_config.get('save_steps', 500),
        save_total_limit=training_config.get('save_total_limit', 3),
        eval_strategy="steps",
        eval_steps=training_config.get('eval_steps', 500),
        gradient_checkpointing=True,
        logging_dir=str(output_dir / "logs"),
        report_to="none",
    )

    # Create trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=formatted_train,
        eval_dataset=formatted_eval,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        packing=False,  # Disable packing to allow proper truncation
        args=training_args,
    )

    print("\nStarting training...")

    # Train
    trainer.train()

    # Save final model
    print("\nSaving final model...")
    model.save_pretrained(output_dir / "final")
    tokenizer.save_pretrained(output_dir / "final")

    print(f"\nTraining complete! Model saved to {output_dir / 'final'}")

    return model, tokenizer


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Train ClarityMentor using QLoRA"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("/home/lebi/projects/mentor/config/training_config.yaml"),
        help="Path to training config YAML"
    )
    parser.add_argument(
        "--train-file",
        type=Path,
        default=Path("/home/lebi/projects/mentor/data/final/claritymentor_train_v2.jsonl"),
        help="Path to training data"
    )
    parser.add_argument(
        "--eval-file",
        type=Path,
        default=Path("/home/lebi/projects/mentor/data/final/claritymentor_eval_v2.jsonl"),
        help="Path to evaluation data"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/home/lebi/projects/mentor/models/claritymentor-lora"),
        help="Output directory for model"
    )
    parser.add_argument(
        "--use-transformers",
        action="store_true",
        help="Use transformers + peft instead of unsloth"
    )

    args = parser.parse_args()

    # Load config
    config = load_config(args.config)
    print(f"Loaded config from {args.config}")

    # Validate files exist
    if not args.train_file.exists():
        print(f"Error: Training file not found: {args.train_file}")
        print("Please run the converter scripts and merge_datasets.py first.")
        sys.exit(1)

    if not args.eval_file.exists():
        print(f"Error: Eval file not found: {args.eval_file}")
        sys.exit(1)

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Choose training backend
    if args.use_transformers:
        train_with_transformers(args.train_file, args.eval_file, config, args.output_dir)
    else:
        try:
            train_with_unsloth(args.train_file, args.eval_file, config, args.output_dir)
        except ImportError:
            print("unsloth not found, falling back to transformers + peft")
            train_with_transformers(args.train_file, args.eval_file, config, args.output_dir)


if __name__ == "__main__":
    main()
