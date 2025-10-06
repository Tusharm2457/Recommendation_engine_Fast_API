from crewai.tools import BaseTool
from typing import Type, Dict, Any, List, Union, Tuple
from pydantic import BaseModel, Field
import json
import os


class IngredientRankerInput(BaseModel):
    user_profile: Union[str, dict] = Field(
        ..., description="User profile JSON (string or dict) as produced by the profile compiler"
    )
    ingredients_path: str = Field(
        default="inputs/transformed_ingredients.json",
        description="Path to the transformed ingredients JSON dataset"
    )


class IngredientRankerTool(BaseTool):
    name: str = "rank_ingredients_for_user"
    description: str = (
        "Ranks ingredients from a dataset for a specific user profile using a hybrid"
        " rule- and similarity-based scoring with safety filters."
    )
    args_schema: Type[BaseModel] = IngredientRankerInput

    # -----------------------------
    # Helpers: safe get functions
    # -----------------------------
    def _get(self, dct: Dict[str, Any], path: List[str], default=None):
        cur: Any = dct
        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                return default
            cur = cur[key]
        return cur

    # -----------------------------
    # User signals extraction
    # -----------------------------
    def _extract_user_signals(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        patient_summary = user_profile.get("patient_summary", {})
        basic = patient_summary.get("basic_profile", {})
        findings = patient_summary.get("biomarker_findings", {})
        patterns = patient_summary.get("key_health_patterns", []) or []
        goals = patient_summary.get("functional_goals", []) or []
        lifestyle = patient_summary.get("lifestyle_and_context", {})

        high_markers: List[str] = [m.lower() for m in findings.get("high", [])]
        low_markers: List[str] = [m.lower() for m in findings.get("low", [])]

        constraints = {
            "medications": [m.lower() for m in basic.get("medications", [])],
            "allergies": [a.lower() for a in lifestyle.get("known_allergies", [])],
            "diet": [d.lower() for d in basic.get("diet_style", [])],
        }

        # Build intent text for simple token overlap
        intent_parts: List[str] = []
        intent_parts.extend(high_markers)
        intent_parts.extend([f"low:{m}" for m in low_markers])
        intent_parts.extend([p.lower() for p in patterns])
        intent_parts.extend([g.lower() for g in goals])
        intent_text = " ".join(intent_parts)

        return {
            "age": basic.get("age"),
            "sex": basic.get("sex"),
            "bmi": basic.get("BMI"),
            "high_markers": high_markers,
            "low_markers": low_markers,
            "patterns": [p.lower() for p in patterns],
            "goals": [g.lower() for g in goals],
            "constraints": constraints,
            "intent_text": intent_text,
        }

    # -----------------------------
    # Ingredient representation
    # -----------------------------
    def _compose_ingredient_profile_text(self, ing: Dict[str, Any]) -> str:
        parts: List[str] = []
        # Prefer actual dataset fields; fallback to generic ones
        for key in [
            "name",
            "ingredient_name",
            "synonyms",
            "core_health_problems",
            "secondary_health_problems",
            "relevant_conditions",
            "biomarkers_mentioned",
            "biomarker_recommendations",
            "key_actions",
            "medicine_category",
            "chunk_text",
            # generic/optional fields if present
            "mechanisms",
            "indications",
            "targets",
            "benefits",
            "evidence",
            "contraindications",
            "cases_when_not_recommended",
            "interactions",
            "dietary_tags",
        ]:
            val = ing.get(key)
            if val is None:
                continue
            if isinstance(val, list):
                parts.extend([str(v).lower() for v in val])
            else:
                parts.append(str(val).lower())
        return " ".join(parts)

    # -----------------------------
    # Scoring components
    # -----------------------------
    def _token_set(self, text: str) -> set:
        return set([t for t in text.lower().replace("/", " ").replace(",", " ").split() if t])

    def _similarity_score(self, intent_text: str, ing_text: str) -> float:
        # Simple token Jaccard similarity as a lightweight proxy for embeddings
        a = self._token_set(intent_text)
        b = self._token_set(ing_text)
        if not a or not b:
            return 0.0
        inter = len(a & b)
        union = len(a | b)
        return inter / union if union else 0.0

    def _rule_target_score(self, user_signals: Dict[str, Any], ing: Dict[str, Any]) -> float:
        # Build a target bag from various dataset fields
        fields = [
            "targets",
            "indications",
            "relevant_conditions",
            "core_health_problems",
            "secondary_health_problems",
            "biomarkers_mentioned",
            "key_actions",
            "chunk_text",
        ]
        targets: List[str] = []
        for key in fields:
            val = ing.get(key)
            if val is None:
                continue
            if isinstance(val, list):
                targets.extend([str(t).lower() for t in val])
            else:
                targets.append(str(val).lower())

        score = 0.0
        # high markers: look for terms like the marker name or related tokens
        for m in user_signals["high_markers"]:
            if any(m_part in t for t in targets for m_part in m.split()):
                score += 1.0
        # low markers
        for m in user_signals["low_markers"]:
            if any(m_part in t for t in targets for m_part in m.split()):
                score += 1.0
        # goals/patterns
        for g in user_signals["goals"]:
            if any(g_part in t for t in targets for g_part in g.split()):
                score += 0.5
        for p in user_signals["patterns"]:
            if any(p_part in t for t in targets for p_part in p.split()):
                score += 0.5
        return score

    # Note: Focus area overlap intentionally removed per requirements.

    def _evidence_score(self, ing: Dict[str, Any]) -> float:
        # Try multiple fields
        evidence = " ".join([
            str(ing.get("evidence", "")),
            str(ing.get("chunk_text", "")),
        ]).lower()
        if not evidence:
            return 0.0
        if any(k in evidence for k in ["meta-analysis", "systematic review", "rct", "randomized"]):
            return 1.0
        if any(k in evidence for k in ["cohort", "observational", "pilot"]):
            return 0.5
        return 0.2

    def _safety_penalty(self, user_signals: Dict[str, Any], ing: Dict[str, Any]) -> Tuple[float, bool]:
        # returns (penalty, hard_exclude)
        hard_conflict = False
        penalty = 0.0

        # medications interactions (string contains)
        interactions = " ".join([str(x).lower() for x in ing.get("interactions", [])])
        for med in user_signals["constraints"]["medications"]:
            if med and med.split()[0] and med.split()[0] in interactions:
                penalty += 1.0

        # allergies / do-not-use cases
        allergens = " ".join([
            *[str(x).lower() for x in ing.get("contraindications", [])],
            *[str(x).lower() for x in ing.get("cases_when_not_recommended", [])],
        ])
        for allergy in user_signals["constraints"]["allergies"]:
            if allergy and allergy in allergens:
                hard_conflict = True

        # diet (strict elimination)
        dietary_tags = [str(x).lower() for x in ing.get("dietary_tags", [])]
        user_diet = user_signals["constraints"]["diet"]
        if "vegan" in user_diet and "vegan" not in dietary_tags:
            hard_conflict = True

        return penalty, hard_conflict

    # -----------------------------
    # Main run
    # -----------------------------
    def _run(self, user_profile: Union[str, dict], ingredients_path: str) -> str:
        try:
            profile: Dict[str, Any]
            if user_profile is None or (isinstance(user_profile, str) and not user_profile.strip()):
                # Fallback: try default compiled profile path
                default_profile_path = os.path.join("outputs", "patient_1", "user_profile.json")
                if os.path.exists(default_profile_path):
                    with open(default_profile_path, "r") as pf:
                        profile = json.load(pf)
                else:
                    return json.dumps({"error": "user_profile not provided and default profile not found"}, indent=2)
            elif isinstance(user_profile, str):
                profile = json.loads(user_profile)
            else:
                profile = user_profile

            if not os.path.exists(ingredients_path):
                return json.dumps({
                    "error": f"Ingredients file not found: {ingredients_path}"
                }, indent=2)

            with open(ingredients_path, "r") as f:
                dataset = json.load(f)

            # Normalize dataset: accept either list[object] or dict[name->object]
            if isinstance(dataset, dict):
                normalized: List[Dict[str, Any]] = []
                for name, obj in dataset.items():
                    if isinstance(obj, dict):
                        merged = {"name": name}
                        merged.update(obj)
                        # Ensure a canonical name field
                        merged["name"] = merged.get("ingredient_name", merged.get("name", name))
                        normalized.append(merged)
                dataset = normalized
            elif isinstance(dataset, list):
                # Ensure name field is populated for each item
                for item in dataset:
                    if isinstance(item, dict):
                        if not item.get("name"):
                            item["name"] = item.get("ingredient_name", "Unknown")
            else:
                return json.dumps({
                    "error": "Ingredients dataset must be either a list of objects or a dict of name->object"
                }, indent=2)

            user_signals = self._extract_user_signals(profile)

            ranked: List[Dict[str, Any]] = []
            # weights
            w_sem = 0.35
            w_rule = 0.35
            w_evd = 0.10
            w_saf = 0.15

            for ing in dataset:
                ing_text = self._compose_ingredient_profile_text(ing)

                safety_pen, hard_exclude = self._safety_penalty(user_signals, ing)
                if hard_exclude:
                    continue

                s_sem = self._similarity_score(user_signals["intent_text"], ing_text)
                s_rule = self._rule_target_score(user_signals, ing)
                s_evd = self._evidence_score(ing)

                score = w_sem * s_sem + w_rule * s_rule + w_evd * s_evd - w_saf * safety_pen

                # short rationale
                rationale_bits: List[str] = []
                if s_rule > 0:
                    rationale_bits.append("matches user biomarkers/goals")
                if s_sem > 0.05:
                    rationale_bits.append("semantic fit to user needs")
                if s_evd > 0:
                    rationale_bits.append("supported by evidence")
                if safety_pen > 0:
                    rationale_bits.append("minor interaction considerations")
                rationale = ", ".join(rationale_bits) if rationale_bits else "general support"

                ranked.append({
                    "name": ing.get("name", ing.get("ingredient_name", "Unknown")),
                    "score": round(score, 4),
                    "components": {
                        "semantic": round(s_sem, 4),
                        "rule": round(s_rule, 4),
                        "evidence": round(s_evd, 4),
                        "safety_penalty": round(safety_pen, 4),
                    },
                    "why": f"{ing.get('name', 'This ingredient')} is recommended because it {rationale}.",
                })

            ranked.sort(key=lambda x: x["score"], reverse=True)

            # Return top 15 for readability
            return json.dumps({"ranked_ingredients": ranked[:15]}, indent=2)

        except Exception as e:
            return json.dumps({
                "error": f"Ingredient ranking failed: {str(e)}",
                "ranked_ingredients": []
            }, indent=2)


