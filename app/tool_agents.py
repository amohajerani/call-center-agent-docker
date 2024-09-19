"""
This script contains tools for the AI agent. These tools are also agents.

"""
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import OpenAI
from langchain_community.utilities import SQLDatabase
from langchain.agents import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_types import AgentType
import os
from dotenv import load_dotenv
from langchain.tools import tool

# Load environment variables
load_dotenv()

# Set up the database connection
db = SQLDatabase.from_uri(os.getenv('DATABASE_URL'))

# Set up the language model
llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")


prefix = """
        You are an agent designed to interact with a SQL database.
        Given an input question, create a syntactically correct Postgres query to run, \
        then look at the results of the query and return the answer.
        Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.
        You can order the results by a relevant column to return the most interesting examples in the database.
        You have access to tools for interacting with the database.
        Only use the below tools. Only use the information returned by the below tools to construct your final answer.\nYou MUST double check your query before executing it. \
        If you get an error while executing a query, rewrite the query and try again.
        The database is for a healthcare clinic. The database holds information about the members, providers, appointments, and providers schedule. Available tables are:
        members: this table holds information about the memberes, such as their demographic and contact inf.\
        providers: this table holds information about the providers, such as demographic, contact info and credentials.\
        availability: this table holds information about the availability of providers. It captures whether a provider is available at a given time or not. 
        appointments: this table holds information about the appointments. Each record is an appointment. \
        When retrieving appointments, pay attention to the appointment date and whether that is a future or a past appointment. \
        For example, if a member is asking about their next appointment, you should use the current time to look for future appointment not a past appointment. \
        If the query to the appointment table does not return anything, that simply means that the member does not have an appointment. You can search the appointments table by member's phone number.  
        """

# Create an instance of SQLDatabaseToolkit
sql_toolkit = SQLDatabaseToolkit(db=db, llm=llm)

query_agent_executor = create_sql_agent(
    llm=llm,
    toolkit=sql_toolkit,  # Pass the instance instead of the class
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    prefix=prefix,
    top_k=10,

)


@tool
def update_databse(question: str) -> str:
    """
    Use this tool for the following purposes:
    - update member's information such as their contact information, email, address, medical conditions and demographics.

    Args:
    question (str): The natural language question or instruction. 

    Returns:
    str: result od the database update operation.
    """
    try:
        result = query_agent_executor.run(question)
        return result
    except Exception as e:
        return f"An error occurred: {str(e)}"
