from typing import List
import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage
import tools as t
import tool_agents
from langchain.globals import set_verbose, set_debug

set_debug(True)

set_verbose(True)

# Ensure environment variables are loaded
load_dotenv()

# Get the OpenAI API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

# Check if the OpenAI API key is not None before creating the client
if openai_api_key is not None:
    client = OpenAI(api_key=openai_api_key)
else:
    raise ValueError("OPENAI_API_KEY environment variable is not set")


class LangChainAgent:
    def __init__(self, system_message: str):
        self.model = "gpt-4o-mini"

        # Initialize LangChain OpenAI LLM
        if openai_api_key is not None:
            self.llm = ChatOpenAI(model=self.model, temperature=0)
        else:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        # Create a simple tool
        self.tools = [
            tool_agents.update_databse,
            t.cancel_appointment,
            t.get_member_information,
            t.get_provider_information,
            t.schedule_appointment,
        ]

        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)

        self.agent_executor = AgentExecutor(
            agent=self.agent, tools=self.tools, verbose=True
        )

    def get_response(self, transcript: List[str]) -> str:
        last_msg = transcript[-1]
        chat_history = []
        for idx, val in enumerate(transcript[:-1]):
            if idx % 2 == 0:
                chat_history.append(AIMessage(content=val))
            else:
                chat_history.append(HumanMessage(content=val))
        print("chat_history: ", chat_history)

        res = self.agent_executor.invoke(
            {"chat_history": chat_history, "input": last_msg}
        )
        return res["output"]


def run_agent(system_message: str, transcript: List[str]) -> str:
    lc_agent = LangChainAgent(system_message)
    return lc_agent.get_response(transcript)
