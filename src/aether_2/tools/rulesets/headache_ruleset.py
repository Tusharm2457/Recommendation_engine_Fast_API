"""
Headache/Migraine focus area scoring ruleset.
"""

from typing import Dict, Optional, Tuple, List
from .constants import FOCUS_AREAS


class HeadacheRuleset:
    """Ruleset for headache/migraine focus area scoring."""
    
    def get_headache_weights(
        self,
        frequent_headaches_migraines: Optional[bool] = None,
        headache_details: Optional[str] = None,
        digestive_symptoms: Optional[str] = None,
        diagnoses: Optional[str] = None,
        sleep_hours_category: Optional[str] = None,
        trouble_staying_asleep: Optional[str] = None,
        snoring_sleep_apnea: Optional[str] = None,
        biological_sex: Optional[str] = None,
        menstrual_concerns: Optional[str] = None,
        alcohol_frequency: Optional[str] = None,
        substance_details: Optional[str] = None,
        chemical_exposures: Optional[str] = None,
        mold_exposure: Optional[bool] = None
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on headache/migraine status.

        Args:
            frequent_headaches_migraines: Boolean indicating frequent headaches/migraines
            headache_details: Free text details about headaches
            digestive_symptoms: Comma-separated digestive symptoms string
            diagnoses: Comma-separated diagnoses string
            sleep_hours_category: Sleep hours category (less_than_6, 6_to_8, 8_to_10, more_than_10)
            trouble_staying_asleep: "yes"/"no" for trouble staying asleep
            snoring_sleep_apnea: "yes"/"no" for sleep apnea
            biological_sex: User's biological sex
            menstrual_concerns: "yes"/"no" for menstrual concerns (female)
            alcohol_frequency: Alcohol consumption frequency
            substance_details: Free text substance use details
            chemical_exposures: Chemical exposure status
            mold_exposure: Boolean for mold exposure

        Returns:
            Tuple of (scores dict, descriptions list)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        descriptions = []
        
        # A) Base decision
        if not frequent_headaches_migraines:
            return (scores, descriptions)
        
        # Base neuro-metabolic load
        scores["STR"] += 0.25
        scores["COG"] += 0.15
        scores["MITO"] += 0.10
        descriptions.append("Frequent headaches/migraines")
        
        # B) GI / brain-gut axis additions
        if digestive_symptoms:
            symptoms_list = [s.strip() for s in digestive_symptoms.split(',') if s.strip()]
            num_symptoms = len(symptoms_list)
            
            # Check for IBS diagnosis
            has_ibs = False
            if diagnoses:
                diagnoses_lower = diagnoses.lower()
                if 'ibs' in diagnoses_lower or 'irritable bowel' in diagnoses_lower:
                    has_ibs = True
            
            if has_ibs or num_symptoms >= 2:
                scores["GA"] += 0.15
                #descriptions.append("GI symptoms (≥2 or IBS)")
            elif num_symptoms >= 1:
                scores["GA"] += 0.10
                #descriptions.append("GI symptoms (brain-gut axis)")
        
        # C) Sleep & breathing links
        # Sleep <6h or trouble staying asleep
        short_sleep = sleep_hours_category and sleep_hours_category == "less_than_6"
        if short_sleep or (trouble_staying_asleep and trouble_staying_asleep.lower() in ['yes', 'y']):
            scores["STR"] += 0.10
            scores["COG"] += 0.05
            #descriptions.append("Sleep disruption")
        
        # OSA suspected/confirmed or loud snoring
        if snoring_sleep_apnea and snoring_sleep_apnea.lower() in ['yes', 'y', 'not sure']:
            scores["STR"] += 0.10
            scores["COG"] += 0.05
            scores["GA"] += 0.05
            #descriptions.append("Sleep apnea/snoring")
        
        # D) Hormonal considerations (female with menstrual relation)
        if biological_sex and biological_sex.lower() == 'female':
            if menstrual_concerns and menstrual_concerns.lower() in ['yes', 'y']:
                scores["HRM"] += 0.10
                scores["STR"] += 0.05
                #descriptions.append("Menstrual-related (estrogen withdrawal)")
        
        # E) Triggers & lifestyle interactions
        # Alcohol
        if alcohol_frequency:
            alcohol_lower = alcohol_frequency.lower()
            if 'daily' in alcohol_lower or 'every day' in alcohol_lower:
                scores["STR"] += 0.05
                scores["GA"] += 0.05
                #descriptions.append("Daily alcohol consumption")
                
                # Check for red wine or binge drinking
                if substance_details:
                    substance_lower = substance_details.lower()
                    if 'red wine' in substance_lower or 'binge' in substance_lower:
                        scores["STR"] += 0.05
                        scores["GA"] += 0.05
                       # descriptions.append("Red wine/binge drinking")
        
        # Chemical/odor sensitivity
        if chemical_exposures and chemical_exposures.lower() not in ['none', 'no', 'n']:
            scores["COG"] += 0.05
            scores["IMM"] += 0.05
            scores["DTX"] += 0.05
            #descriptions.append("Chemical/odor sensitivity")
        
        # Mold/water-damage history
        if mold_exposure:
            scores["IMM"] += 0.05
            scores["COG"] += 0.05
            #descriptions.append("Mold exposure")
        
        return (scores, descriptions)

