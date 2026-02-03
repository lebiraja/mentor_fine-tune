"""
Inference script for ClarityMentor.

Usage:
    python scripts/inference.py
    python scripts/inference.py --prompt "I feel lost in life"
    python scripts/inference.py --interactive
"""

import argparse
from pathlib import Path
import torch


def load_model(model_path: Path, max_seq_length: int = 2048):
    """Load the fine-tuned model."""
    try:
        from unsloth import FastLanguageModel
        print("Loading model with unsloth...")
        model, tokenizer = FastLanguageModel.from_pretrained(
            str(model_path),
            max_seq_length=max_seq_length,
            load_in_4bit=True,
        )
        FastLanguageModel.for_inference(model)
    except ImportError:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        print("Loading model with transformers...")
        tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            device_map="auto",
            load_in_4bit=True,
        )

    return model, tokenizer


def load_system_prompt(config_dir: Path) -> str:
    """Load the system prompt."""
    prompt_file = config_dir / "system_prompt.txt"
    if prompt_file.exists():
        return prompt_file.read_text().strip()
    return "You are ClarityMentor, a thoughtful philosophical mentor."


def generate_response(
    model,
    tokenizer,
    user_message: str,
    system_prompt: str,
    max_new_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9,
) -> str:
    """Generate a response from the model."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    # Add a starter to steer away from questions
    assistant_starter = "I understand. Here's my perspective:\n\n"

    inputs = tokenizer.apply_chat_template(
        messages,
        return_tensors="pt",
        add_generation_prompt=True,
    )

    # Append the assistant starter to guide generation
    starter_tokens = tokenizer.encode(assistant_starter, add_special_tokens=False, return_tensors="pt")
    inputs = torch.cat([inputs, starter_tokens], dim=1).to(model.device)

    outputs = model.generate(
        inputs,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        do_sample=True,
        pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
    )

    # Decode only the new tokens (excluding the starter we added)
    full_response = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
    response = assistant_starter + full_response

    # Clean up any unwanted fragments from the prompt
    response = response.strip()
    # Stop at common prompt markers if they appear
    for marker in ["Your turn!", "BEFORE RESPOND:", "FORMAT:", "Next step:", "4. CLOSING", "be specific"]:
        if marker in response:
            response = response[:response.index(marker)].strip()
            break

    return response


def interactive_mode(model, tokenizer, system_prompt: str):
    """Run interactive chat mode with conversation history."""
    print("\n" + "="*60)
    print("ClarityMentor Interactive Mode")
    print("="*60)
    print("Type your message and press Enter. Type 'quit' to exit.\n")

    conversation_history = []

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            # Add user message to history
            conversation_history.append({"role": "user", "content": user_input})

            # Build messages with full history
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)

            # Add a starter to steer generation
            assistant_starter = "I understand. Here's my perspective:\n\n"

            inputs = tokenizer.apply_chat_template(
                messages,
                return_tensors="pt",
                add_generation_prompt=True,
            )

            # Append the assistant starter to guide generation
            starter_tokens = tokenizer.encode(assistant_starter, add_special_tokens=False, return_tensors="pt")
            inputs = torch.cat([inputs, starter_tokens], dim=1).to(model.device)

            outputs = model.generate(
                inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            )

            # Decode only the new tokens
            full_response = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
            response = assistant_starter + full_response

            # Clean up prompt fragments
            response = response.strip()
            for marker in ["Your turn!", "BEFORE RESPOND:", "FORMAT:", "Next step:", "4. CLOSING", "be specific"]:
                if marker in response:
                    response = response[:response.index(marker)].strip()
                    break

            print("\nClarityMentor: ", end="", flush=True)
            print(response)

            # Add assistant response to history
            conversation_history.append({"role": "assistant", "content": response})

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break


def main():
    parser = argparse.ArgumentParser(description="ClarityMentor Inference")
    parser.add_argument(
        "--model-path",
        type=Path,
        default=Path("/home/lebi/projects/mentor/models/claritymentor-lora/final"),
        help="Path to the fine-tuned model",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("/home/lebi/projects/mentor/config"),
        help="Path to config directory",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Single prompt to generate response for",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Maximum tokens to generate",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (0.0-1.0)",
    )

    args = parser.parse_args()

    # Load model and system prompt
    print(f"Loading model from {args.model_path}...")
    model, tokenizer = load_model(args.model_path)
    system_prompt = load_system_prompt(args.config_dir)
    print("Model loaded!\n")

    if args.interactive:
        interactive_mode(model, tokenizer, system_prompt)
    elif args.prompt:
        print(f"You: {args.prompt}\n")
        print("ClarityMentor:", end=" ")
        response = generate_response(
            model, tokenizer, args.prompt, system_prompt,
            max_new_tokens=args.max_tokens,
            temperature=args.temperature,
        )
        print(response)
    else:
        # Default test prompts
        test_prompts = [
            "I feel stuck in my career and don't know what to do next.",
            "What's the point of life if we all die anyway?",
            "My friend betrayed my trust. Should I forgive them?",
        ]

        print("Running test prompts...\n")
        print("="*60)

        for prompt in test_prompts:
            print(f"\nYou: {prompt}\n")
            response = generate_response(model, tokenizer, prompt, system_prompt)
            print(f"ClarityMentor: {response}")
            print("\n" + "-"*60)


if __name__ == "__main__":
    main()
