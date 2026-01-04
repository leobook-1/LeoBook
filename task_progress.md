# Task Progress: Fix Empty Team Names Issue

## Problem
The LLM Semantic Matcher is filtering out matches because they have empty team names. The issue is in the football.com extractor where team name selectors aren't correctly finding team names on the page.

## Solution Steps

- [ ] 1. Analyze the current team name selectors in extractor.py
- [ ] 2. Check the knowledge.json file for correct football.com selectors  
- [ ] 3. Update the JavaScript extraction logic to use correct selectors
- [ ] 4. Test the fix by running a test extraction
- [ ] 5. Verify that team names are now being extracted correctly
- [ ] 6. Ensure the LLM Semantic Matcher can now match predictions successfully

## Expected Outcome
All matches should have valid team names and the LLM Semantic Matcher should be able to match predictions instead of filtering them out as invalid.
