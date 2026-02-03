"""
LLM Core - Shared logic for ClarityMentor inference.
Extracted from inference.py for reuse in both text-only and voice pipelines.
"""

from pathlib import Path
from typing import List, Dict, Any
import torch


def load_claritymentor_model(model_path: Path, max_seq_length: int = 2048):
    """
    Load the fine-tuned ClarityMentor model.

    Args:
        model_path: Path to LoRA model directory
        max_seq_length: Maximum sequence length

    Returns:
        (model, tokenizer) tuple
    """
    try:
        from unsloth import FastLanguageModel

        print("Loading ClarityMentor with unsloth...")
        model, tokenizer = FastLanguageModel.from_pretrained(
            str(model_path),
            max_seq_length=max_seq_length,
            load_in_4bit=True,
        )
        FastLanguageModel.for_inference(model)

    except ImportError:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        print("Loading ClarityMentor with transformers...")
        tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            device_map="auto",
            load_in_4bit=True,
        )

    return model, tokenizer


def load_system_prompt(config_dir: Path) -> str:
    """
    Load the system prompt from config.

    Args:
        config_dir: Path to config directory

    Returns:
        System prompt string
    """
    prompt_file = config_dir / "system_prompt.txt"
    if prompt_file.exists():
        return prompt_file.read_text().strip()
    return "You are ClarityMentor, a thoughtful philosophical mentor."


def generate_response_core(
    model,
    tokenizer,
    messages: List[Dict[str, str]],
    max_new_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9,
) -> str:
    """
    Generate response from ClarityMentor.

    Args:
        model: Loaded model
        tokenizer: Loaded tokenizer
        messages: List of {"role": ..., "content": ...} dicts
        max_new_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        top_p: Nucleus sampling parameter

    Returns:
        Generated response text
    """
    # Add assistant starter to guide generation
    assistant_starter = "I understand. Here's my perspective:\n\n"

    inputs = tokenizer.apply_chat_template(
        messages,
        return_tensors="pt",
        add_generation_prompt=True,
    )

    # Append starter tokens
    starter_tokens = tokenizer.encode(
        assistant_starter, add_special_tokens=False, return_tensors="pt"
    )
    inputs = torch.cat([inputs, starter_tokens], dim=1).to(model.device)

    outputs = model.generate(
        inputs,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        do_sample=True,
        pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
    )

    # Decode only new tokens
    full_response = tokenizer.decode(
        outputs[0][inputs.shape[1] :], skip_special_tokens=True
    )
    response = assistant_starter + full_response

    # Clean up prompt fragments
    response = response.strip()
    for marker in [
        "Your turn!",
        "BEFORE RESPOND:",
        "FORMAT:",
        "Next step:",
        "4. CLOSING",
        "be specific",
    ]:
        if marker in response:
            response = response[: response.index(marker)].strip()
            break

    return response
