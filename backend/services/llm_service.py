"""LLM service for ClarityMentor inference."""

import asyncio
from typing import Dict, Any, List, Optional
from backend.core.exceptions import LLMError


class LLMService:
    """Service for LLM inference with emotion-aware responses."""

    def __init__(self, model_service, emotion_prompts: Dict[str, Any]):
        """Initialize LLM service.

        Args:
            model_service: ModelService instance
            emotion_prompts: Emotion prompt configurations from config
        """
        self.model_service = model_service
        self.emotion_prompts = emotion_prompts
        self._model = None
        self._tokenizer = None
        self._system_prompt = None
        self._prompt_augmenter = None

    @property
    def model(self):
        """Lazily get the LLM model."""
        if self._model is None:
            self._model = self.model_service.get_model("llm")
        return self._model

    @property
    def tokenizer(self):
        """Lazily get the tokenizer."""
        if self._tokenizer is None:
            self._tokenizer = self.model_service.get_model("tokenizer")
        return self._tokenizer

    @property
    def system_prompt(self):
        """Lazily get the system prompt."""
        if self._system_prompt is None:
            self._system_prompt = self.model_service.get_model("system_prompt")
        return self._system_prompt

    async def generate_response(
        self, messages: List[Dict[str, str]], emotion: Dict[str, Any]
    ) -> str:
        """Generate emotion-aware response from LLM.

        Args:
            messages: Conversation history
            emotion: Detected emotion with confidence

        Returns:
            Generated response text

        Raises:
            LLMError: If generation fails
        """
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, self._generate_response_blocking, messages, emotion
            )
            return response

        except Exception as e:
            raise LLMError(f"LLM generation failed: {e}")

    def _generate_response_blocking(
        self, messages: List[Dict[str, str]], emotion: Dict[str, Any]
    ) -> str:
        """Blocking LLM generation (runs in executor).

        Args:
            messages: Conversation history
            emotion: Detected emotion

        Returns:
            Generated response
        """
        try:
            # Augment system prompt based on emotion
            augmented_prompt = self._augment_system_prompt(emotion)

            # Prepare messages with augmented system prompt
            augmented_messages = [
                {"role": "system", "content": augmented_prompt}
            ]
            augmented_messages.extend(messages)

            # Generate response using existing LLM core logic
            response = self._generate_with_model(augmented_messages)

            return response

        except Exception as e:
            raise LLMError(f"LLM generation failed: {e}")

    def _augment_system_prompt(self, emotion: Dict[str, Any]) -> str:
        """Augment system prompt based on detected emotion.

        Args:
            emotion: Emotion dict with 'primary_emotion' and 'confidence'

        Returns:
            Augmented system prompt
        """
        primary_emotion = emotion.get("primary_emotion", "neutral")
        confidence = emotion.get("confidence", 0.0)

        # Get emotion-specific prompt addition if confidence is high enough
        threshold = self.emotion_prompts.get("thresholds", {}).get("high_confidence", 0.7)

        if confidence >= threshold and primary_emotion in self.emotion_prompts.get(
            "emotions", {}
        ):
            emotion_config = self.emotion_prompts["emotions"][primary_emotion]
            prompt_addition = emotion_config.get("prompt_addition", "")

            return f"{self.system_prompt}\n\n{prompt_addition}"

        return self.system_prompt

    def _generate_with_model(self, messages: List[Dict[str, str]]) -> str:
        """Generate response using the model.

        Args:
            messages: Messages to send to model

        Returns:
            Generated text
        """
        try:
            # Try to use existing generate function from llm_core
            try:
                from scripts.llm_core import generate_response_core

                response = generate_response_core(self.model, self.tokenizer, messages)
            except ImportError:
                # Fallback: Use model directly
                from transformers import TextGenerationPipeline

                pipeline = TextGenerationPipeline(
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=0 if self.model.device.type == "cuda" else -1,
                )

                # Format messages as single prompt
                prompt = self._format_messages_as_prompt(messages)
                outputs = pipeline(
                    prompt,
                    max_new_tokens=512,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                )
                response = outputs[0]["generated_text"]

            return response

        except Exception as e:
            raise LLMError(f"Model generation failed: {e}")

    def _format_messages_as_prompt(
        self, messages: List[Dict[str, str]]
    ) -> str:
        """Format conversation messages as a prompt string.

        Args:
            messages: List of message dicts

        Returns:
            Formatted prompt string
        """
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt += f"{content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"

        prompt += "Assistant: "
        return prompt
