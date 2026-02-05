# visual_analyzer.py: Advanced multimodal UI analysis engine.
# Refactored for Clean Architecture (v2.7)
# This script combines screenshots and DOM trees to derive interaction strategies.

"""
Visual Analyzer Module
Handles screenshot analysis and visual UI processing using Local Leo AI.
Orchestrates sub-modules for visual analysis, selector mapping, and recovery.
"""

import os
import re
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from .selector_db import knowledge_db, save_knowledge
from ..Browser.page_logger import log_page_html
from ..Utils.utils import LOG_DIR


# Import sub-modules
from .html_utils import clean_html_content
from .selector_mapping import map_visuals_to_selectors
from .selector_utils import simplify_selectors
from .recovery import attempt_visual_recovery

# --- Vision Integration ---

async def get_visual_ui_analysis(page: Any, context_key: str = "unknown") -> str:
    from .api_manager import grok_api_call
    import os

    print(f"    [VISION] Loading UI/UX analysis from logged screenshot for '{context_key}'...")

    # Look in Page subdirectory where screenshots are saved
    PAGE_LOG_DIR = LOG_DIR / "Page"
    files = list(PAGE_LOG_DIR.glob(f"*{context_key}.png"))

    if not files:
        print(f"    [VISION ERROR] No screenshot found for context: {context_key}")
        return ""

    # Get the most recent screenshot
    png_file = max(files, key=os.path.getmtime)
    print(f"    [VISION] Using logged screenshot: {png_file.name}")

    try:
        # Check if file is not empty (successful screenshot)
        if png_file.stat().st_size == 0:
            print(f"    [VISION ERROR] Screenshot file is empty: {png_file.name}")
            return ""

        image_data = {"mime_type": "image/png", "data": png_file.read_bytes()}

        prompt = """
        You are a senior front-end engineer and UI/UX analyst with 15+ years of experience in reverse-engineering complex web applications.
        Your task: Perform an exhaustive, pixel-perfect visual inventory of the provided screenshot.
        Analyze every visible element on the page — nothing is too small.
        Organize your response using ONLY this exact hierarchical structure (do not deviate):
        1. Layout & Structural Elements
           • Overall page layout (e.g., "fixed header + sticky secondary nav + main content + right sidebar")
           • Fixed, sticky, or absolute-positioned containers
           • Scroll containers and overflow boundaries
        2. Navigation Components
           • Primary and secondary navigation bars
           • Tab groups with current active state clearly marked
           • Icon buttons (hamburger, back, close, search, profile)
        3. Interactive Controls
           • Buttons: text, icon-only, outlined, filled, FABs — include visible text and state
           • Toggles, switches, checkboxes, radio groups
           • Text inputs, search fields, filters
        4. Content & Data Display
           • Cards, lists, tables, expandable rows
           • Match/event rows (critical — describe structure in detail)
           • Typography: headings, labels, timestamps, scores, team names
           • Badges, chips, tags, live indicators (LIVE, HT, FT)
        5. Advertising & Promotional
           • All ad containers and close buttons
        6. System & Feedback Elements
           • Cookie consent banners, privacy modals
           • Loading skeletons, spinners
        7. Other Notable Elements
           • Language selector, dark mode toggle

        For every element, use brief naming: "UI Element Name: Exact Text (or Function if no text)".
        Include: Position, Repetition, State.
        Be exhaustive. Do not summarize.
        """
        response = await grok_api_call(
            [prompt, image_data],
            generation_config={"temperature": 0.1}
        )

        if response and hasattr(response, 'text') and response.text:
            print("    [VISION] UI/UX Analysis complete.")
            return response.text
        else:
            print("    [VISION ERROR] No valid response from Grok API")
            return ""

    except Exception as e:
        print(f"    [VISION ERROR] Failed to analyze screenshot: {e}")
        return ""


