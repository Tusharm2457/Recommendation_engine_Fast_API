from crewai.tools import BaseTool
from typing import Type, Union, List, Dict, Any
from pydantic import BaseModel, Field
import json
import chromadb
from chromadb.config import Settings
import os
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load environment variables
load_dotenv()

class IngredientRankerRAGInput(BaseModel):
    user_profile: Union[str, dict, None] = Field(
        default=None,
        description="JSON string OR dict containing the user profile from Agent 2. If not provided, will use kickoff inputs."
    )

class IngredientRankerRAGTool(BaseTool):
    name: str = "rank_ingredients_rag"
    description: str = (
        "RAG-based ingredient ranker that searches the vector database for relevant ingredients "
        "based on the user profile (demographics, flagged biomarkers, medical history)."
    )
    args_schema: Type[BaseModel] = IngredientRankerRAGInput
    kickoff_inputs: dict = {}

    def _get_vector_db_connection(self):
        """Get connection to the existing vector database"""
        try:
            db_path = "./ingredients_vector_db"
            print(f"🔍 Connecting to vector database at: {db_path}")
            
            client = chromadb.PersistentClient(path=db_path)
            collection = client.get_collection("ingredients")
            
            print(f"✅ Connected to vector database with {collection.count()} ingredients")
            return client, collection
            
        except Exception as e:
            print(f"❌ Error connecting to vector database: {str(e)}")
            raise

    def _get_all_vector_db_data(self):
        """Get all data from vector database for hybrid search"""
        try:
            client, collection = self._get_vector_db_connection()
            
            # Get all documents, metadatas, and embeddings in one call
            results = collection.get(
                include=["documents", "metadatas", "embeddings"]
            )
            
            print(f"✅ Retrieved {len(results['documents'])} ingredients from vector database")
            return results
            
        except Exception as e:
            print(f"❌ Error getting vector database data: {str(e)}")
            return None

    def _create_search_query(self, user_profile: Dict[str, Any]) -> str:
        """Create a comprehensive search query from user profile"""
        query_parts = []
        
        # Add demographics
        demographics = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("demographics", {})
        if demographics:
            age = demographics.get("age", "")
            gender = demographics.get("gender", "")
            if age and gender:
                query_parts.append(f"{gender} age {age}")
        
        # Add flagged biomarkers
        flagged_biomarkers = user_profile.get("flagged_biomarkers", [])
        biomarker_names = []
        for biomarker in flagged_biomarkers:
            name = biomarker.get("name", "")
            category = biomarker.get("category", "")
            if name and category:
                biomarker_names.append(f"{name} {category}")
        
        if biomarker_names:
            query_parts.append(" ".join(biomarker_names))
        
        # Add medical conditions
        medical_conditions = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("medical_conditions", [])
        if medical_conditions:
            query_parts.append(" ".join(medical_conditions))
        
        # Add lifestyle factors
        lifestyle = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("lifestyle", {})
        if lifestyle:
            exercise = lifestyle.get("exercise_frequency", "")
            diet = lifestyle.get("diet_type", "")
            if exercise:
                query_parts.append(f"exercise {exercise}")
            if diet:
                query_parts.append(f"diet {diet}")
        
        # Combine all parts
        search_query = " ".join(query_parts)
        print(f"🔍 Search query: {search_query}")
        
        return search_query

    def _bm25_search_from_vector_db(self, query: str, vector_db_data: Dict, n_results: int = 30) -> List[Dict[str, Any]]:
        """Perform BM25 keyword search using vector database data"""
        try:
            if not vector_db_data or not vector_db_data.get("documents"):
                return []
            
            documents = vector_db_data["documents"]
            metadatas = vector_db_data["metadatas"]
            
            # Prepare documents and query
            all_docs = documents + [query]  # Add query as last document
            
            # Create TF-IDF vectors
            vectorizer = TfidfVectorizer(
                stop_words='english',
                lowercase=True,
                ngram_range=(1, 2),  # Use unigrams and bigrams
                max_features=1000
            )
            
            tfidf_matrix = vectorizer.fit_transform(all_docs)
            
            # Get query vector (last row)
            query_vector = tfidf_matrix[-1]
            doc_vectors = tfidf_matrix[:-1]
            
            # Calculate cosine similarities
            similarities = cosine_similarity(query_vector, doc_vectors).flatten()
            
            # Create results with BM25 scores
            bm25_results = []
            for i, similarity in enumerate(similarities):
                if similarity > 0:  # Only include ingredients with some similarity
                    bm25_results.append({
                        "ingredient_name": metadatas[i].get("ingredient_name", ""),
                        "description": documents[i],
                        "bm25_score": float(similarity),
                        "metadata": metadatas[i]
                    })
            
            # Sort by BM25 score and return top results
            bm25_results.sort(key=lambda x: x["bm25_score"], reverse=True)
            print(f"✅ BM25 search found {len(bm25_results)} relevant ingredients")
            
            return bm25_results[:n_results]
            
        except Exception as e:
            print(f"❌ Error in BM25 search: {str(e)}")
            return []

    def _search_ingredients(self, query: str, n_results: int = 20) -> List[Dict[str, Any]]:
        """Search for relevant ingredients using vector similarity"""
        try:
            # Get database connection
            client, collection = self._get_vector_db_connection()
            
            # Perform vector search
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            ingredients = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0], 
                results["distances"][0]
            )):
                ingredients.append({
                    "ingredient_name": metadata.get("ingredient_name", ""),
                    "description": doc,
                    "semantic_score": 1 - distance,  # Convert distance to similarity
                    "metadata": metadata
                })
            
            print(f"✅ Found {len(ingredients)} ingredients")
            return ingredients
            
        except Exception as e:
            print(f"❌ Error searching ingredients: {str(e)}")
            return []

    def _hybrid_search_from_vector_db(self, query: str, user_profile: Dict[str, Any], n_results: int = 15) -> List[Dict[str, Any]]:
        """Perform hybrid search using vector database data only"""
        try:
            # Get all data from vector database in one call
            vector_db_data = self._get_all_vector_db_data()
            if not vector_db_data:
                return []
            
            # Perform semantic search
            semantic_results = self._search_ingredients(query, n_results=50)
            
            # Perform BM25 search using vector database data
            bm25_results = self._bm25_search_from_vector_db(query, vector_db_data, n_results=50)
            
            # Create ingredient score dictionary
            ingredient_scores = {}
            
            # Add semantic scores
            for result in semantic_results:
                name = result["ingredient_name"]
                ingredient_scores[name] = {
                    "ingredient_name": name,
                    "description": result["description"],
                    "metadata": result["metadata"],
                    "semantic_score": result["semantic_score"],
                    "bm25_score": 0.0,
                    "biomarker_boost": 0.0,
                    "final_score": 0.0
                }
            
            # Add BM25 scores
            for result in bm25_results:
                name = result["ingredient_name"]
                if name in ingredient_scores:
                    ingredient_scores[name]["bm25_score"] = result["bm25_score"]
                else:
                    ingredient_scores[name] = {
                        "ingredient_name": name,
                        "description": result["description"],
                        "metadata": result["metadata"],
                        "semantic_score": 0.0,
                        "bm25_score": result["bm25_score"],
                        "biomarker_boost": 0.0,
                        "final_score": 0.0
                    }
            
            # Apply biomarker boosting
            flagged_biomarkers = user_profile.get("flagged_biomarkers", [])
            biomarker_names = [b.get("name", "").lower() for b in flagged_biomarkers]
            
            for name, ingredient in ingredient_scores.items():
                description = ingredient["description"].lower()
                
                # Check biomarker mentions in description
                biomarker_mentions = 0
                for biomarker in biomarker_names:
                    if biomarker in description:
                        biomarker_mentions += 1
                
                # Also check biomarker recommendations in metadata
                biomarker_recs = ingredient["metadata"].get("biomarker_recommendations", "")
                if biomarker_recs:
                    for biomarker in biomarker_names:
                        if biomarker in biomarker_recs.lower():
                            biomarker_mentions += 1
                
                # Apply biomarker boost
                if biomarker_mentions > 0:
                    boost = biomarker_mentions * 0.15  # 15% boost per biomarker mention
                    ingredient["biomarker_boost"] = boost
            
            # Calculate final hybrid scores
            # Weight: 40% semantic + 30% BM25 + 30% biomarker boost
            for ingredient in ingredient_scores.values():
                semantic_weighted = ingredient["semantic_score"] * 0.4
                bm25_weighted = ingredient["bm25_score"] * 0.3
                biomarker_weighted = ingredient["biomarker_boost"] * 0.3
                
                ingredient["final_score"] = semantic_weighted + bm25_weighted + biomarker_weighted
            
            # Convert to list and sort by final score
            hybrid_results = list(ingredient_scores.values())
            hybrid_results.sort(key=lambda x: x["final_score"], reverse=True)
            
            print(f"✅ Hybrid search completed with {len(hybrid_results)} ingredients")
            return hybrid_results[:n_results]
            
        except Exception as e:
            print(f"❌ Error in hybrid search: {str(e)}")
            return []

    def _rank_ingredients(self, ingredients: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply additional ranking based on biomarker relevance"""
        try:
            flagged_biomarkers = user_profile.get("flagged_biomarkers", [])
            biomarker_names = [b.get("name", "").lower() for b in flagged_biomarkers]
            
            # Boost scores for ingredients that mention flagged biomarkers
            for ingredient in ingredients:
                description = ingredient.get("description", "").lower()
                metadata = ingredient.get("metadata", {})
                
                # Check if ingredient description mentions any flagged biomarkers
                biomarker_mentions = 0
                for biomarker in biomarker_names:
                    if biomarker in description:
                        biomarker_mentions += 1
                
                # Boost score based on biomarker relevance
                if biomarker_mentions > 0:
                    boost = biomarker_mentions * 0.1  # 10% boost per biomarker mention
                    ingredient["similarity_score"] = min(1.0, ingredient["similarity_score"] + boost)
                    ingredient["biomarker_boost"] = boost
            
            # Sort by final score
            ingredients.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            # Update ranks
            for i, ingredient in enumerate(ingredients):
                ingredient["rank"] = i + 1
            
            return ingredients
            
        except Exception as e:
            print(f"❌ Error ranking ingredients: {str(e)}")
            return ingredients

    def _run(self, user_profile: Union[str, dict, None] = None) -> str:
        """Main RAG search and ranking function"""
        try:
            # Get user_profile from parameter or kickoff_inputs
            if user_profile is None or user_profile == "":
                user_profile = self.kickoff_inputs.get("user_profile")
                if user_profile:
                    print("ℹ️ Using user_profile from kickoff_inputs")

            if not user_profile:
                return json.dumps({"error": "user_profile not provided"}, indent=2)

            # Parse input
            if isinstance(user_profile, str):
                user_profile_parsed = json.loads(user_profile)
            else:
                user_profile_parsed = user_profile

            # Validate required fields exist
            required_fields = ["patient_data", "flagged_biomarkers"]
            for field in required_fields:
                if field not in user_profile_parsed:
                    return json.dumps({"error": f"Missing required field: {field}"}, indent=2)
            
            print(f"🔍 RAG Agent - Processing user profile")
            print(f"  - Patient data present: {'patient_data' in user_profile_parsed}")
            print(f"  - Flagged biomarkers: {len(user_profile_parsed.get('flagged_biomarkers', []))}")
            
            # Create search query
            search_query = self._create_search_query(user_profile_parsed)
            
            if not search_query.strip():
                return json.dumps([], indent=2)
            
            # Perform hybrid search (semantic + BM25 + biomarker boosting) using vector database only
            hybrid_results = self._hybrid_search_from_vector_db(search_query, user_profile_parsed, n_results=15)
            
            if not hybrid_results:
                return json.dumps([], indent=2)
            
            # Add rank numbers to final results
            for i, ingredient in enumerate(hybrid_results):
                ingredient["rank"] = i + 1
            
            # Create clean response with direct ingredient array
            response = hybrid_results
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            print(f"❌ RAG search failed: {str(e)}")
            return json.dumps([], indent=2)
