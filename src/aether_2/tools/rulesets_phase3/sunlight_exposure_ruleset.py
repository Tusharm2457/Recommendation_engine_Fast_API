from typing import Dict, Any, List
from .constants import FOCUS_AREAS


class SunlightExposureRuleset:
    """
    Ruleset for evaluating sunlight exposure ranking patterns.
    
    Analyzes the ranked order of days (most to least sunlight) to detect:
    - Weekend dominance (social jetlag)
    - Erratic patterns (circadian misalignment)
    - Regular weekday patterns (protective)
    """
    
    # Per-domain caps for this field
    CAPS = {
        "STR": 0.50,
        "GA": 0.40,
        "CM": 0.20,
        "COG": 0.20,
        "IMM": 0.30,  # For negative (protective) scores
        "MITO": 0.20,
        "SKN": 0.20,
        "HRM": 0.20,
        "DTX": 0.20
    }
    
    # Day name mappings (abbreviations and full names)
    DAY_MAPPINGS = {
        "mon": "Mon", "monday": "Mon",
        "tue": "Tue", "tues": "Tue", "tuesday": "Tue",
        "wed": "Wed", "wednesday": "Wed",
        "thu": "Thu", "thur": "Thu", "thurs": "Thu", "thursday": "Thu",
        "fri": "Fri", "friday": "Fri",
        "sat": "Sat", "saturday": "Sat",
        "sun": "Sun", "sunday": "Sun"
    }
    
    WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    WEEKEND = ["Sat", "Sun"]
    ALL_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    def get_sunlight_exposure_weights(
        self,
        ranking_data: Any,
        age: int = None,
        bright_light_at_night: bool = False,
        daylight_sufficient: bool = False
    ) -> Dict[str, float]:
        """
        Calculate focus area weights based on sunlight exposure ranking pattern.
        
        Args:
            ranking_data: String with ranked days (e.g., "Sat, Sun, Fri, Thu, Wed, Tue, Mon")
            age: Patient age (must be >= 18)
            bright_light_at_night: Optional flag from other fields
            daylight_sufficient: Optional flag from other fields (adequate daylight ≥5 days/week)
        
        Returns:
            Dictionary mapping focus area codes to weight adjustments
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # Age check
        if age and age < 18:
            return scores
        
        if not ranking_data:
            return scores
        
        # Parse the ranking
        days_ranked = self._parse_ranking(ranking_data)
        
        if not days_ranked or len(days_ranked) < 7:
            # Incomplete data - return zeros
            return scores
        
        # Calculate rank positions (1 = most exposure, 7 = least)
        rank_positions = self._calculate_rank_positions(days_ranked)
        
        # Calculate pattern features
        weekend_avg = (rank_positions["Sat"] + rank_positions["Sun"]) / 2.0
        weekday_avg = sum(rank_positions[day] for day in self.WEEKDAYS) / 5.0
        wdi = weekday_avg - weekend_avg  # Weekend Dominance Index
        
        # Weekend-only classifier
        weekend_only = self._is_weekend_only(rank_positions)
        
        # Oscillation count (direction changes)
        oscillation_count = self._count_oscillations(rank_positions)
        
        # Apply decision rules
        scores = self._apply_circadian_misalignment_rules(
            scores, wdi, weekend_only, oscillation_count
        )
        
        scores = self._apply_regular_pattern_rules(
            scores, wdi, oscillation_count
        )
        
        # Optional cross-field modifiers
        if bright_light_at_night:
            scores["STR"] += 0.10
        
        if daylight_sufficient and wdi < 1.0:
            scores["IMM"] -= 0.05
        
        # Apply caps
        for domain in scores:
            if scores[domain] >= 0:
                scores[domain] = min(scores[domain], self.CAPS.get(domain, 1.0))
            else:
                # Negative (protective) scores - cap at negative limit
                scores[domain] = max(scores[domain], -self.CAPS.get(domain, 0.3))
        
        return scores
    
    def _parse_ranking(self, data: Any) -> List[str]:
        """
        Parse ranking data into list of day names.
        
        Supports formats:
        - "Sat, Sun, Fri, Thu, Wed, Tue, Mon"
        - "Sat; Sun; Fri; Thu; Wed; Tue; Mon"
        - "saturday, sunday, friday, thursday, wednesday, tuesday, monday"
        
        Returns:
            List of standardized day names (e.g., ["Sat", "Sun", "Fri", ...])
        """
        if not isinstance(data, str):
            return []
        
        # Split by common separators
        data_str = data.strip()
        
        # Try multiple separators
        if "," in data_str:
            parts = data_str.split(",")
        elif ";" in data_str:
            parts = data_str.split(";")
        else:
            # Try whitespace
            parts = data_str.split()
        
        # Normalize each day name
        days_ranked = []
        for part in parts:
            day_str = part.strip().lower()
            if day_str in self.DAY_MAPPINGS:
                days_ranked.append(self.DAY_MAPPINGS[day_str])
        
        return days_ranked
    
    def _calculate_rank_positions(self, days_ranked: List[str]) -> Dict[str, int]:
        """
        Convert ranked list to position mapping.

        Args:
            days_ranked: List of days in order from most to least exposure

        Returns:
            Dict mapping day name to rank position (1 = most, 7 = least)
        """
        rank_positions = {}
        for i, day in enumerate(days_ranked):
            rank_positions[day] = i + 1  # 1-indexed
        return rank_positions

    def _is_weekend_only(self, rank_positions: Dict[str, int]) -> bool:
        """
        Check if pattern is weekend-only (strong weekend dominance).

        Criteria (from spec):
        - Sat and Sun both in top 2 (rank <= 2)
        - At least 4 weekdays ranked 3rd-7th (rank >= 3)

        This means at most 1 weekday can be in positions 1-2.

        Returns:
            True if weekend-only pattern detected
        """
        sat_rank = rank_positions.get("Sat", 7)
        sun_rank = rank_positions.get("Sun", 7)

        # Both weekend days in top 2
        if sat_rank > 2 or sun_rank > 2:
            return False

        # Count weekdays ranked 3rd-7th (NOT in top 2)
        # Spec says: "≥4 weekdays are ranked 3rd–7th"
        low_ranked_weekdays = sum(
            1 for day in self.WEEKDAYS
            if rank_positions.get(day, 7) >= 3
        )

        return low_ranked_weekdays >= 4

    def _count_oscillations(self, rank_positions: Dict[str, int]) -> int:
        """
        Count direction changes in the ranking pattern (Mon -> Sun).

        Oscillation = change from increasing to decreasing or vice versa.
        High oscillation count (≥4) indicates erratic/zig-zag pattern.

        Returns:
            Number of direction changes
        """
        # Get ranks in Mon-Sun order
        ranks = [rank_positions.get(day, 7) for day in self.ALL_DAYS]

        if len(ranks) < 3:
            return 0

        # Count direction changes
        oscillations = 0
        for i in range(1, len(ranks) - 1):
            prev_diff = ranks[i] - ranks[i - 1]
            next_diff = ranks[i + 1] - ranks[i]

            # Direction change if signs differ (and neither is zero)
            if prev_diff != 0 and next_diff != 0:
                if (prev_diff > 0 and next_diff < 0) or (prev_diff < 0 and next_diff > 0):
                    oscillations += 1

        return oscillations

    def _apply_circadian_misalignment_rules(
        self,
        scores: Dict[str, float],
        wdi: float,
        weekend_only: bool,
        oscillation_count: int
    ) -> Dict[str, float]:
        """
        Apply rules for circadian misalignment patterns.

        Patterns:
        - Weekend-only: Strong social jetlag
        - Strong weekend dominance: Moderate social jetlag
        - Moderate weekend bias: Mild social jetlag
        - Erratic week: Irregular zeitgebers
        """
        # 1) Weekend-only (strongest signal)
        if weekend_only:
            scores["STR"] += 0.35
            scores["GA"] += 0.15
            scores["CM"] += 0.10
            scores["COG"] += 0.05

        # 2) Strong weekend dominance (WDI >= 2.0, not weekend-only)
        elif wdi >= 2.0:
            scores["STR"] += 0.25
            scores["GA"] += 0.10
            scores["CM"] += 0.05

        # 3) Moderate weekend bias (1.0 <= WDI < 2.0)
        elif wdi >= 1.0:
            scores["STR"] += 0.15
            scores["GA"] += 0.05

        # 4) Erratic week (oscillation count >= 4)
        if oscillation_count >= 4:
            scores["STR"] += 0.20
            scores["GA"] += 0.10

        return scores

    def _apply_regular_pattern_rules(
        self,
        scores: Dict[str, float],
        wdi: float,
        oscillation_count: int
    ) -> Dict[str, float]:
        """
        Apply rules for regular, protective patterns.

        Patterns:
        - Weekday-dominant regularity: Consistent daytime light
        - Balanced exposure: Regular zeitgeber input
        """
        # 1) Weekday-dominant regularity (WDI <= -1.0 and OC <= 2)
        if wdi <= -1.0 and oscillation_count <= 2:
            scores["STR"] -= 0.20
            scores["GA"] -= 0.05

        # 2) Balanced exposure (|WDI| < 1.0 and OC <= 2)
        elif abs(wdi) < 1.0 and oscillation_count <= 2:
            scores["STR"] -= 0.15
            scores["GA"] -= 0.05

        return scores