class VisualAnalyzer:
    """Handles visual analysis of web pages by orchestrating sub-modules"""

    @staticmethod
    async def analyze_page_and_update_selectors(
        page,
        context_key: str,
        force_refresh: bool = False,
        info: Optional[str] = None,
    ):
        """
        1. Checks if selectors exist. If they do and not force_refresh, skips.
        2. Captures Visual UI Inventory (The What).
        3. Captures HTML (The How).
        4. Maps Visuals to HTML Selectors with STANDARDIZED KEYS for critical items.
        """
        Focus = info
        # --- INTELLIGENT SKIP LOGIC ---
        if not force_refresh and context_key in knowledge_db and knowledge_db[context_key]:
            print(f"    [AI INTEL] Selectors found for '{context_key}'. Skipping AI analysis.")
            return

        print(
            f"    [AI INTEL] Starting Full Discovery for context: '{context_key}' (Force: {force_refresh})..."
        )

        print(f"    [AI INTEL] Taking Screenshot and HTML capture of: '{context_key}'...")
        await log_page_html(page, context_key)

        # Step 1: Get Visual Context
        # Note: We rely on the screenshot existing. If calling from get_selector_auto, we ensured a fresh one.
        ui_visual_context = await get_visual_ui_analysis(page, context_key)
        if not ui_visual_context:
            return

        PAGE_LOG_DIR = LOG_DIR / "Page"
        files = list(PAGE_LOG_DIR.glob(f"*{context_key}.html"))
        if not files:
            print(f"    [AI INTEL ERROR] No HTML file found for context: {context_key}")
            return

        html_file = max(files, key=os.path.getmtime)
        print(f"    [AI INTEL] Using logged HTML: {html_file.name}")

        try:
            with open(html_file, "r", encoding="utf-8") as f:
                html_content = f.read()
        except Exception as e:
            print(f"    [AI INTEL ERROR] Failed to load HTML: {e}")
            return

        # Optional: Minimal clean to save tokens
        html_content = re.sub(
            r"<script.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE
        )
        html_content = re.sub(
            r"<style.*?</style>", "", html_content, flags=re.DOTALL | re.IGNORECASE
        )
        html_content = html_content[:100000]  # Truncate if too long

        # Step 3: Map Visuals to HTML (with Extraction Rules)
        print("    [AI INTEL] Mapping UI Elements to HTML Selectors...")
        prompt = f"""
        You are an elite front-end reverse-engineer tasked with mapping every visible UI element from a screenshot to a precise, working CSS selector using the provided HTML.
        You have two responsibilities:
        1. Map critical Flashscore/Football.com elements using EXACT predefined keys
        2. Map all other visible elements using a rigid, predictable naming convention
        CRITICAL RULES — FOLLOW EXACTLY:
        ### 1. MANDATORY CORE ELEMENTS (Use These Exact Keys If Present)
        Important: {Focus}
        Use these keys EXACTLY as written if the element exists on the page:
        {{
        "sport_container": "Main container holding all football matches and leagues",
        "league_header": "Header row containing country and league name",
        "match_rows": "Selector that matches ALL individual match rows",
        "match_row_home_team_name": "Element inside a match row containing the home team name",
        "match_row_away_team_name": "Element inside a match row containing the away team name",
        "match_row_time": "Element inside a match row showing kick-off time",
        "next_day_button": "Button or icon that navigates to tomorrow's fixtures",
        "prev_day_button": "Button or icon that navigates to previous day",
        "league_category": "Country name (e.g., ENGLAND) in league header",
        "league_title_link": "Clickable league name link in header",
        "event_row_link": "Anchor tag inside match row linking to match detail page",
        "cookie_accept_button": "Primary accept button in cookie/privacy banner",
        "tab_live": "Live matches tab",
        "tab_finished": "Finished matches tab",
        "tab_scheduled": "Scheduled/upcoming matches tab",
        "final_score_home": "The home team final score in the match page",
        "final_score_away": "The away team final score in the match page",
        "h2h_tab": "Head-to-head statistics tab on match page",
        "h2h_section_home": "Container/section that holds home team last matches",
        "h2h_section_away": "Container/section that holds away team last matches",
        "h2h_section_h2h": "Container/section that holds direct head-to-head last matches",
        "h2h_rows": "The row that contains individual past match entries in row_h2h_section. This has a link to match details.",
        "row_h2h_section_home": "The entire h2h_rows container for home team past matches.",
        "row_h2h_section_away": "The entire h2h_rows container for away team past matches.",
        "row_h2h_section_h2h": "The entire h2h_rows container for direct head-to-head past matches.",
        "show_more_matches_button_home": "Button that reveals more past matches in row_h2h_section for home team",
        "show_more_matches_button_away": "Button that reveals more past matches in row_h2h_section for away team",
        "show_more_matches_button_h2h": "Button that reveals more past matches in row_h2h_section for direct head-to-head matches",
        "standings_tab": "Standings/league table tab on match page",
        "tooltip_i_understand_button": "Button with text 'I understand' in a tooltip, like the one with data-testid 'wcl-tooltip-actionButton'",
        # fb_login_page keys
        "top_right_login": "official logical method",
        "center_text_mobile_number_placeholder": "Input field placeholder for entering mobile number",
        "center_text_password_placeholder": "Input field placeholder for entering password",
        "bottom_button_text_login": "Primary login button text at the bottom",
        "center_link_forgot_password": "Link to recover forgotten password",
        "center_text_mobile_country_code": "Text displaying the mobile country code",
        "top_container_nav_bar": "Top navigation bar container",
        "top_icon_back": "Back icon in the top navigation bar",
        "top_icon_close": "Close icon for popup. the close icon is usually at the top right corner.",
        "top_tab_register": "Register tab in the navigation menu",
        "top_tab_login": "Login tab in the navigation menu",
        # fb_main_page keys
        "navbar_balance": "Element showing user balance in the navbar",
        "currency": "Element showing currency class in the navbar_balance",
        "search_button": "Search button/icon in the main page",
        "search_input": "Search input field",
        "bet_slip_fab_icon_button": "Floating action button (FAB) icon/button to open the bet slip section from anywhere on the match page",
        # fb_schedule_page keys
        "pre_match_list_league_container": "Main container holding all pre_match football leagues and matches",
        "league_title_wrapper": "Header row containing country, league name and number of matches in pre_match list",
        "league_title_link": "Clickable league name link in league_title_wrapper",
        "league_wrapper_collapsed": "Same as just 'league_wrapper'(when league_title_wrapper is clicked). Contains the matches for the given league",
        "league_row": "Contains the league_title_wrapper and the league_wrapper_collapsed, which is make up a league. So the league_row is one league",
        "match_card": "Selector with each match details (home team, away team, date, time, league name(and url), and the match page url) in pre_match list",
        "match_card_link": "Anchor tag inside match_card linking to match detail page",
        "match_region_league_name": "Selector with the match region and league name (e.g England - Premier League)",
        "match_card_home_team": "Element inside a match_card containing the home team name",
        "match_card_away_team": "Element inside a match_card containing the away team name",
        "match_card_date": "Element inside a match_card showing match date",
        "match_card_time": "Element inside a match_card showing kick_off time",
        "match_card_league_link": "Clickable href of region-league name in match_card(e.g International Clubs - UEFA Champions League)",
        "match_url": "The href link of the match_card to the match detail page ",
        "bet_slip_fab_icon_button": "Floating action button (FAB) icon/button to open the bet slip section from anywhere on the match page",
        # fb_match_page keys
        "tooltip_icon_close": "tooltip in the top right side of the match page",
        "dialog_container": "popup dialog in the match page",
        "dialog_container_wrapper": "dialog_container that prevents inactive in on the page when the dialog_container appears",
        "intro_dialog": "body of the dialog_container in the match page",
        "intro_dialog_btn": "intro_dialog button for 'Next' and 'Got it'",
        "match_smart_picks_container": "Container for match football.com AI smart picks section",
        "match_smart_picks_dropdown": "Dropdown to reveal different smart pick analysis options",
        "smart_pick_item": "Selector for each individual smart pick item in the smart picks section",
        "match_market_category_tab": "container for market category tabs (e.g., 'All', 'Main', 'Early wins', 'Corners', 'Goals', etc.)",
        "match_market_search_icon_button": "Search icon/button to search for specific betting markets available for the match",
        "match_market_search_input": "Input field to type in betting market search terms available for the match",
        "match_market_details_container": "Container that holds a betting market details for the match. This is the main wrapper for a market group (e.g., 1X2, Over/Under). Clicking on a market header expands it to show all available betting options.",
        "match_market_name": "Element showing the name/title of a specific betting market for the match (e.g Home to win either half, Away to win either half, etc.)",
        "match_market_info_tooltip": "Tooltip icon/button that shows additional information about a specific betting market when clicked",
        "match_market_info_tooltip_text": "The text content inside the tooltip that provides additional information about a specific betting market",
        "match_market_tooltip_ok_button": "OK button inside the betting market tooltip to close it",
        "match_market_table": "Table inside a betting market that lists all available betting options along with their odds",
        "match_market_table_header": "Header row of the betting market table that contains column titles (e.g., 'outcome(value)', 'over', 'under')",
        "match_market_table_row": "Row inside the betting market table representing a single betting option(1.5(in the outcome column), 1.85(in the over column), 1.95(in the under column), etc.)",
        "match_market_odds_button": "The clickable element representing a single betting outcome (e.g., 'Home', 'Over 2.5') that displays the odds. This element should be unique for each outcome.",
        "bet_slip_container": "Container for the bet slip section that shows selected bets and allows users to manage their bets",
        "bet_slip_predicitions_counter": "Text Element inside the bet slip that displays the number of predictions/bets added to the slip. Could be class "real-theme" and "is-zero real-theme(whenthe counter is zero)",
        "bet_slip_remove_all_button": "Button inside the bet slip that allows users to clear all selected bets from the slip",
        "bet_slip_single_bet_tab": "Tab inside the bet slip for placing single bets",
        "bet_slip_multiple_bet_tab": "Tab inside the bet slip for placing multiple bets (accumulators)",
        "bet_slip_system_bet_tab": "Tab inside the bet slip for placing system bets",
        "bet_slip_outcome_list": "List inside the bet slip that shows all selected betting outcomes",
        "bet_slip_outcome_item": "Item inside the bet slip outcome list representing a single selected betting outcome",
        "bet_slip_outcome_remove_button": "Button inside a bet slip outcome item that allows users to remove that specific outcome from the bet slip",
        "bet_slip_outcome_details": "Element inside a bet slip outcome item that displays details about the selected betting outcome (e.g., market name, outcome, odds, match teams etc.). clicking on this element usually navigates to the match page.",
        "match_url": "The URL link to the match detail page from the bet slip outcome details",
        "navbar_balance": "Element showing user currency and balance in the bet slip section",
        "real_match_button": "Button that switches from virtual match to real match all with real money for the selected bet_slip_outcome_item in the bet slip section",
        "stake_input_field_button": "Input field/button to enter stake amount for the selected bet_slip_outcome_item in the bet slip section",
        "stake_input_keypad_button": "Keypad button inside the stake input field to enter stake amount for the selected bet_slip_outcome_item in the bet slip section",
        "keypad_1": "Keypad button for digit '1'",
        "keypad_2": "Keypad button for digit '2'",
        "keypad_3": "Keypad button for digit '3'",
        "keypad_4": "Keypad button for digit '4'",
        "keypad_5": "Keypad button for digit '5'",
        "keypad_6": "Keypad button for digit '6'",
        "keypad_7": "Keypad button for digit '7'",
        "keypad_8": "Keypad button for digit '8'",
        "keypad_9": "Keypad button for digit '9'",
        "keypad_0": "Keypad button for digit '0'",
        "keypad_dot": "Keypad button for decimal point",
        "keypad_clear": "Keypad button to clear the entered stake amount",
        "keypad_done": "Keypad button to confirm the entered stake amount",
        "bet_slip_total_odds": "Element showing total odds for all selected bets in the bet slip",
        "bet_slip_potential_win": "Element showing potential winnings for the entered stake amount in the bet slip",
        "bet_slip_early_win_checkbox": "Checkbox in the bet slip to enable or disable early win cash out option",
        "bet_slip_one_cut_checkbox": "Checkbox in the bet slip to enable or disable one cut option",
        "bet_slip_cut_one_checkbox": "Checkbox in the bet slip to enable or disable cut one option",
        "bet_slip_accept_odds_change_button": "Button in the bet slip to accept any odds changes before placing the bet",
        "bet_slip_book_bet_button": "Button to reveal a bottom sheet/modal get the betslip shareable link, code, and image",
        "bet_code": "Element showing the unique bet code for sharing or retrieving the bet slip",
        "bet_link": "Element showing the unique bet link URL for sharing or retrieving the bet slip",
        "bet_image": "Element showing the bet slip image/graphic for sharing or saving",
        "place_bet_button": "Button to confirm and place the bet with the entered stake amount",
        "bet_slip_fab_icon_button": "Floating action button (FAB) icon/button to open the bet slip section from anywhere on the match page",
        # fb_withdraw_page keys
        "withdrawable_balance": "Element showing user withdrawable balance on the withdraw page",
        "withdraw_input_amount_field": "Input field to enter amount to withdraw on the withdraw page",
        "withdraw_button_submit": "Button to submit the withdrawal request on the withdraw page",
        "withdrawal_pin_field": "four digits input box for withdrawal pin",
        "keypad_1": "Keypad button for digit '1'",
        "keypad_2": "Keypad button for digit '2'",
        "keypad_3": "Keypad button for digit '3'",
        "keypad_4": "Keypad button for digit '4'",
        "keypad_5": "Keypad button for digit '5'",
        "keypad_6": "Keypad button for digit '6'",
        "keypad_7": "Keypad button for digit '7'",
        "keypad_8": "Keypad button for digit '8'",
        "keypad_9": "Keypad button for digit '9'",
        "keypad_0": "Keypad button for digit '0'",
        "keypad_dot": "Keypad button for decimal point",
        "keypad_clear": "Keypad button to clear the entered withdrawal pin",
        "keypad_done": "Keypad button to confirm the entered withdrawal pin",
        }}

        ### 2. ALL OTHER ELEMENTS → Strict Naming Convention
        Pattern: <location>*<type>*<content_or_purpose>
        Examples: top_button_login, header_icon_search, center_text_premier_league
        ### 3. Selector Quality Rules
        - Return ONLY a valid JSON object: {{"key": "selector"}}
        - Prefer IDs > Classes > Attributes.
        - AVOID :contains() (use :has-text() if needed, or better yet simple CSS).
        - NO MARKDOWN in response.
        """

        prompt_tail = f"""
        ### INPUT
        --- VISUAL INVENTORY ---
        {ui_visual_context}
        --- CLEANED HTML SOURCE ---
        {html_content}
        Return ONLY the JSON mapping. No explanations. No markdown.
        """

        full_prompt = prompt + prompt_tail

        try:
            from .api_manager import gemini_api_call_with_rotation, GenerationConfig
            response = await gemini_api_call_with_rotation(
                full_prompt,
                generation_config=GenerationConfig(response_mime_type="application/json")
            )
            # Fix for JSON Decode Errors
            from .utils import clean_json_response
            cleaned_json = clean_json_response(response.text)
            new_selectors = json.loads(cleaned_json)

            knowledge_db[context_key] = new_selectors
            save_knowledge()
            print(f"    [AI INTEL] Successfully mapped {len(new_selectors)} elements.")
        except Exception as e:
            print(f"    [AI INTEL ERROR] Failed to generate selectors map: {e}")
            return

    # Re-export key functions as static methods for backward compatibility if needed
    @staticmethod
    async def get_visual_ui_analysis(page, context_key: str) -> Optional[str]:
        return await get_visual_ui_analysis(page, context_key)

    @staticmethod
    def clean_html_content(html_content: str) -> str:
        return clean_html_content(html_content)

    @staticmethod
    async def map_visuals_to_selectors(
        ui_visual_context: str, html_content: str, focus: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        return await map_visuals_to_selectors(ui_visual_context, html_content, focus)

    @staticmethod
    def simplify_selectors(selectors: Dict[str, str], html_content: str) -> Dict[str, str]:
        return simplify_selectors(selectors, html_content)

    @staticmethod
    async def attempt_visual_recovery(page, context_name: str) -> bool:
        return await attempt_visual_recovery(page, context_name)
