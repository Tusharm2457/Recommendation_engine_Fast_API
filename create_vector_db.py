#!/usr/bin/env python3
"""
Vector Database Creator for Ingredients
Converts transformed_ingredients.json into a vector database for RAG search
"""

import json
import os
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
import uuid

def load_ingredients(file_path: str) -> Dict[str, Any]:
    """Load ingredients from JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def create_ingredient_chunk(ingredient_name: str, ingredient_data: Dict[str, Any]) -> str:
    """Create a comprehensive text chunk for an ingredient"""
    
    # Extract key information
    core_problems = ingredient_data.get('core_health_problems', [])
    secondary_problems = ingredient_data.get('secondary_health_problems', [])
    key_actions = ingredient_data.get('key_actions', [])
    relevant_conditions = ingredient_data.get('relevant_conditions', [])
    biomarkers_mentioned = ingredient_data.get('biomarkers_mentioned', [])
    biomarker_recommendations = ingredient_data.get('biomarker_recommendations', [])
    special_cases = ingredient_data.get('special_cases', [])
    cases_when_not_recommended = ingredient_data.get('cases_when_not_recommended', [])
    lifestyle_factors = ingredient_data.get('lifestyle_factors', [])
    medicine_category = ingredient_data.get('medicine_category', [])
    chunk_text = ingredient_data.get('chunk_text', '')
    
    # Create comprehensive chunk text
    chunk_parts = [
        f"Ingredient: {ingredient_name}",
        f"Medicine Category: {', '.join(medicine_category)}",
        f"Core Health Problems: {', '.join(core_problems)}",
        f"Secondary Health Problems: {', '.join(secondary_problems)}",
        f"Key Actions: {', '.join(key_actions)}",
        f"Relevant Conditions: {', '.join(relevant_conditions)}",
        f"Biomarkers Mentioned: {', '.join(biomarkers_mentioned)}",
        f"Biomarker Recommendations: {', '.join([str(rec) for rec in biomarker_recommendations])}",
        f"Special Cases: {', '.join(special_cases)}",
        f"Cases When Not Recommended: {', '.join(cases_when_not_recommended)}",
        f"Lifestyle Factors: {', '.join(lifestyle_factors)}",
        f"Description: {chunk_text}"
    ]
    
    return "\n".join(chunk_parts)

def create_vector_database(ingredients_file: str, db_path: str = "./ingredients_vector_db"):
    """Create vector database from ingredients using ChromaDB default embeddings"""
    
    print("Loading ingredients...")
    ingredients = load_ingredients(ingredients_file)
    
    print(f"Found {len(ingredients)} ingredients")
    
    # Initialize ChromaDB with default embedding model
    print("Initializing ChromaDB with default embedding model...")
    client = chromadb.PersistentClient(path=db_path)
    
    collection = client.get_or_create_collection(
        name="ingredients",
        metadata={"description": "Vector database of supplement ingredients"}
    )
    
    # Prepare data for vector database
    documents = []
    metadatas = []
    ids = []
    
    for ingredient_name, ingredient_data in ingredients.items():
        # Create chunk
        chunk_text = create_ingredient_chunk(ingredient_name, ingredient_data)
        
        # Create metadata
        metadata = {
            "ingredient_name": ingredient_name,
            "medicine_category": ", ".join(ingredient_data.get('medicine_category', [])),
            "core_health_problems": ", ".join(ingredient_data.get('core_health_problems', [])),
            "biomarkers_mentioned": ", ".join(ingredient_data.get('biomarkers_mentioned', [])),
            "special_cases": ", ".join(ingredient_data.get('special_cases', [])),
            "cases_when_not_recommended": ", ".join(ingredient_data.get('cases_when_not_recommended', []))
        }
        
        documents.append(chunk_text)
        metadatas.append(metadata)
        ids.append(ingredient_name)  # Use ingredient name as ID to prevent duplicates
    
    # Add to collection
    print("Adding documents to vector database...")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"Successfully created vector database with {len(documents)} ingredients")
    print(f"Database saved to: {db_path}")
    
    return client, collection

def test_vector_database(collection, query: str = "cardiovascular health cholesterol"):
    """Test the vector database with a sample query"""
    print(f"\nTesting vector database with query: '{query}'")
    
    results = collection.query(
        query_texts=[query],
        n_results=3
    )
    
    print(f"Found {len(results['documents'][0])} results:")
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"\n{i+1}. {metadata['ingredient_name']}")
        print(f"   Category: {metadata['medicine_category']}")
        print(f"   Core Problems: {metadata['core_health_problems']}")
        print(f"   Biomarkers: {metadata['biomarkers_mentioned']}")
        print(f"   Relevance Score: {results['distances'][0][i]:.4f}")

if __name__ == "__main__":
    # File paths
    ingredients_file = "inputs/transformed_ingredients.json"
    db_path = "./ingredients_vector_db"
    
    # Check if ingredients file exists
    if not os.path.exists(ingredients_file):
        print(f"Error: {ingredients_file} not found!")
        exit(1)
    
    try:
        # Create vector database
        client, collection = create_vector_database(ingredients_file, db_path)
        
        # Test the database
        test_vector_database(collection, "cardiovascular health cholesterol")
        test_vector_database(collection, "stress anxiety sleep")
        test_vector_database(collection, "testosterone hormone")
        
        print("\n✅ Vector database creation completed successfully!")
        
    except Exception as e:
        print(f"❌ Error creating vector database: {str(e)}")
        exit(1)
