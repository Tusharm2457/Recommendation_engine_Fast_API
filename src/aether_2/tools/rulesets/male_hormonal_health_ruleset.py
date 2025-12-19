"""
Male Hormonal Health focus area scoring ruleset.
"""

from typing import Dict, Optional, Tuple, List
from .constants import FOCUS_AREAS


class MaleHormonalHealthRuleset:
    """Ruleset for male hormonal health focus area scoring."""
    
    # Anabolic steroid keywords
    AAS_KEYWORDS = [
        'anabolic steroid', 'testosterone injection', 'trt', 'testosterone replacement',
        'deca', 'trenbolone', 'dianabol', 'winstrol', 'anavar', 'sustanon'
    ]
    
    # Opioid keywords (reuse from chronic pain)
    OPIOID_KEYWORDS = [
        'morphine', 'oxycodone', 'oxycontin', 'percocet', 'hydrocodone',
        'vicodin', 'norco', 'codeine', 'tramadol', 'ultram', 'fentanyl',
        'methadone', 'hydromorphone', 'dilaudid', 'oxymorphone', 'opana'
    ]
    
    # SSRI/SNRI keywords
    SSRI_SNRI_KEYWORDS = [
        'ssri', 'snri', 'fluoxetine', 'prozac', 'sertraline', 'zoloft',
        'paroxetine', 'paxil', 'citalopram', 'celexa', 'escitalopram', 'lexapro',
        'venlafaxine', 'effexor', 'duloxetine', 'cymbalta', 'desvenlafaxine', 'pristiq'
    ]
    
    # Antihypertensive keywords (thiazide, beta-blockers)
    ANTIHYPERTENSIVE_KEYWORDS = [
        'thiazide', 'hydrochlorothiazide', 'hctz', 'chlorthalidone',
        'beta blocker', 'beta-blocker', 'metoprolol', 'atenolol', 'propranolol',
        'carvedilol', 'bisoprolol', 'labetalol'
    ]
    
    def get_male_hormonal_health_weights(
        self,
        biological_sex: Optional[str] = None,
        age: Optional[int] = None,
        hormonal_concerns: Optional[str] = None,
        concern_details: Optional[str] = None,
        bmi: Optional[float] = None,
        diagnoses: Optional[str] = None,
        snoring_sleep_apnea: Optional[str] = None,
        current_medications: Optional[List[Dict]] = None,
        substance_details: Optional[str] = None,
        chemical_exposures: Optional[str] = None,
        surgeries: Optional[str] = None
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on male hormonal health.
        
        Args:
            biological_sex: User's biological sex
            age: User's age
            hormonal_concerns: "yes"/"no"/"not applicable" for hormonal concerns
            concern_details: Free text details about concerns
            bmi: Body mass index
            diagnoses: Comma-separated diagnoses string
            snoring_sleep_apnea: Sleep apnea status
            current_medications: List of medication dicts
            substance_details: Free text substance use details
            chemical_exposures: Chemical exposure status
            surgeries: Free text surgeries
            
        Returns:
            Tuple of (scores dict, descriptions list)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        descriptions = []
        
        # Check if user is male
        if not biological_sex or biological_sex.lower() != 'male':
            return (scores, descriptions)
        
        # E) Special case - Surgical/chemical hypogonadism (even if answer is "No" or "Not applicable")
        has_special_case = False
        if surgeries:
            surgeries_lower = surgeries.lower()
            if 'orchiectomy' in surgeries_lower or 'testicular removal' in surgeries_lower:
                if 'bilateral' in surgeries_lower or 'both' in surgeries_lower:
                    scores["HRM"] += 0.30
                    scores["CM"] += 0.15
                    scores["STR"] += 0.10
                    scores["MITO"] += 0.10
                    descriptions.append("Surgical hypogonadism (bilateral orchiectomy)")
                    has_special_case = True
        
        # Check for androgen-deprivation therapy
        if current_medications:
            for med in current_medications:
                med_name = med.get('name', '').lower()
                adt_keywords = ['leuprolide', 'lupron', 'goserelin', 'zoladex', 'degarelix', 'firmagon']
                if any(keyword in med_name for keyword in adt_keywords):
                    scores["HRM"] += 0.30
                    scores["CM"] += 0.15
                    scores["STR"] += 0.10
                    scores["MITO"] += 0.10
                    descriptions.append("Chemical hypogonadism (ADT)")
                    has_special_case = True
                    break
        
        # Check if hormonal_concerns is "yes"
        if not hormonal_concerns or hormonal_concerns.lower() not in ['yes', 'y']:
            # Return special case scores if any, otherwise no contribution
            return (scores, descriptions)
        
        # A) Base rule (answer = "Yes")
        scores["HRM"] += 0.45
        scores["STR"] += 0.10
        scores["CM"] += 0.10
        scores["COG"] += 0.10
        scores["MITO"] += 0.05
        descriptions.append("Has hormonal/sexual concerns")
        
        # B) Age-band modifiers
        if age:
            if 18 <= age <= 39:
                # Young adult
                scores["HRM"] += 0.10
                descriptions.append("Age 18-39 (secondary causes)")
                
                # Check for AAS/anabolic steroid use
                has_aas = False
                if substance_details:
                    substance_lower = substance_details.lower()
                    if any(keyword in substance_lower for keyword in self.AAS_KEYWORDS):
                        has_aas = True
                
                if current_medications:
                    for med in current_medications:
                        med_name = med.get('name', '').lower()
                        if any(keyword in med_name for keyword in self.AAS_KEYWORDS):
                            has_aas = True
                            break
                
                if has_aas:
                    scores["HRM"] += 0.15
                    scores["DTX"] += 0.05
                    descriptions.append("AAS/anabolic steroid use")

            elif 40 <= age <= 60:
                # Middle age (ED as vascular sentinel)
                scores["CM"] += 0.15
                scores["STR"] += 0.05
                descriptions.append("Age 40-60 (cardiovascular risk)")

            elif age > 60:
                # Older adult
                scores["CM"] += 0.10
                scores["COG"] += 0.05
                scores["MITO"] += 0.05
                descriptions.append("Age >60 (aging vasculature)")

        # C) Cross-field refiners
        # 1) Obesity/central adiposity
        if bmi and bmi > 29:
            scores["CM"] += 0.10
            scores["HRM"] += 0.05
            descriptions.append("Obesity (BMI >29)")

        # 2) Diabetes
        if diagnoses:
            diagnoses_lower = diagnoses.lower()
            if 'diabetes' in diagnoses_lower:
                scores["CM"] += 0.15
                descriptions.append("Diabetes (ED risk)")

        # 3) Obstructive sleep apnea
        if snoring_sleep_apnea and snoring_sleep_apnea.lower() in ['yes', 'y', 'not sure']:
            scores["CM"] += 0.10
            scores["HRM"] += 0.05
            scores["STR"] += 0.05
            descriptions.append("Sleep apnea (OSA)")

        # 4) Medication contributors
        if current_medications:
            # Chronic opioids
            has_chronic_opioid = False
            for med in current_medications:
                med_name = med.get('name', '').lower()
                frequency = med.get('frequency', '').lower()
                if any(keyword in med_name for keyword in self.OPIOID_KEYWORDS):
                    if 'daily' in frequency or 'chronic' in frequency:
                        has_chronic_opioid = True
                        break

            if has_chronic_opioid:
                scores["HRM"] += 0.10
                scores["STR"] += 0.05
                scores["MITO"] += 0.05
                descriptions.append("Chronic opioid use")

            # SSRIs/SNRIs
            has_ssri_snri = False
            for med in current_medications:
                med_name = med.get('name', '').lower()
                if any(keyword in med_name for keyword in self.SSRI_SNRI_KEYWORDS):
                    has_ssri_snri = True
                    break

            if has_ssri_snri:
                scores["COG"] += 0.10
                scores["HRM"] += 0.05
                descriptions.append("SSRI/SNRI use")

            # Antihypertensives (thiazide, beta-blockers)
            has_antihypertensive = False
            for med in current_medications:
                med_name = med.get('name', '').lower()
                if any(keyword in med_name for keyword in self.ANTIHYPERTENSIVE_KEYWORDS):
                    has_antihypertensive = True
                    break

            if has_antihypertensive:
                scores["STR"] += 0.05
                scores["HRM"] += 0.05
                descriptions.append("Antihypertensive use")

        # 5) Chemical/toxin exposure
        if chemical_exposures and chemical_exposures.lower() not in ['none', 'no', 'n']:
            scores["HRM"] += 0.05
            scores["DTX"] += 0.05
            descriptions.append("Chemical/toxin exposure")

        return (scores, descriptions)

