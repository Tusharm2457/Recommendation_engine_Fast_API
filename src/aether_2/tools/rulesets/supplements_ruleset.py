"""
Supplements/Medications to health domain mapping ruleset.

This module implements evidence-based mappings from prescription medications and supplements
to health focus areas, including drug-nutrient interactions and functional medicine considerations.
"""

from typing import Dict, List, Tuple


class SupplementsRuleset:
    """
    Handles medication/supplement-based adjustments to health focus areas.
    
    Implements comprehensive medication-to-domain mapping with:
    - Base weights by medication category (PPI, antibiotics, metformin, etc.)
    - Drug-nutrient interaction considerations
    - Functional medicine guardrails and tradeoffs
    """
    
    FOCUS_AREAS = {
        "CM": "Cardiometabolic & Metabolic Health",
        "COG": "Cognitive & Mental Health",
        "DTX": "Detoxification & Biotransformation",
        "IMM": "Immune Function & Inflammation",
        "MITO": "Mitochondrial & Energy Metabolism",
        "SKN": "Skin & Barrier Function",
        "STR": "Stress-Axis & Nervous System Resilience",
        "HRM": "Hormonal Health (Transport)",
        "GA": "Gut Health and assimilation",
    }
    
    # Medication category keywords for classification
    PPI_KEYWORDS = ["omeprazole", "esomeprazole", "lansoprazole", "pantoprazole", "rabeprazole", "ppi", "proton pump inhibitor"]
    H2_BLOCKER_KEYWORDS = ["famotidine", "ranitidine", "cimetidine", "nizatidine", "h2 blocker", "h2ra"]
    ANTIBIOTIC_KEYWORDS = ["antibiotic", "amoxicillin", "azithromycin", "ciprofloxacin", "doxycycline", "penicillin", "cephalexin", "clindamycin", "metronidazole"]
    METFORMIN_KEYWORDS = ["metformin", "glucophage", "fortamet", "glumetza"]
    OPIOID_KEYWORDS = ["morphine", "oxycodone", "hydrocodone", "fentanyl", "tramadol", "codeine", "opioid", "narcotic"]
    NSAID_KEYWORDS = ["ibuprofen", "naproxen", "aspirin", "diclofenac", "celecoxib", "nsaid", "anti-inflammatory"]
    BILE_ACID_SEQUESTRANT_KEYWORDS = ["cholestyramine", "colesevelam", "colestipol", "bile acid sequestrant"]
    STATIN_KEYWORDS = ["atorvastatin", "simvastatin", "rosuvastatin", "pravastatin", "lovastatin", "statin", "lipitor", "zocor", "crestor"]
    SSRI_SNRI_KEYWORDS = ["sertraline", "fluoxetine", "paroxetine", "citalopram", "escitalopram", "venlafaxine", "duloxetine", "ssri", "snri", "antidepressant"]
    BENZODIAZEPINE_KEYWORDS = ["lorazepam", "diazepam", "alprazolam", "clonazepam", "temazepam", "benzodiazepine", "benzo"]
    ANTICHOLINERGIC_KEYWORDS = ["diphenhydramine", "scopolamine", "oxybutynin", "tolterodine", "anticholinergic"]
    GLP1_AGONIST_KEYWORDS = ["semaglutide", "tirzepatide", "liraglutide", "dulaglutide", "glp-1", "ozempic", "wegovy", "mounjaro"]
    SGLT2_INHIBITOR_KEYWORDS = ["empagliflozin", "canagliflozin", "dapagliflozin", "sglt2", "jardiance", "invokana", "farxiga"]
    CORTICOSTEROID_KEYWORDS = ["prednisone", "methylprednisolone", "dexamethasone", "hydrocortisone", "corticosteroid", "steroid"]
    ESTROGEN_KEYWORDS = ["estradiol", "estrogen", "birth control", "oral contraceptive", "hrt", "hormone replacement"]
    THYROID_KEYWORDS = ["levothyroxine", "synthroid", "levoxyl", "thyroid", "t4"]
    ACE_INHIBITOR_KEYWORDS = ["lisinopril", "enalapril", "ramipril", "captopril", "ace inhibitor"]
    DIURETIC_KEYWORDS = ["hydrochlorothiazide", "furosemide", "spironolactone", "diuretic", "hctz", "lasix"]
    BETA_BLOCKER_KEYWORDS = ["metoprolol", "atenolol", "propranolol", "carvedilol", "beta blocker"]
    
    def get_supplement_medication_weights(self, supplements_data: List[Dict], medications: List[str] = None) -> Dict[str, float]:
        """
        Calculate medication/supplement-based weights for health focus areas.
        
        Args:
            supplements_data: List of supplement dictionaries with 'name', 'dose', 'frequency', 'purpose'
            medications: List of medication names (from separate medications field)
            
        Returns:
            Dictionary mapping focus area codes to weight adjustments
        """
        weights = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        # Combine supplements and medications for analysis
        all_medications = []
        
        # Extract medication names from supplements data
        if supplements_data:
            for supplement in supplements_data:
                name = supplement.get("name", "").lower()
                purpose = supplement.get("purpose", "").lower()
                all_medications.append(name)
        
        # Add separate medications list if provided
        if medications:
            all_medications.extend([med.lower() for med in medications])
        
        # Remove duplicates and empty strings
        all_medications = list(set([med for med in all_medications if med.strip()]))
        
        # Apply medication-specific rules
        for medication in all_medications:
            med_weights = self._get_medication_weights(medication)
            for code, weight in med_weights.items():
                weights[code] += weight
        
        # Apply interaction modifiers
        interaction_modifiers = self._get_interaction_modifiers(all_medications)
        for code, modifier in interaction_modifiers.items():
            weights[code] += modifier
        
        # Clamp weights at 1.0 to avoid over-weighting
        for code in weights:
            weights[code] = min(weights[code], 1.0)
        
        return weights
    
    def _get_medication_weights(self, medication: str) -> Dict[str, float]:
        """Get base weights for specific medication."""
        weights = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        med_lower = medication.lower()
        
        # 1) Acid suppression
        if any(keyword in med_lower for keyword in self.PPI_KEYWORDS):
            weights["GA"] += 0.30  # hypochlorhydria → dysbiosis/SIBO/C. diff
            weights["DTX"] += 0.10  # nutrient/B12 reduction
            weights["IMM"] += 0.10  # infection susceptibility
            
        elif any(keyword in med_lower for keyword in self.H2_BLOCKER_KEYWORDS):
            weights["GA"] += 0.10  # weaker acid suppression
            weights["DTX"] += 0.05  # B12 association if long-term
        
        # 2) Antibiotics
        elif any(keyword in med_lower for keyword in self.ANTIBIOTIC_KEYWORDS):
            weights["GA"] += 0.30  # microbiome disruption/C. diff susceptibility
        
        # 3) Metformin
        elif any(keyword in med_lower for keyword in self.METFORMIN_KEYWORDS):
            weights["GA"] += 0.20  # dose-dependent diarrhea
        
        # 4) Opioids
        elif any(keyword in med_lower for keyword in self.OPIOID_KEYWORDS):
            weights["GA"] += 0.25  # constipation, motility
        
        # 5) NSAIDs
        elif any(keyword in med_lower for keyword in self.NSAID_KEYWORDS):
            weights["GA"] += 0.15  # ulcer/mucosal injury/leakiness
        
        # 6) Bile-acid sequestrants
        elif any(keyword in med_lower for keyword in self.BILE_ACID_SEQUESTRANT_KEYWORDS):
            weights["GA"] += 0.20  # fat-soluble vitamin malabsorption
            weights["DTX"] += 0.10  # nutrient-handling burden
        
        # 7) Statins
        elif any(keyword in med_lower for keyword in self.STATIN_KEYWORDS):
            weights["CM"] += 0.20  # cardiometabolic axis context
            weights["MITO"] += 0.10  # lower circulating CoQ10 levels
        
        # 8) SSRIs/SNRIs
        elif any(keyword in med_lower for keyword in self.SSRI_SNRI_KEYWORDS):
            weights["COG"] += 0.10  # mood/anxiety modulation
            weights["STR"] += 0.10  # HPA-axis modulation
        
        # 9) Benzodiazepines
        elif any(keyword in med_lower for keyword in self.BENZODIAZEPINE_KEYWORDS):
            weights["COG"] += 0.15  # cognitive effects/sedation
            weights["STR"] += 0.10  # older adults higher risk
        
        # 10) Anticholinergics
        elif any(keyword in med_lower for keyword in self.ANTICHOLINERGIC_KEYWORDS):
            weights["GA"] += 0.15  # constipation/ileus
            weights["COG"] += 0.10  # anticholinergic burden
        
        # 11) GLP-1 receptor agonists
        elif any(keyword in med_lower for keyword in self.GLP1_AGONIST_KEYWORDS):
            weights["GA"] += 0.20  # nausea, delayed gastric emptying
            weights["CM"] -= 0.10  # beneficial metabolic effect offset
        
        # 12) SGLT2 inhibitors
        elif any(keyword in med_lower for keyword in self.SGLT2_INHIBITOR_KEYWORDS):
            weights["IMM"] += 0.05  # mycotic infections
            weights["CM"] -= 0.10  # cardiometabolic/renal benefit context
        
        # 13) Systemic corticosteroids
        elif any(keyword in med_lower for keyword in self.CORTICOSTEROID_KEYWORDS):
            weights["IMM"] += 0.15  # immune suppression
            weights["CM"] += 0.10  # glycemic effects
            weights["SKN"] += 0.05  # skin effects
        
        # 14) Estrogen-containing medications
        elif any(keyword in med_lower for keyword in self.ESTROGEN_KEYWORDS):
            weights["DTX"] += 0.10  # hepatic handling
            weights["CM"] += 0.05  # VTE vigilance
            weights["GA"] += 0.05  # cholestasis signal
        
        # 15) Thyroid hormone
        elif any(keyword in med_lower for keyword in self.THYROID_KEYWORDS):
            weights["HRM"] += 0.15  # active hormonal management
        
        # 16) CV agents
        elif any(keyword in med_lower for keyword in self.ACE_INHIBITOR_KEYWORDS):
            weights["STR"] += 0.05  # cough/fatigue can stress sleep
            
        elif any(keyword in med_lower for keyword in self.DIURETIC_KEYWORDS):
            weights["MITO"] += 0.05  # electrolyte handling
            weights["DTX"] += 0.05  # K+/Mg2+ losses
            
        elif any(keyword in med_lower for keyword in self.BETA_BLOCKER_KEYWORDS):
            weights["STR"] += 0.05  # fatigue/exercise tolerance
            weights["CM"] += 0.10  # BP benefit
        
        return weights
    
    def _get_interaction_modifiers(self, medications: List[str]) -> Dict[str, float]:
        """Get interaction modifiers for medication combinations."""
        modifiers = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        meds_lower = [med.lower() for med in medications]
        
        # PPI + Antibiotics interaction
        has_ppi = any(any(ppi in med for ppi in self.PPI_KEYWORDS) for med in meds_lower)
        has_antibiotic = any(any(abx in med for abx in self.ANTIBIOTIC_KEYWORDS) for med in meds_lower)
        
        if has_ppi and has_antibiotic:
            modifiers["GA"] += 0.05  # additional GA burden from PPI + antibiotic combo
        
        # PPI + Metformin interaction (B12 monitoring)
        has_metformin = any(any(met in med for met in self.METFORMIN_KEYWORDS) for med in meds_lower)
        
        if has_ppi and has_metformin:
            modifiers["DTX"] += 0.05  # synergistic B12 deficiency risk
        
        # Multiple medications burden
        if len(medications) > 5:
            modifiers["DTX"] += 0.05  # polypharmacy burden
            modifiers["GA"] += 0.05  # increased GI burden
        
        return modifiers
    
    def get_explainability_trace(self, supplements_data: List[Dict], medications: List[str] = None) -> List[str]:
        """
        Generate human-readable explanations for medication mappings.
        
        Args:
            supplements_data: List of supplement dictionaries
            medications: List of medication names
            
        Returns:
            List of explanation strings
        """
        explanations = []
        
        # Combine all medications
        all_medications = []
        if supplements_data:
            for supplement in supplements_data:
                name = supplement.get("name", "")
                if name:
                    all_medications.append(name.lower())
        
        if medications:
            all_medications.extend([med.lower() for med in medications])
        
        all_medications = list(set([med for med in all_medications if med.strip()]))
        
        for medication in all_medications:
            med_lower = medication.lower()
            
            # Generate explanations based on medication type
            if any(keyword in med_lower for keyword in self.PPI_KEYWORDS):
                explanations.append(f"PPI ({medication}) → GA↑ DTX↑ IMM↑ (hypochlorhydria, B12, infection risk)")
                
            elif any(keyword in med_lower for keyword in self.ANTIBIOTIC_KEYWORDS):
                explanations.append(f"Antibiotic ({medication}) → GA↑ (microbiome disruption)")
                
            elif any(keyword in med_lower for keyword in self.METFORMIN_KEYWORDS):
                explanations.append(f"Metformin ({medication}) → GA↑ (GI effects)")
                
            elif any(keyword in med_lower for keyword in self.STATIN_KEYWORDS):
                explanations.append(f"Statin ({medication}) → CM↑ MITO↑ (cardiometabolic, CoQ10)")
                
            elif any(keyword in med_lower for keyword in self.SSRI_SNRI_KEYWORDS):
                explanations.append(f"SSRI/SNRI ({medication}) → COG↑ STR↑ (mood, HPA-axis)")
                
            elif any(keyword in med_lower for keyword in self.GLP1_AGONIST_KEYWORDS):
                explanations.append(f"GLP-1 agonist ({medication}) → GA↑ CM↓ (GI effects, metabolic benefit)")
                
            elif any(keyword in med_lower for keyword in self.OPIOID_KEYWORDS):
                explanations.append(f"Opioid ({medication}) → GA↑ (constipation, motility)")
                
            elif any(keyword in med_lower for keyword in self.NSAID_KEYWORDS):
                explanations.append(f"NSAID ({medication}) → GA↑ (mucosal injury)")
                
            elif any(keyword in med_lower for keyword in self.THYROID_KEYWORDS):
                explanations.append(f"Thyroid hormone ({medication}) → HRM↑ (hormonal management)")
                
            elif any(keyword in med_lower for keyword in self.ESTROGEN_KEYWORDS):
                explanations.append(f"Estrogen ({medication}) → DTX↑ CM↑ GA↑ (hepatic, VTE, cholestasis)")
        
        return explanations
