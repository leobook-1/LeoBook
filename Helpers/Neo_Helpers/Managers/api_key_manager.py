# api_key_manager.py
import os
import json
import base64
import ollama

# Default model, can be overridden by env or config
DEFAULT_MODEL = "qwen3-vl:2b"

async def gemini_api_call_with_rotation(prompt_content, generation_config=None, **kwargs):
    """
    Replaces the original Gemini API call with a local Ollama call.
    Maintains the function name to avoid breaking existing imports,
    but redirects logic to the local qwen3-vl model.
    """
    print(f"    [Ollama] Processing request with model {DEFAULT_MODEL}...")

    # precise input parsing
    prompt_text = ""
    images = []

    if isinstance(prompt_content, list):
        for item in prompt_content:
            if isinstance(item, str):
                prompt_text += item + "\n"
            elif isinstance(item, dict) and "inline_data" in item:
                # Extract image data
                # Expected format: {"inline_data": {"mime_type": "image/png", "data": base64_str}}
                b64_data = item["inline_data"].get("data")
                if b64_data:
                    # Ollama python client accepts base64 strings in the 'images' list for vision models
                    # It also accepts bytes. Let's pass the bytes to be safe, or just the b64 string.
                    # Qwen2-VL/Qwen3-VL in Ollama supports base64.
                    # The python library 'ollama' expects 'images': [path_or_bytes_or_base64]
                    images.append(b64_data)
    elif isinstance(prompt_content, str):
        prompt_text = prompt_content

    # Extract temperature from generation_config if provided
    options = {}
    if generation_config:
        # generation_config might be an object or dict
        if hasattr(generation_config, 'temperature'):
            options['temperature'] = generation_config.temperature
        elif isinstance(generation_config, dict) and 'temperature' in generation_config:
            options['temperature'] = generation_config['temperature']
    
    # Defaults
    if 'temperature' not in options:
        options['temperature'] = 0.1

    try:
        # Prepare the message
        message = {
            'role': 'user',
            'content': prompt_text,
        }
        if images:
            message['images'] = images

        # Call Ollama
        response = ollama.chat(
            model=DEFAULT_MODEL,
            messages=[message],
            options=options
        )
        
        # Wrap response to match loosely what Gemini provided (an object with .text)
        class MockGeminiResponse:
            def __init__(self, content):
                self.text = content
                self.candidates = [type('MockCandidate', (), {'content': type('MockContent', (), {'parts': [type('MockPart', (), {'text': content})]})})]

        return MockGeminiResponse(response['message']['content'])

    except Exception as e:
        print(f"    [Ollama Error] Failed to generate content: {e}")
        return None
