from crewai import Agent, Crew, Process, Task
from crewai.tasks.conditional_task import ConditionalTask
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.tasks.task_output import TaskOutput
#from crewai_tools import SerperDevTool
from typing import List

from aether_2.tools.biomarker_evaluation import BiomarkerEvaluationTool
#from aether_2.tools.fuzzy_dsld_search_tool import FuzzyDSLDSearchTool
from aether_2.tools.focus_areas_generator import EvaluateFocusAreasTool
from aether_2.tools.user_profile_compiler import UserProfileCompilerTool
from aether_2.tools.ingredient_ranker import IngredientRankerTool
from aether_2.tools.supplement_recommender import SupplementRecommendationTool


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
    def focus_area_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['focus_area_agent'],  # <-- add config in agents.yaml
            verbose=True,
            tools=[EvaluateFocusAreasTool()]
        )
    
    @agent
    def user_profile_compiler(self) -> Agent:
        return Agent(
            config=self.agents_config['user_profile_compiler'],
            verbose=True,
            tools=[UserProfileCompilerTool()]
        )

    @agent
    def ingredient_ranker(self) -> Agent:
        return Agent(
            config=self.agents_config['ingredient_ranker'],
            verbose=True,
            tools=[IngredientRankerTool()]
        )
    
    @agent
    def supplement_recommender(self) -> Agent:
        return Agent(
            config=self.agents_config['supplement_recommender'],
            verbose=True,
            tools=[SupplementRecommendationTool()]
        )

    '''
    @agent
    def ingredient_discovery_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['ingredient_discovery_agent'],  # type: ignore[index]
            verbose=True,
            tools=[SerperDevTool()]
        )

    @agent
    def supplement_search_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['supplement_search_agent'],  # type: ignore[index]
            verbose=True,
            tools=[FuzzyDSLDSearchTool()]
        )
    '''
    #
    # @task
    # def summarize_data(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['summarize_data'],  # type: ignore[index]
    #     )
    #
    # @task
    # def form_hypothesis(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['form_hypothesis'],  # type: ignore[index]
    #         human_input=True
    #     )

    @task
    def evaluate_inputs(self) -> Task:
        return Task(
            config=self.tasks_config['evaluate_inputs'],  # type: ignore[index]
        )
    
    @task
    def evaluate_focus_areas(self) -> Task:
        return Task(
            config=self.tasks_config['evaluate_focus_areas'],  # <-- add config in tasks.yaml
            output_file="focus_areas.md"
        )
    
    @task
    def compile_user_profile(self) -> Task:
        return Task(
            config=self.tasks_config['compile_user_profile'],
            output_file="user_profile.json",
            context=[self.evaluate_inputs()]  # Pass flagged biomarkers from previous task
        )

    @task
    def rank_ingredients(self) -> Task:
        return Task(
            config=self.tasks_config['rank_ingredients'],
            output_file="ranked_ingredients.json",
            context=[self.compile_user_profile()]
        )
    
    @task
    def generate_supplement_recommendations(self) -> Task:
        return Task(
            config=self.tasks_config['generate_supplement_recommendations'],
            output_file="supplement_recommendations.json",
            context=[self.compile_user_profile(), self.rank_ingredients(), self.evaluate_focus_areas()]
        )

    '''
    @task
    def ingredient_discovery_task(self) -> Task:
        return Task(
            config=self.tasks_config['ingredient_discovery_task'],  # type: ignore[index]
            output_file="ingredients.md"
        )

    @task
    def search_supplements_for_ingredients(self) -> Task:
        return Task(
            config=self.tasks_config['search_supplements_for_ingredients'],  # type: ignore[index]
            output_file="supplements.md"
        )
    '''
    @crew
    def crew(self) -> Crew:
        """Creates the LatestAiDevelopment crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True
        )
