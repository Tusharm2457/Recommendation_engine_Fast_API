"""
Current medications-based focus area scoring ruleset.
"""

from typing import Dict, List, Tuple
from .constants import FOCUS_AREAS


class MedicationsRuleset:
    """Ruleset for current medications-based focus area scoring."""
    
    def get_medications_weights(
        self,
        current_medications: List[Dict]
    ) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
        """
        Calculate focus area weights based on current medications.
        
        Args:
            current_medications: List of medication objects with 'name', 'dosage', 'frequency', 'purpose'
            
        Returns:
            Tuple of:
                - Cumulative scores dict (all medications combined, clamped at [0.0, 1.0])
                - Per-medication breakdown dict {med_name: {focus_area: score}}
        """
        # Early exit if no medications
        if not current_medications:
            return ({code: 0.0 for code in FOCUS_AREAS}, {})
        
        cumulative_scores = {code: 0.0 for code in FOCUS_AREAS}
        per_medication_breakdown = {}
        
        # Track drug types for cross-medication interactions
        has_ppi = False
        has_antibiotics = False
        
        # Process each medication
        for med in current_medications:
            med_name = med.get("name", "")
            if not med_name:
                continue
            
            # Classify and score
            med_type = self._classify_medication(med_name)
            
            # Skip unknown medications
            if med_type == "unknown":
                continue
            
            med_scores = self._score_single_medication(med_type, med.get("frequency", ""))
            
            # Track for interactions
            if med_type == "ppi":
                has_ppi = True
            if med_type == "antibiotic":
                has_antibiotics = True
            
            # Add to cumulative
            for code in FOCUS_AREAS:
                cumulative_scores[code] += med_scores[code]
            
            # Store per-medication breakdown (use original name)
            per_medication_breakdown[med_name] = med_scores
        
        # Apply cross-medication modifiers (not tracked separately)
        if has_ppi and has_antibiotics:
            cumulative_scores["GA"] += 0.05  # Rule 1 add-on: concurrent PPI + antibiotics
        
        # Clamp each focus area at [0.0, 1.0] (handle negative weights)
        for code in FOCUS_AREAS:
            cumulative_scores[code] = max(0.0, min(cumulative_scores[code], 1.0))
        
        return (cumulative_scores, per_medication_breakdown)
    
    def _classify_medication(self, med_name: str) -> str:
        """
        Classify medication into drug type using keyword matching.
        
        Returns:
            Drug type: 'ppi', 'h2_blocker', 'antibiotic', 'metformin', 'opioid', 
                       'nsaid', 'bile_sequestrant', 'statin', 'ssri_snri', 
                       'benzodiazepine', 'anticholinergic', 'glp1', 'sglt2', 
                       'corticosteroid', 'estrogen', 'thyroid', 'ace_inhibitor', 
                       'diuretic', 'beta_blocker', 'unknown'
        """
        med_lower = med_name.lower()
        
        # 1. PPIs (Proton-pump inhibitors)
        if any(keyword in med_lower for keyword in ["omeprazole", "esomeprazole", "lansoprazole", "pantoprazole", "rabeprazole", "dexlansoprazole", "ppi", "prilosec", "nexium", "prevacid", "protonix"]):
            return "ppi"
        
        # 2. H2 blockers
        if any(keyword in med_lower for keyword in ["famotidine", "ranitidine", "cimetidine", "nizatidine", "pepcid", "zantac", "tagamet"]):
            return "h2_blocker"
        
        # 3. Antibiotics (common classes)
        if any(keyword in med_lower for keyword in [
            "cillin", "mycin", "cycline", "floxacin", "sulfa", "cephalexin", "cefdinir", "ceftriaxone",
            "amoxicillin", "azithromycin", "doxycycline", "ciprofloxacin", "levofloxacin", "metronidazole",
            "clindamycin", "trimethoprim", "antibiotic", "bactrim", "augmentin", "z-pack", "zithromax"
        ]):
            return "antibiotic"
        
        # 4. Metformin
        if "metformin" in med_lower or "glucophage" in med_lower:
            return "metformin"
        
        # 5. Opioids
        if any(keyword in med_lower for keyword in [
            "oxycodone", "hydrocodone", "morphine", "fentanyl", "tramadol", "codeine", "hydromorphone",
            "oxycontin", "percocet", "vicodin", "norco", "dilaudid", "opiate", "opioid"
        ]):
            return "opioid"
        
        # 6. NSAIDs
        if any(keyword in med_lower for keyword in [
            "ibuprofen", "naproxen", "diclofenac", "celecoxib", "indomethacin", "ketorolac", "meloxicam",
            "advil", "motrin", "aleve", "celebrex", "voltaren", "nsaid"
        ]):
            return "nsaid"
        
        # 7. Bile-acid sequestrants
        if any(keyword in med_lower for keyword in ["cholestyramine", "colesevelam", "colestipol", "questran", "welchol"]):
            return "bile_sequestrant"
        
        # 8. Statins
        if any(keyword in med_lower for keyword in [
            "statin", "atorvastatin", "simvastatin", "rosuvastatin", "pravastatin", "lovastatin", "fluvastatin", "pitavastatin",
            "lipitor", "zocor", "crestor", "pravachol", "mevacor"
        ]):
            return "statin"
        
        # 9. SSRIs/SNRIs
        if any(keyword in med_lower for keyword in [
            "ssri", "snri", "fluoxetine", "sertraline", "paroxetine", "citalopram", "escitalopram", "venlafaxine", "duloxetine", "desvenlafaxine",
            "prozac", "zoloft", "paxil", "celexa", "lexapro", "effexor", "cymbalta", "pristiq"
        ]):
            return "ssri_snri"
        
        # 10. Benzodiazepines
        if any(keyword in med_lower for keyword in [
            "benzodiazepine", "alprazolam", "lorazepam", "clonazepam", "diazepam", "temazepam", "triazolam",
            "xanax", "ativan", "klonopin", "valium", "restoril"
        ]):
            return "benzodiazepine"

        # 11. Anticholinergics (strong burden)
        if any(keyword in med_lower for keyword in [
            "diphenhydramine", "hydroxyzine", "oxybutynin", "tolterodine", "solifenacin", "trospium",
            "benadryl", "vistaril", "ditropan", "detrol", "vesicare", "anticholinergic"
        ]):
            return "anticholinergic"

        # 12. GLP-1 receptor agonists
        if any(keyword in med_lower for keyword in [
            "glp-1", "glp1", "semaglutide", "tirzepatide", "liraglutide", "dulaglutide", "exenatide",
            "ozempic", "wegovy", "mounjaro", "victoza", "saxenda", "trulicity", "byetta", "bydureon"
        ]):
            return "glp1"

        # 13. SGLT2 inhibitors
        if any(keyword in med_lower for keyword in [
            "sglt2", "sglt-2", "empagliflozin", "dapagliflozin", "canagliflozin", "ertugliflozin",
            "jardiance", "farxiga", "invokana", "steglatro"
        ]):
            return "sglt2"

        # 14. Systemic corticosteroids
        if any(keyword in med_lower for keyword in [
            "prednisone", "prednisolone", "methylprednisolone", "dexamethasone", "hydrocortisone", "cortisone",
            "corticosteroid", "steroid", "medrol", "decadron", "deltasone"
        ]):
            return "corticosteroid"

        # 15. Estrogen-containing (oral contraception/HRT)
        if any(keyword in med_lower for keyword in [
            "estrogen", "estradiol", "ethinyl estradiol", "conjugated estrogen", "birth control", "oral contraceptive",
            "premarin", "climara", "vivelle", "estrace", "yaz", "yasmin", "ortho", "lo loestrin", "nuvaring"
        ]):
            return "estrogen"

        # 16. Thyroid hormone
        if any(keyword in med_lower for keyword in [
            "levothyroxine", "liothyronine", "thyroid", "synthroid", "levoxyl", "cytomel", "armour thyroid", "nature-throid"
        ]):
            return "thyroid"

        # 17. ACE inhibitors
        if any(keyword in med_lower for keyword in [
            "ace inhibitor", "pril", "lisinopril", "enalapril", "ramipril", "benazepril", "captopril", "quinapril",
            "prinivil", "zestril", "vasotec", "altace", "lotensin", "accupril"
        ]):
            return "ace_inhibitor"

        # 18. Diuretics (thiazide/loop)
        if any(keyword in med_lower for keyword in [
            "diuretic", "hydrochlorothiazide", "chlorthalidone", "furosemide", "bumetanide", "torsemide", "spironolactone",
            "hctz", "lasix", "bumex", "demadex", "aldactone"
        ]):
            return "diuretic"

        # 19. Beta-blockers
        if any(keyword in med_lower for keyword in [
            "beta blocker", "beta-blocker", "olol", "metoprolol", "atenolol", "carvedilol", "propranolol", "bisoprolol", "labetalol",
            "lopressor", "toprol", "tenormin", "coreg", "inderal", "zebeta"
        ]):
            return "beta_blocker"

        return "unknown"

    def _score_single_medication(self, med_type: str, frequency: str) -> Dict[str, float]:
        """Score a single medication based on type and frequency."""
        scores = {code: 0.0 for code in FOCUS_AREAS}

        # 1. PPIs
        if med_type == "ppi":
            scores["GA"] += 0.30
            scores["DTX"] += 0.10
            scores["IMM"] += 0.10

        # 2. H2 blockers
        elif med_type == "h2_blocker":
            scores["GA"] += 0.10
            scores["DTX"] += 0.05

        # 3. Antibiotics
        elif med_type == "antibiotic":
            scores["GA"] += 0.30

        # 4. Metformin
        elif med_type == "metformin":
            scores["GA"] += 0.20

        # 5. Opioids
        elif med_type == "opioid":
            scores["GA"] += 0.25

        # 6. NSAIDs (check frequency for "regular use")
        elif med_type == "nsaid":
            if frequency and any(keyword in frequency.lower() for keyword in ["daily", "regular", "twice", "three times", "2x", "3x"]):
                scores["GA"] += 0.15
            else:
                scores["GA"] += 0.10  # Conservative default

        # 7. Bile-acid sequestrants
        elif med_type == "bile_sequestrant":
            scores["GA"] += 0.20
            scores["DTX"] += 0.10

        # 8. Statins
        elif med_type == "statin":
            scores["CM"] += 0.20
            scores["MITO"] += 0.10

        # 9. SSRIs/SNRIs
        elif med_type == "ssri_snri":
            scores["COG"] += 0.10
            scores["STR"] += 0.10

        # 10. Benzodiazepines
        elif med_type == "benzodiazepine":
            scores["COG"] += 0.15
            scores["STR"] += 0.10

        # 11. Anticholinergics
        elif med_type == "anticholinergic":
            scores["GA"] += 0.15
            scores["COG"] += 0.10

        # 12. GLP-1 receptor agonists
        elif med_type == "glp1":
            scores["GA"] += 0.20
            scores["CM"] -= 0.10  # Beneficial metabolic effect (negative weight)

        # 13. SGLT2 inhibitors
        elif med_type == "sglt2":
            scores["IMM"] += 0.05
            scores["CM"] -= 0.10  # Cardiometabolic benefit (negative weight)

        # 14. Systemic corticosteroids
        elif med_type == "corticosteroid":
            scores["IMM"] += 0.15
            scores["CM"] += 0.10
            scores["SKN"] += 0.05

        # 15. Estrogen-containing
        elif med_type == "estrogen":
            scores["DTX"] += 0.10
            scores["CM"] += 0.05
            scores["GA"] += 0.05

        # 16. Thyroid hormone
        elif med_type == "thyroid":
            scores["HRM"] += 0.15

        # 17. ACE inhibitors
        elif med_type == "ace_inhibitor":
            scores["STR"] += 0.05

        # 18. Diuretics
        elif med_type == "diuretic":
            scores["MITO"] += 0.05
            scores["DTX"] += 0.05

        # 19. Beta-blockers
        elif med_type == "beta_blocker":
            scores["STR"] += 0.05
            scores["CM"] += 0.10

        return scores

