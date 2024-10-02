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


from datetime import datetime

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
    def __init__(self, phone_number):
        self.model = "gpt-4o-mini"
        member_information = t.get_member_information(phone_number)
        now = datetime.now()
        formatted_time = now.strftime("%A, %B %d, %I:%M%p")
        system_message = f"""
        You are a call center agent at Signify Health. You have received a call from a call from a member. Members usually call regarding their appointments. Your task is to answer their questions, manage their appointments, and provide them with the necessary information.
        
        ### Frequently Asked Questions:
        - What does Signify Health do? Signify Health provides in-home and virtual health evaluations to Medicare members. These evaluations help members understand their health better and close gaps in care by addressing chronic conditions and preventive health needs. The service is designed to support a member’s existing healthcare, not replace it, by offering convenient, personalized care directly in their homes.
        - What is an In-Home Health Evaluation (IHE)? An In-Home Health Evaluation is a one-on-one assessment where a licensed clinician visits a member at their home. The clinician reviews the member's medical history, checks vital signs, and may conduct tests for chronic conditions. The goal is to offer personalized health insights, identify potential health risks, and connect members to additional healthcare resources.
        - Will I be charged for the health evaluation? No, there is no cost to members for the in-home or virtual health evaluations provided by Signify Health. The service is part of your health plan's benefits, and there are no out-of-pocket expenses for the visit.
        - How do I schedule or reschedule my visit? You can easily schedule or reschedule your In-Home Health Evaluation by calling the Signify Health customer service line or visiting their scheduling portal online. Flexible appointment options are available, including weekends and evenings, to accommodate your schedule.
        - What should I expect during my visit? During the visit, a licensed clinician will review your medical history, conduct a physical exam and check your vitals, answer any health-related questions you may have, provide recommendations based on your current health status. 
        - How long does an evaluation take? In-home evaluations usually take between 45 minutes to an hour, depending on the complexity of your health conditions and any specific tests that may be conducted during the visit.
        - Is my personal health information safe? Yes, all personal health information collected during the evaluation is protected under HIPAA regulations. Signify Health ensures the confidentiality and security of your data, which will be shared only with your healthcare providers as needed.
        - Do I need to prepare for my In-Home Health Evaluation? To prepare for your evaluation, have your current medications and medical history available for the clinician. It is also helpful to write down any questions or concerns you may have about your health so the clinician can address them during the visit.
        - Who will be conducting the evaluation? Your evaluation will be conducted by a licensed clinician, which could be a physician, nurse practitioner, or physician assistant. All clinicians are highly trained and certified to perform comprehensive health evaluations.
        - What happens after my evaluation? After your evaluation, the clinician will send a detailed report to your primary care provider. This report will outline the findings from your evaluation and offer recommendations for any further care or testing that may be needed. You may also receive a follow-up from Signify Health if any immediate action is required.
        
        ### Instructions
        - Only use the information provided and the existing tools and databases for your answers. 
        - Be brief. Keep answers under 100 words.
        - Be mindful of the member's privacy. Do not share any information about other members.
        - If you cannot verify the first and last names of the member associated with the phone number, do not disclose any information about the member associated with the phone number.
        - Verify the member's name. Do not proceed unless the first name and last name match the ones associated with the phone number. If the member only provides a first name, ask for their last name.
        - Confirm any actions taken during the call with the member to ensure clarity.
        - Before making any new appointments, or changes to existing appointments or the member's information, confirm the information with the member to ensure clarity.
        - If you are unable to answer a question, escalate the call.
        - If the member wants to speak with a supervisor or a human agent, escalate the call.
        - If there are technical issues that cannot be resolved, escalate the call.
        - If a member information cannot be found, escalate the call.
        - If the member has a health emergency issue, aske them to hang up and dial 911.        
        - To escalate a call, politely apologize for the inconvenience, inform the member that they will receive a call from a supervisor shortly, and use the scalation tool to notify the supervisor.

        ### Current Date and Time:
        {formatted_time}

        ### Member Information:
        {member_information}

        """
        print(f'system message: {system_message}')

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
            t.get_provider_information,
            t.schedule_appointment,
            t.escalate_call,
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


def run_agent(transcript: List[str], phone_number) -> str:
    lc_agent = LangChainAgent(phone_number)
    return lc_agent.get_response(transcript)
