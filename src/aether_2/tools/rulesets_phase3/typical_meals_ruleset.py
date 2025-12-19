"""
Typical Meals Ruleset for Phase 3 Focus Area Evaluation (LLM-based)

Field: "Walk me through your typical meals and snacks."
Answer: Free-text multiline description

Scoring Logic:
- Uses LLM (Gemini 2.0 Flash) to categorize dietary patterns into predefined branches
- LLM returns comma-separated list of detected categories with frequency
- Python script applies corresponding scores based on detected categories
- Per-domain caps: ±1.5 for all focus areas

Age gating: Only score if age >= 18
"""

from typing import Dict, Any, List, Optional
import re
from .constants import call_vertex_ai_llm


class TypicalMealsRuleset:
    """Ruleset for evaluating dietary patterns using LLM categorization."""

    # Per-domain caps
    CAPS = {
        "CM": 1.5,
        "COG": 1.5,
        "DTX": 1.5,
        "IMM": 1.5,
        "MITO": 1.5,
        "SKN": 1.5,
        "STR": 1.5,
        "HRM": 1.5,
        "GA": 1.5,
    }

    # Frequency scalars
    FREQUENCY_SCALARS = {
        "rare": 0.25,
        "some days": 0.6,
        "most days": 0.9,
        "daily": 1.0,
    }

    # Category weights (base weights before frequency scaling)
    CATEGORY_WEIGHTS = {
        "Refined carbs/UPF": {
            "CM": 0.35,
            "IMM": 0.15,
            "GA": 0.20,
            "DTX": 0.10
        },
        "Emulsifiers": {
            "GA": 0.30,
            "IMM": 0.10,
            "DTX": 0.10
        },
        "Artificial sweeteners": {
            "GA": 0.25,
            "CM": 0.10
        },
        "High caffeine": {
            "STR": 0.20
        },
        "Late meals": {
            "GA": 0.25,
            "STR": 0.05
        },
        "Large meals": {
            "GA": 0.25
        },
        "Fatty/fried foods": {
            "GA": 0.20
        },
        "Carbonated beverages": {
            "GA": 0.20
        },
        "Spicy/acidic foods": {
            "GA": 0.15
        },
        "Plant diversity": {
            "CM": -0.15,
            "IMM": -0.15,
            "GA": -0.25
        },
        "High fruit/veg": {
            "CM": -0.20,
            "IMM": -0.15
        },
        "Fermented foods": {
            "GA": -0.25,
            "IMM": -0.10
        },
        "Hydration/walks": {
            "GA": -0.10
        },
        "Processed meats": {
            "CM": 0.15,
            "DTX": 0.10,
            "GA": 0.20
        },
        "Alcohol with GI": {
            "DTX": 0.20,
            "GA": 0.15
        }
    }

    # Flags and their weights
    FLAG_WEIGHTS = {
        "home-cooked flag": {
            "DTX": -0.10,
            "CM": -0.10
        },
        "timing flag": {
            "STR": -0.05,
            "CM": -0.05
        },
        "post-meal flag": {
            "GA": -0.10
        },
        "Omega-3 flag": {
            "IMM": -0.10,
            "CM": -0.10
        }
    }

    def _create_llm_prompt(self, meals_text: str) -> str:
        """Create prompt for LLM to categorize dietary patterns with frequency."""
        
        prompt = f"""You are a clinical nutrition expert analyzing a patient's typical meals and snacks.

Your task is to categorize the dietary patterns into predefined categories based on the description below.
For EACH category you detect, also estimate the frequency (rare/some days/most days/daily).

**Patient's Meal Description:**
{meals_text}

**Available Categories (select ALL that apply with frequency):**
1. "Refined carbs/UPF" - Frequent refined carbs, ultra-processed foods, fast food, packaged snacks, sugary items
2. "Emulsifiers" - Foods containing emulsifiers (polysorbate-80, CMC, processed sauces, ice cream, stabilizers)
3. "Artificial sweeteners" - Diet soda, sugar-free products, sucralose, aspartame, saccharin
4. "High caffeine" - ≥3 cups coffee/day or energy drinks, especially afternoon/evening
5. "Late meals" - Eating within 2-3 hours of bedtime, late dinners, bedtime snacks
6. "Large meals" - Large portions, overeating, feeling very full/stuffed
7. "Fatty/fried foods" - Fried foods, greasy/oily foods, high-fat meals
8. "Carbonated beverages" - Soda, sparkling water, beer, fizzy drinks
9. "Spicy/acidic foods" - Spicy foods, citrus, tomato sauce, vinegar, hot sauce
10. "Plant diversity" - ≥30 different plants/week OR mentions variety/diverse diet with many fruits/vegetables/grains/legumes/nuts
11. "High fruit/veg" - ≥5 servings/day fruits/vegetables OR Mediterranean-style diet
12. "Fermented foods" - ≥2 servings/day of yogurt, kefir, kimchi, sauerkraut, miso, kombucha
13. "Hydration/walks" - ≥2L water/day OR post-meal walks mentioned
14. "Processed meats" - Bacon, sausage, deli meats, hot dogs, salami
15. "Alcohol with GI" - Nightly alcohol (wine/beer/spirits) mentioned

**Special Flags (select if applicable, no frequency needed):**
- "Unhealthy flag" - If ≥3 categories from items 5-9 are detected (late meals, large meals, fatty/fried, carbonated, spicy/acidic)
- "home-cooked flag" - If mentions home-cooked, homemade, cooking from scratch, whole foods most days AND no unhealthy patterns
- "timing flag" - If mentions early dinner, 12-14 hour overnight fast, time-restricted eating
- "post-meal flag" - If mentions bitters, ginger, or peppermint after meals for digestion
- "Omega-3 flag" - If mentions fish ≥2×/week OR flax/chia seeds regularly

**Frequency Definitions:**
- "rare" = ≤1×/week or rarely/seldom mentioned
- "some days" = 2-4×/week or sometimes/occasionally
- "most days" = 5-6×/week or usually/often
- "daily" = every day or 7×/week or always

**Instructions:**
1. Read the meal description carefully
2. Select ALL categories that clearly apply based on the description
3. For each category, estimate frequency based on the text (rare/some days/most days/daily)
4. Be conservative - only select if there's clear evidence in the text
5. Return ONLY a comma-separated list in the format: "Category (frequency), Category (frequency), Flag"
6. Do NOT include explanations, just the list

**Output Format:**
Category1 (frequency), Category2 (frequency), Flag1, Flag2

**Example Output 1:**
Refined carbs/UPF (most days), Carbonated beverages (daily), Late meals (some days), Unhealthy flag

**Example Output 2:**
Plant diversity (daily), High fruit/veg (daily), Fermented foods (most days), home-cooked flag, timing flag

**Your Response (comma-separated list only):**"""

        return prompt

    def _parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """
        Parse LLM response into categories with frequencies and flags.

        Args:
            llm_response: Comma-separated string from LLM

        Returns:
            Dict with 'categories' (list of tuples) and 'flags' (list of strings)
            Example: {
                'categories': [('Refined carbs/UPF', 'most days'), ('Late meals', 'some days')],
                'flags': ['Unhealthy flag']
            }
        """
        categories = []
        flags = []

        if not llm_response:
            return {'categories': categories, 'flags': flags}

        # Split by comma
        items = [item.strip() for item in llm_response.split(',')]

        for item in items:
            # Check if it's a flag (no parentheses)
            if '(' not in item:
                # It's a flag
                if 'flag' in item.lower():
                    flags.append(item)
            else:
                # It's a category with frequency
                # Extract category and frequency using regex
                match = re.match(r'(.+?)\s*\((.+?)\)', item)
                if match:
                    category = match.group(1).strip()
                    frequency = match.group(2).strip().lower()
                    categories.append((category, frequency))

        return {'categories': categories, 'flags': flags}

    def _get_frequency_scalar(self, frequency: str) -> float:
        """Convert frequency string to scalar."""
        frequency_lower = frequency.lower()

        if frequency_lower in self.FREQUENCY_SCALARS:
            return self.FREQUENCY_SCALARS[frequency_lower]

        # Default to most days if unclear
        return 0.9

    def get_typical_meals_weights(
        self,
        meals_data: Any,
        age: int = None,
        digestive_symptoms: str = None,
        current_supplements: List[str] = None
    ) -> Dict[str, float]:
        """
        Calculate focus area weights based on typical meals description.

        Args:
            meals_data: Free-text description of typical meals
            age: Patient age (must be >= 18)
            digestive_symptoms: Digestive symptoms from Phase 2 (for caffeine + reflux check)
            current_supplements: List of current supplements (for omega-3 double-counting check)

        Returns:
            Dict mapping focus area codes to weight adjustments
        """
        weights = {
            "CM": 0.0,
            "COG": 0.0,
            "DTX": 0.0,
            "IMM": 0.0,
            "MITO": 0.0,
            "SKN": 0.0,
            "STR": 0.0,
            "HRM": 0.0,
            "GA": 0.0,
        }

        # Age gating
        if age is None or age < 18:
            return weights

        # Validate input
        if not meals_data:
            return weights

        text = str(meals_data).strip()

        # Minimum word count check (at least 10 words)
        if len(text.split()) < 10:
            return weights

        # Call LLM to categorize dietary patterns
        prompt = self._create_llm_prompt(text)
        llm_response = call_vertex_ai_llm(prompt, temperature=0.0)

        if not llm_response:
            return weights

        # Parse LLM response
        parsed = self._parse_llm_response(llm_response)
        categories = parsed['categories']
        flags = parsed['flags']

        # Track GA triggers for Unhealthy flag bonus
        ga_trigger_count = 0
        ga_trigger_categories = ["Late meals", "Large meals", "Fatty/fried foods",
                                 "Carbonated beverages", "Spicy/acidic foods"]

        # Apply category weights
        for category, frequency in categories:
            if category in self.CATEGORY_WEIGHTS:
                freq_scalar = self._get_frequency_scalar(frequency)
                category_weights = self.CATEGORY_WEIGHTS[category]

                for focus_area, base_weight in category_weights.items():
                    weights[focus_area] += base_weight * freq_scalar

                # Count GA triggers
                if category in ga_trigger_categories:
                    ga_trigger_count += 1

        # Apply flags
        for flag in flags:
            if flag in self.FLAG_WEIGHTS:
                flag_weights = self.FLAG_WEIGHTS[flag]
                for focus_area, weight in flag_weights.items():
                    weights[focus_area] += weight

        # Special handling: High caffeine + reflux
        # Check if "High caffeine" was detected AND digestive symptoms contain reflux keywords
        caffeine_detected = any(cat == "High caffeine" for cat, _ in categories)
        if caffeine_detected and digestive_symptoms:
            reflux_keywords = ['heartburn', 'reflux', 'gerd', 'acid', 'burning', 'indigestion']
            if any(kw in digestive_symptoms.lower() for kw in reflux_keywords):
                weights["GA"] += 0.10

        # Special handling: Unhealthy flag bonus
        # If ≥3 GA triggers detected, add extra GA weight
        if ga_trigger_count >= 3 or "Unhealthy flag" in flags:
            weights["GA"] += 0.10

        # Special handling: Omega-3 flag - check for double counting
        if "Omega-3 flag" in flags and current_supplements:
            # Check if already taking omega-3 supplements
            omega3_supplements = ['fish oil', 'omega-3', 'omega 3', 'epa', 'dha', 'krill oil']
            already_supplementing = any(
                any(omega in supp.lower() for omega in omega3_supplements)
                for supp in current_supplements
            )

            if not already_supplementing:
                # Apply omega-3 flag weights only if not already supplementing
                flag_weights = self.FLAG_WEIGHTS["Omega-3 flag"]
                for focus_area, weight in flag_weights.items():
                    weights[focus_area] += weight

        # Apply caps
        for code in weights:
            if weights[code] > 0:
                weights[code] = min(weights[code], self.CAPS.get(code, 1.5))
            else:
                weights[code] = max(weights[code], -self.CAPS.get(code, 1.5))

        return weights

