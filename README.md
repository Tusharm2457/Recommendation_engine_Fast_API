# Aether AI Engine Crew

Welcome to the Aether AI Engine Crew project, powered by [crewAI](https://crewai.com). 

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
### Customizing

**Add your `MODEL, AZURE_API_KEY, AZURE_API_BASE, AZURE_API_VERSION and SERPER_API_KEY` into the `.env` file**

The code was tested with gpt-4o deployed on azure.


- Modify `src/aether_2/config/agents.yaml` to define your agents
- Modify `src/aether_2/config/tasks.yaml` to define your tasks
- Modify `src/aether_2/crew.py` to add your own logic, tools and specific args
- Modify `src/aether_2/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart the crew of AI agents and begin task execution, run this from the root folder of the project:

```bash
$ crewai run
```

This command initializes the aether-ai-engine Crew, assembling the agents and assigning them tasks as defined in your configuration.


## Understanding Your Crew

The aether-ai-engine Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.


About the tools - 

biomarker_evaluation.py
The biomarker_evaluation tool evaluates a person’s biomarker measurements against a predefined set of reference ranges. It takes a JSON string containing the person’s age, sex assigned at birth, and biomarker values, then looks up the relevant ranges for each biomarker, which may differ by sex or age. Each range is labeled (e.g., “optimal,” “normal,” “borderline,” “high” or similarly scaled) and mapped to a severity score from 0 (ideal) to 4 (critical). For each biomarker, the code determines which category the value falls into by checking it against the lower and upper bounds of each range. If the severity is 2 or higher, the biomarker is flagged. The result includes a detailed breakdown for every biomarker—its value, unit, category, severity, and range used—as well as a separate list of flagged biomarkers. Biomarkers not found in the reference table are returned with "status": "no_data". The main run method handles parsing the input, performing the evaluation, and returning the results as formatted JSON.

fuzzy_dsld_search_tool.py
The fuzzy_dsld_search tool searches the Dietary Supplement Label Database (DSLD) for products containing a given ingredient name using fuzzy string matching. It takes an ingredient name and a desired number of results, converts the ingredient name to lowercase, and expands it with any predefined synonyms so related terms are also searched. For each candidate term, it compares it against ingredient names in the DSLD dataset using a partial ratio match score from the rapidfuzz library, keeping matches above a threshold of 70. Matching results are sorted in descending order of similarity, and duplicates are removed based on their URL. The tool then returns up to the requested number of top matches, with each result including the product name, ingredient, amount per serving, unit, and the product’s URL.

Usage of SerperDevTool :

The agent when searching for ingredients associated with biomarkers, uses SerperDevTool to look them up at sources like pubmed. 