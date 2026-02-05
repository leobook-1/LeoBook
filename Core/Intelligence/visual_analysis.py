# visual_analysis.py: Low-level visual processing and screenshot interpretation.
# Refactored for Clean Architecture (v2.7)
# This script handles base64 encoding and visual prompt construction.

"""
Visual Analysis Module
Handles screenshot capture and visual UI analysis using Local Leo AI.
"""

import base64
import traceback
import asyncio
import requests
import os
import json
from .prompts import get_keys_for_context, BASE_VISUAL_INSTRUCTIONS
from .api_manager import leo_api_call_with_rotation as ai_api_call


async def get_visual_ui_analysis(page, context_key: str) -> str | None:
    """Capture and analyze visual UI elements from screenshot using dynamic context-aware keys"""
    try:
        # 1. Capture Screenshot
        try:
            screenshot_bytes = await page.screenshot(full_page=True, type="jpeg", quality=60, timeout=15000)
        except Exception:
            print(f"    [VISUAL WARNING] Full page screenshot failed. Falling back to viewport.")
            screenshot_bytes = await page.screenshot(full_page=False, type="jpeg", quality=60)
        
        img_data = base64.b64encode(screenshot_bytes).decode("utf-8")

        # 2. Get Dynamic Keys for this context
        target_keys = get_keys_for_context(context_key)
        keys_str = json.dumps(target_keys, indent=2)

        # 3. Build Prompt
        prompt = f"{BASE_VISUAL_INSTRUCTIONS}\n{keys_str}"

        # 4. Multimodal AI Analysis
        print(f"    [VISUAL] Analyzing {context_key} UI via AI API...")
        
        content = [
            {"type": "text", "text": prompt},
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": img_data
                }
            }
        ]
        
        response = await ai_api_call(content, generation_config={"temperature": 0.1})

        if response and hasattr(response, 'text') and response.text:
            return response.text
        else:
            print(f"    [VISUAL ERROR] AI API returned no text response")
            return None

    except Exception as e:
        traceback.print_exc()
        print(f"    [VISUAL ERROR] Failed to analyze screenshot: {e}")
        return None
