from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, conint, confloat, conlist

class IngredientRecommendation(BaseModel):
    ingredient_name: str = Field(..., description="Exact ingredient name")
    recommended_dosage: str = Field(..., description="Clinical dosage with proper units (mg, mcg, IU, etc.)")
    frequency: str = Field(..., description="Optimal timing and frequency")
    focus_area: List[str] = Field(..., description="List of 1-2 most relevant focus area codes")
    why: str = Field(..., description="Patient-specific reasoning for the recommendation")

class SupplementRecommendation(BaseModel):
    ingredient_name: str = Field(..., description="Exact ingredient name")
    rank: int = Field(..., description="Clinical priority rank (1-10)")
    why: str = Field(..., description="Concise 1-2 line explanation of why this ingredient is necessary for this specific patient")

class SupplementRecommendations(BaseModel):
    final_recommendations: List[SupplementRecommendation] = Field(..., description="List of final supplement recommendations ranked by clinical priority")

class FinalSupplementProtocol(BaseModel):
    supplement_recommendations: List[IngredientRecommendation] = Field(..., description="Complete list of supplement recommendations with dosages and protocols")

class FlaggedBiomarker(BaseModel):
    name: str
    value: float
    unit: str
    category: str

class CategorySummary(BaseModel):
    healthy_markers: int
    low_markers: int
    high_markers: int

class Summary(BaseModel):
    total_biomarkers_evaluated: int
    total_flagged: int
    high_priority_issues: int
    category_summary: CategorySummary

class UserProfile(BaseModel):
    patient_data: Dict[str, Any]  # flexible structure with proper typing
    flagged_biomarkers: List[FlaggedBiomarker]
    summary: Summary

class FocusAreaScores(BaseModel):
    CM: float = Field(..., description="Cardiometabolic & Metabolic Health")
    STR: float = Field(..., description="Stress-Axis & Nervous System Resilience")
    HRM: float = Field(..., description="Hormonal Health (Transport)")
    IMM: float = Field(..., description="Immune Function & Inflammation")
    SKN: float = Field(..., description="Skin & Barrier Function")
    COG: float = Field(..., description="Cognitive & Mental Health")
    MITO: float = Field(..., description="Mitochondrial & Energy Metabolism")
    DTX: float = Field(..., description="Detoxification & Biotransformation")
    GA: float = Field(..., description="Gut Health and Assimilation")
    
class RankedIngredient(BaseModel):
    ingredient_name: str = Field(..., description="Name of the ingredient")
    description: str = Field(..., description="Detailed description or summary of the ingredient")
    semantic_score: confloat(ge=0.0, le=1.0) = Field(..., description="Semantic similarity score (0–1 scale)")
    bm25_score: float = Field(..., description="BM25 relevance score from document retrieval")
    biomarker_boost: confloat(ge=0.0, le=1.0) = Field(..., description="Additional boost based on biomarker match")
    final_score: float = Field(..., description="Final combined ranking score after weighting")
    rank: conint(ge=1) = Field(..., description="Rank position in the ordered list")

class RankedIngredientsResponse(BaseModel):
    ranked_ingredients: List[RankedIngredient]
