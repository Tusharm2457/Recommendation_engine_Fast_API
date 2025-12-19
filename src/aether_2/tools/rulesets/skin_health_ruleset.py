"""
Skin Health focus area scoring ruleset.
"""

from typing import Dict, Optional, Tuple, List
from .constants import FOCUS_AREAS


class SkinHealthRuleset:
    """Ruleset for skin health focus area scoring."""
    
    def get_skin_health_weights(
        self,
        has_skin_issues: bool,
        skin_condition_details: Optional[str] = None,
        diagnoses: Optional[str] = None,
        digestive_symptoms: Optional[str] = None,
        current_medications: Optional[List[str]] = None,
        diet_style: Optional[str] = None,
        chemical_exposures: Optional[str] = None,
        alcohol_frequency: Optional[str] = None
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on skin health status.
        
        Args:
            has_skin_issues: Whether patient has skin issues
            skin_condition_details: Free text description of skin conditions
            diagnoses: Comma-separated diagnoses string (for skin conditions)
            digestive_symptoms: Digestive symptoms string (for IBS/IBD detection)
            current_medications: List of current medications (for recent antibiotics)
            diet_style: Diet style string (for high-glycemic/dairy detection)
            chemical_exposures: Chemical exposures string
            alcohol_frequency: Alcohol frequency (for flush/rosacea)
            
        Returns:
            Tuple of (scores dict, descriptions list)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        descriptions = []
        
        # A) Base rule
        if not has_skin_issues:
            return (scores, descriptions)
        
        # Base adds for "Yes"
        scores["SKN"] = 0.30
        scores["IMM"] = 0.12
        scores["GA"] = 0.10
        descriptions.append("Has skin issues")
        
        # Combine all text sources for phenotype detection
        all_text = ""
        if skin_condition_details:
            all_text += skin_condition_details.lower() + " "
        if diagnoses:
            all_text += diagnoses.lower() + " "
        
        # B) Phenotype-specific adds
        # 1) Atopic dermatitis / eczema
        if any(keyword in all_text for keyword in ['atopic dermatitis', 'eczema', 'atopic']):
            scores["SKN"] += 0.10
            scores["IMM"] += 0.10
            scores["GA"] += 0.05
            descriptions.append("Atopic dermatitis/eczema")
            
            # Check for IgE-mediated food allergy (specialist-proven)
            # Note: This is a placeholder - would need specific field for proven food allergy
            # For now, we skip this overlay
        
        # 2) Psoriasis / psoriatic disease
        if any(keyword in all_text for keyword in ['psoriasis', 'psoriatic']):
            scores["IMM"] += 0.12
            scores["CM"] += 0.10
            scores["GA"] += 0.07
            descriptions.append("Psoriasis")
        
        # 3) Acne
        if 'acne' in all_text:
            scores["SKN"] += 0.08
            scores["DTX"] += 0.05
            descriptions.append("Acne")
            
            # Check for high-glycemic diet or dairy
            if diet_style:
                diet_lower = diet_style.lower()
                # High-glycemic or skim milk/dairy (not dairy-free)
                if 'dairy_free' not in diet_lower:
                    scores["GA"] += 0.05
                    scores["CM"] += 0.03
                    descriptions.append("Acne + dairy")
        
        # 4) Urticaria/hives / episodic rashes
        if any(keyword in all_text for keyword in ['urticaria', 'hives', 'rash', 'rashes']):
            scores["IMM"] += 0.10
            descriptions.append("Urticaria/hives")
            
            # Check for medication/chemical relation
            # Note: This would require temporal data - using chemical_exposures as proxy
            if chemical_exposures and chemical_exposures.lower() not in ['none', 'no', '']:
                scores["DTX"] += 0.05
        
        # 5) Fungal skin infections
        if any(keyword in all_text for keyword in ['tinea', 'candida', 'fungal', 'yeast']):
            scores["IMM"] += 0.08
            scores["DTX"] += 0.05
            scores["GA"] += 0.05
            descriptions.append("Fungal infection")
        
        # 6) Rosacea
        if 'rosacea' in all_text:
            scores["IMM"] += 0.05
            scores["GA"] += 0.03
            scores["DTX"] += 0.03
            descriptions.append("Rosacea")
        
        # 7) Autoimmune rashes
        if any(keyword in all_text for keyword in ['lupus', 'cutaneous lupus', 'autoimmune']):
            scores["IMM"] += 0.15
            scores["CM"] += 0.05
            descriptions.append("Autoimmune rash")
        
        # C) Gut-skin axis overlays
        # 1) IBS/IBD present
        has_ibs_ibd = False
        if digestive_symptoms:
            symptoms_lower = digestive_symptoms.lower()
            ibs_ibd_keywords = ['ibs', 'irritable bowel', 'ibd', 'inflammatory bowel', 'crohn', 'colitis']
            has_ibs_ibd = any(keyword in symptoms_lower for keyword in ibs_ibd_keywords)
        
        if has_ibs_ibd:
            scores["GA"] += 0.10
            descriptions.append("IBS/IBD overlay")
            
            # If psoriasis + IBD
            if 'psoriasis' in all_text or 'psoriatic' in all_text:
                scores["GA"] += 0.05
                descriptions.append("Psoriasis + IBD")
        
        # 2) Recent systemic antibiotics (≤3 mo)
        # Note: We don't have a "recent" field, so we check current_medications for antibiotics
        # This is a limitation - ideally we'd have a "recent_medications" field
        # For now, we skip this overlay
        
        # 3) Abnormal intestinal permeability
        # Note: We don't have this data in the current schema
        # Skip this overlay
        
        # D) Triggers & environment
        # 1) Clear food trigger
        # Note: We don't have a food trigger field
        # Skip this overlay
        
        # 2) Chemical/odor exposure
        if chemical_exposures and chemical_exposures.lower() not in ['none', 'no', '']:
            scores["DTX"] += 0.05
            scores["IMM"] += 0.05
            descriptions.append("Chemical exposure")
        
        # 3) Alcohol flush/rosacea flares
        if alcohol_frequency and alcohol_frequency.lower() in ['daily', 'weekly', '3_4_per_week']:
            if 'rosacea' in all_text:
                scores["DTX"] += 0.03
                scores["IMM"] += 0.03
                descriptions.append("Alcohol + rosacea")
        
        return (scores, descriptions)

