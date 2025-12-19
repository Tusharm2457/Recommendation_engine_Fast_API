"""
Female Hormonal Health focus area scoring ruleset.
"""

from typing import Dict, Optional, Tuple, List
from .constants import FOCUS_AREAS


class FemaleHormonalHealthRuleset:
    """Ruleset for female hormonal health focus area scoring."""
    
    # Hormone therapy keywords
    HRT_KEYWORDS = [
        'estrogen', 'estradiol', 'premarin', 'climara', 'vivelle', 'estrace',
        'progesterone', 'prometrium', 'provera', 'medroxyprogesterone',
        'hormone replacement', 'hrt', 'mht', 'menopausal hormone therapy',
        'birth control', 'oral contraceptive', 'contraceptive pill'
    ]
    
    # Vaginal estrogen keywords
    VAGINAL_ESTROGEN_KEYWORDS = [
        'vaginal estrogen', 'vagifem', 'estrace cream', 'premarin cream',
        'estring', 'vaginal cream', 'vaginal tablet'
    ]
    
    def get_female_hormonal_health_weights(
        self,
        biological_sex: Optional[str] = None,
        age: Optional[int] = None,
        menstrual_concerns: Optional[str] = None,
        concern_details: Optional[str] = None,
        diagnoses: Optional[str] = None,
        digestive_symptoms: Optional[str] = None,
        surgeries: Optional[str] = None,
        current_medications: Optional[List[Dict]] = None,
        skin_condition_details: Optional[str] = None
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on female hormonal health.
        
        Args:
            biological_sex: User's biological sex
            age: User's age
            menstrual_concerns: "yes"/"no" for menstrual concerns
            concern_details: Free text details about concerns
            diagnoses: Comma-separated diagnoses string
            digestive_symptoms: Comma-separated digestive symptoms
            surgeries: Free text surgeries
            current_medications: List of medication dicts
            skin_condition_details: Free text skin condition details
            
        Returns:
            Tuple of (scores dict, descriptions list)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        descriptions = []
        
        # Check if user is female
        if not biological_sex or biological_sex.lower() != 'female':
            return (scores, descriptions)
        
        # Check if menstrual_concerns is "yes"
        if not menstrual_concerns or menstrual_concerns.lower() != 'yes':
            # D) Special case - Surgical menopause (bilateral oophorectomy before 45)
            if surgeries and age and age < 45:
                surgeries_lower = surgeries.lower()
                if 'oophorectomy' in surgeries_lower or 'ovary removal' in surgeries_lower:
                    if 'bilateral' in surgeries_lower or 'both' in surgeries_lower:
                        scores["HRM"] += 0.20
                        scores["CM"] += 0.10
                        scores["STR"] += 0.10
                        scores["SKN"] += 0.05
                        descriptions.append("Surgical menopause (bilateral oophorectomy <45)")
            
            return (scores, descriptions)
        
        # A) Base case (answer = "Yes")
        scores["HRM"] = 0.45
        scores["STR"] = 0.10
        scores["COG"] = 0.10
        scores["CM"] = 0.10
        scores["MITO"] = 0.05
        scores["GA"] = 0.05
        scores["SKN"] = 0.05
        descriptions.append("Has menstrual concerns")
        
        # Check for hormone therapy side effects
        has_hrt_side_effects = False
        if current_medications and concern_details:
            concern_lower = concern_details.lower()
            for med in current_medications:
                med_name = med.get('name', '').lower()
                if any(keyword in med_name for keyword in self.HRT_KEYWORDS):
                    # Check for side effect keywords in concern details
                    side_effect_keywords = ['side effect', 'intolerance', 'reaction', 'adverse']
                    if any(keyword in concern_lower for keyword in side_effect_keywords):
                        has_hrt_side_effects = True
                        break
        
        if has_hrt_side_effects:
            scores["IMM"] += 0.05
            scores["DTX"] += 0.05
            descriptions.append("Hormone therapy side effects")
        
        # B) Age-band modifiers
        if age:
            if 18 <= age <= 39:
                # Reproductive years
                scores["HRM"] += 0.10
                descriptions.append("Reproductive years (18-39)")
                
                # PCOS suspicion
                if concern_details or diagnoses:
                    all_text = ""
                    if concern_details:
                        all_text += concern_details.lower() + " "
                    if diagnoses:
                        all_text += diagnoses.lower() + " "
                    
                    pcos_keywords = ['pcos', 'polycystic', 'irregular cycle', 'hirsutism', 'acne']
                    if any(keyword in all_text for keyword in pcos_keywords):
                        scores["CM"] += 0.10
                        scores["HRM"] += 0.05
                        descriptions.append("PCOS suspicion")

                # Heavy menstrual bleeding
                if concern_details:
                    concern_lower = concern_details.lower()
                    heavy_bleeding_keywords = ['heavy bleeding', 'heavy period', 'menorrhagia', 'excessive bleeding']
                    if any(keyword in concern_lower for keyword in heavy_bleeding_keywords):
                        scores["MITO"] += 0.10
                        scores["HRM"] += 0.05
                        descriptions.append("Heavy menstrual bleeding")

                # Thyroid disorder
                if diagnoses:
                    diagnoses_lower = diagnoses.lower()
                    thyroid_keywords = ['thyroid', 'hypothyroid', 'hyperthyroid', 'hashimoto', 'graves']
                    if any(keyword in diagnoses_lower for keyword in thyroid_keywords):
                        scores["HRM"] += 0.05
                        scores["CM"] += 0.05
                        descriptions.append("Thyroid disorder")

            elif 40 <= age <= 60:
                # Peri-menopause / early post-menopause
                scores["CM"] += 0.15
                scores["STR"] += 0.10
                scores["COG"] += 0.10
                scores["MITO"] += 0.10
                descriptions.append("Peri/early post-menopause (40-60)")

            elif age > 60:
                # Post-menopause
                scores["SKN"] += 0.10
                scores["COG"] += 0.05
                scores["CM"] += 0.10
                descriptions.append("Post-menopause (>60)")

        # C) Cross-field GI pattern refiners
        if digestive_symptoms:
            symptoms_lower = digestive_symptoms.lower()

            # Constipation in luteal phase
            if concern_details:
                concern_lower = concern_details.lower()
                if 'constipation' in symptoms_lower:
                    luteal_keywords = ['luteal', 'before period', 'premenstrual', 'pms']
                    if any(keyword in concern_lower for keyword in luteal_keywords):
                        scores["GA"] += 0.05
                        descriptions.append("Luteal phase constipation")

            # Diarrhea/cramps during menses
            if concern_details:
                concern_lower = concern_details.lower()
                if 'diarrhea' in symptoms_lower or 'cramp' in concern_lower:
                    menses_keywords = ['during period', 'during menses', 'menstrual', 'when bleeding']
                    if any(keyword in concern_lower for keyword in menses_keywords):
                        scores["GA"] += 0.05
                        scores["IMM"] += 0.05
                        descriptions.append("Menstrual diarrhea/cramps")

        # E) Protective adjustments
        # Menopausal hormone therapy (MHT) with symptom improvement
        has_mht_benefit = False
        if current_medications and concern_details:
            concern_lower = concern_details.lower()
            for med in current_medications:
                med_name = med.get('name', '').lower()
                if any(keyword in med_name for keyword in self.HRT_KEYWORDS):
                    benefit_keywords = ['improved', 'better', 'helped', 'relief', 'controlled']
                    if any(keyword in concern_lower for keyword in benefit_keywords):
                        has_mht_benefit = True
                        break

        if has_mht_benefit:
            scores["HRM"] -= 0.05
            scores["STR"] -= 0.05
            descriptions.append("MHT with symptom improvement")

        # Local vaginal estrogen for GSM
        has_vaginal_estrogen = False
        if current_medications or skin_condition_details:
            all_text = ""
            if current_medications:
                for med in current_medications:
                    all_text += med.get('name', '').lower() + " "
            if skin_condition_details:
                all_text += skin_condition_details.lower()

            if any(keyword in all_text for keyword in self.VAGINAL_ESTROGEN_KEYWORDS):
                has_vaginal_estrogen = True

        if has_vaginal_estrogen:
            scores["SKN"] -= 0.05
            descriptions.append("Vaginal estrogen for GSM")

        return (scores, descriptions)

