from crewai import Agent, Crew, Process, Task, LLM
from crewai.tasks.conditional_task import ConditionalTask
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.tasks.task_output import TaskOutput
#from crewai_tools import SerperDevTool
from typing import List, Dict, Optional, Any
from pydantic import BaseModel,Field,conint, confloat, conlist
from src.aether_2.models import (
    IngredientRecommendation, SupplementRecommendation, SupplementRecommendations,
    FinalSupplementProtocol, FlaggedBiomarker, CategorySummary, Summary,
    UserProfile, FocusAreaScores, RankedIngredient, RankedIngredientsResponse
)
from src.aether_2.tools.web_ingredient_discovery import WebIngredientDiscoveryTool
from src.aether_2.tools.ingredient_ranker_rag import IngredientRankerRAGTool
#from src.aether_2.tools.google_search_validator import GoogleSearchValidatorTool
from src.aether_2.tools.ingredient_ranker import IngredientRankerTool
from src.aether_2.tools.supplement_recommender import SupplementRecommendationTool
from src.aether_2.tools.final_supplement_compiler import FinalSupplementCompilerTool

 
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators
llm = LLM(
    model="vertex_ai/gemini-2.5-flash",
    #base_url="http://localhost:11434",
    temperature=0,
    seed=42
)
@CrewBase
class Aether2():
    """Aether2 crew"""
    agents: List[BaseAgent]
    tasks: List[Task]
    kickoff_inputs: dict = {}  # Class variable for tools to access

    # @agent
    # def summarizer(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['summarizer'],  # type: ignore[index]
    #         verbose=True
    #     )
    #
    # @agent
    # def clinical_reasoner(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['clinical_reasoner'],  # type: ignore[index]
    #         verbose=True,
    #         tools=[BiomarkerKnowledgeTool()]
    #     )

    @agent
    def web_ingredient_discovery(self) -> Agent:
        return Agent(
            config=self.agents_config['web_ingredient_discovery'],
            verbose=True,
            tools=[WebIngredientDiscoveryTool(kickoff_inputs=self.kickoff_inputs)],
            llm=llm
        )

    # Temporarily disabled for testing
    @agent
    def ingredient_ranker_rag(self) -> Agent:
        return Agent(
            config=self.agents_config['ingredient_ranker_rag'],
            verbose=True,
            tools=[IngredientRankerRAGTool(kickoff_inputs=self.kickoff_inputs)],
            llm=llm
        )

    # @agent
    # def google_search_validator(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['google_search_validator'],
    #         verbose=True,
    #         tools=[GoogleSearchValidatorTool()]
    #     )

    # @agent
    # def ingredient_ranker(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['ingredient_ranker'],
    #         verbose=True,
    #         tools=[IngredientRankerTool()]
    #     )
    
    @agent
    def supplement_recommender(self) -> Agent:
        return Agent(
            config=self.agents_config['supplement_recommender'],
            verbose=True,
            tools=[SupplementRecommendationTool(kickoff_inputs=self.kickoff_inputs)],
            llm=llm
        )

    @agent
    def final_supplement_compiler(self) -> Agent:
        return Agent(
            config=self.agents_config['final_supplement_compiler'],
            verbose=True,
            tools=[FinalSupplementCompilerTool(kickoff_inputs=self.kickoff_inputs)],
            llm=llm
        )

    
   

    @task
    def discover_ingredients_web(self) -> Task:
        return Task(
            config=self.tasks_config['discover_ingredients_web']
        )

    @task
    def rank_ingredients_rag(self) -> Task:
        return Task(
            config=self.tasks_config['rank_ingredients_rag'],
            output_pydantic=RankedIngredientsResponse
        )

    # @task
    # def validate_ingredients_google(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['validate_ingredients_google'],
    #         output_file="validated_ingredients_google.json",
    #         context=[self.compile_user_profile(), self.rank_ingredients_rag()]  # Get user profile and ranked ingredients
    #     )

    # @task
    # def rank_ingredients(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['rank_ingredients'],
    #         output_file="ranked_ingredients.json",
    #         context=[self.compile_user_profile()]
    #     )
    
    @task
    def generate_supplement_recommendations(self) -> Task:
        return Task(
            config=self.tasks_config['generate_supplement_recommendations'],
            context=[self.rank_ingredients_rag(), self.discover_ingredients_web()],
            output_pydantic=SupplementRecommendations
        )

    @task
    def compile_final_supplement_recommendations(self) -> Task:
        return Task(
            config=self.tasks_config['compile_final_supplement_recommendations'],
            context=[self.generate_supplement_recommendations()],
            output_pydantic=FinalSupplementProtocol
        )

   
    @crew
    def crew(self) -> Crew:
        """Creates the LatestAiDevelopment crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True
        )
