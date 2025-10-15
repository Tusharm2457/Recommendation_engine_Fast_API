from crewai import Agent, Crew, Process, Task
from crewai.tasks.conditional_task import ConditionalTask
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.tasks.task_output import TaskOutput
#from crewai_tools import SerperDevTool
from typing import List

from src.aether_2.tools.biomarker_evaluation import BiomarkerEvaluationTool
#from src.aether_2.tools.fuzzy_dsld_search_tool import FuzzyDSLDSearchTool
from src.aether_2.tools.focus_areas_generator import EvaluateFocusAreasTool
from src.aether_2.tools.user_profile_compiler import UserProfileCompilerTool
from src.aether_2.tools.web_ingredient_discovery import WebIngredientDiscoveryTool
from src.aether_2.tools.ingredient_ranker_rag import IngredientRankerRAGTool
#from src.aether_2.tools.google_search_validator import GoogleSearchValidatorTool
from src.aether_2.tools.ingredient_ranker import IngredientRankerTool
from src.aether_2.tools.supplement_recommender import SupplementRecommendationTool
from src.aether_2.tools.final_supplement_compiler import FinalSupplementCompilerTool


# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class Aether2():
    """Aether2 crew"""
    agents: List[BaseAgent]
    tasks: List[Task]

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
    def biomarker_preprocessor(self) -> Agent:
        return Agent(
            config=self.agents_config['biomarker_preprocessor'],  # type: ignore[index]
            verbose=True,
            tools=[BiomarkerEvaluationTool()]
        )
    
    @agent
    def user_profile_compiler(self) -> Agent:
        return Agent(
            config=self.agents_config['user_profile_compiler'],
            verbose=True,
            tools=[UserProfileCompilerTool()]
        )
    
    @agent
    def focus_area_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['focus_area_agent'],  # <-- add config in agents.yaml
            verbose=True,
            tools=[EvaluateFocusAreasTool()]
        )
    
    @agent
    def web_ingredient_discovery(self) -> Agent:
        return Agent(
            config=self.agents_config['web_ingredient_discovery'],
            verbose=True,
            tools=[WebIngredientDiscoveryTool()]
        )
    
    # Temporarily disabled for testing
    @agent
    def ingredient_ranker_rag(self) -> Agent:
        return Agent(
            config=self.agents_config['ingredient_ranker_rag'],
            verbose=True,
            tools=[IngredientRankerRAGTool()]
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
            tools=[SupplementRecommendationTool()]
        )

    @agent
    def final_supplement_compiler(self) -> Agent:
        return Agent(
            config=self.agents_config['final_supplement_compiler'],
            verbose=True,
            tools=[FinalSupplementCompilerTool()]
        )

    
   

    @task
    def evaluate_inputs(self) -> Task:
        return Task(
            config=self.tasks_config['evaluate_inputs'],  # type: ignore[index]
            output_file="flagged_biomarkers.md"
        )
    
    @task
    def compile_user_profile(self) -> Task:
        return Task(
            config=self.tasks_config['compile_user_profile'],
            output_file="user_profile.json",
            context=[self.evaluate_inputs()],  # Pass flagged biomarkers from previous task
            inputs={"patient_and_blood_data": "The original combined data"} 
        )
    
    @task
    def evaluate_focus_areas(self) -> Task:
        return Task(
            config=self.tasks_config['evaluate_focus_areas'],  # <-- add config in tasks.yaml
            output_file="focus_areas.md"
        )
    
    @task
    def discover_ingredients_web(self) -> Task:
        return Task(
            config=self.tasks_config['discover_ingredients_web'],
            output_file="discovered_ingredients_web.json",
            context=[self.compile_user_profile()]  # Get user profile from Agent 2
        )
    
    # Temporarily disabled for testing
    @task
    def rank_ingredients_rag(self) -> Task:
        return Task(
            config=self.tasks_config['rank_ingredients_rag'],
            output_file="ranked_ingredients_rag.json",
            context=[self.compile_user_profile()]  # Get user profile from Agent 2
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
            output_file="supplement_recommendations.json",
            context=[self.compile_user_profile(), self.rank_ingredients_rag(), self.discover_ingredients_web()]
        )

    @task
    def compile_final_supplement_recommendations(self) -> Task:
        return Task(
            config=self.tasks_config['compile_final_supplement_recommendations'],
            output_file="final_supplement_recommendations.json",
            context=[self.generate_supplement_recommendations(), self.evaluate_focus_areas()]
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
