# recovery.py: Visual state recovery and stuck-state resolution.
# Refactored for Clean Architecture (v2.7)
# This script uses multimodal models to find "un-stick" actions (back, close, home).

"""
Recovery Module
Handles visual recovery mechanisms for stuck states.
"""

import base64
import os
import requests
import asyncio
from typing import Optional

from .api_manager import grok_api_call
from .prompts import RECOVERY_PROMPT


async def attempt_visual_recovery(page, context_name: str) -> bool:
    """
    Emergency AI Recovery Mechanism.
    1. Extracts HTML content from the page.
    2. Sends it to Leo AI to identify blocking overlays (Ads, Popups, Modals).
    3. Asks for the CSS selector to click (Close, X, No Thanks).
    4. Executes the click.
    Returns True if a recovery action was taken.
    """
    print(f"    [AI RECOVERY] Analyzing HTML for blockers/popups in context: {context_name}...")

    # 1. Extract HTML content focusing on potential blocking elements
    try:
        html_content = await page.evaluate("""
            () => {
                const getVisibleText = (element) => {
                    if (!element) return '';
                    const style = window.getComputedStyle(element);
                    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                        return '';
                    }
                    return element.textContent.trim().substring(0, 100);
                };

                const blockingElements = [];

                // Common blocking element selectors
                const selectors = [
                    ['[role="dialog"]', 'MODAL_DIALOG'],
                    ['.modal, .popup, .overlay, .lightbox', 'OVERLAY'],
                    ['.cookie-banner, .gdpr-banner, .privacy-notice', 'COOKIE_BANNER'],
                    ['.ad-overlay, .advertisement, .promo-popup', 'AD_OVERLAY'],
                    ['.alert, .notification, .toast', 'ALERT'],
                    ['.login-prompt, .auth-required', 'AUTH_PROMPT'],
                    ['button', 'CLOSE_BUTTONS'],
                    ['[onclick], [data-dismiss], [data-close]', 'DISMISS_ELEMENTS']
                ];

                selectors.forEach(([sel, label]) => {
                    const elements = document.querySelectorAll(sel);
                    Array.from(elements).forEach((el, index) => {
                        const text = getVisibleText(el);
                        if (text) {
                            blockingElements.push(`${label}_${index}: "${text}"`);
                        }
                    });
                });

                // Look for elements with high z-index (potential overlays)
                const allElements = document.querySelectorAll('*');
                Array.from(allElements).forEach((el, index) => {
                    const style = window.getComputedStyle(el);
                    const zIndex = parseInt(style.zIndex) || 0;
                    if (zIndex > 1000 && getVisibleText(el)) {
                        blockingElements.push(`HIGH_ZINDEX_${index}: z-index ${zIndex} - "${getVisibleText(el)}"`);
                    }
                });

                return blockingElements.slice(0, 20).join('\\n'); // Limit to prevent token overflow
            }
        """)
    except Exception as e:
        print(f"    [AI RECOVERY] Could not extract HTML content: {e}")
        return False

    # 2. Format prompt with HTML content
    formatted_prompt = RECOVERY_PROMPT.format(html_content=html_content)

    try:
        response = await grok_api_call(
            formatted_prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        if response and hasattr(response, 'text') and response.text:
            import json
            data = json.loads(response.text)
            selector = data.get("selector")

            if selector and selector != "null":
                print(f"    [AI RECOVERY] Detected blocker. Attempting to click: {selector}")
                try:
                    await page.click(selector, timeout=5000)
                    await asyncio.sleep(1)  # Wait for animation
                    return True
                except Exception as click_e:
                    print(f"    [AI RECOVERY] Failed to click selector {selector}: {click_e}")

    except Exception as e:
        print(f"    [AI RECOVERY] AI Analysis failed: {e}")

    return False
