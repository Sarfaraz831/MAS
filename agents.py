from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
from langchain_google_genai import GoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-120b",temperature=0.1)

# llm = ChatMistralAI(
#     model="mistral-small-latest",
#     temperature=0.1,
#     )

# llm = GoogleGenerativeAI(
#     model = "gemini-2.5-flash",
#     temperature=0.2
# )


# build_search_agent feature:
# - gives the AI tool access to live web search results
# - used to discover recent and relevant information before writing the report
# - this is the "research discovery" stage of the pipeline
def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search]
    )


# build_reader_agent feature:
# - gives the AI tool access to page scraping
# - used to extract deeper content from the best source discovered earlier
# - this is the "deep content extraction" stage of the pipeline
def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url]
    )


# writer_prompt feature:
# - transforms all found research into a structured final report
# - enforces introduction, findings, conclusion, and source list format
# - now also makes the report more usable for source-based citation workflows
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert researcher. Give clear, structured and insightful reports."),
    ("human", """Give a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Comparison or Insights (if relevant)
- Conclusion
- Sources (list each source URL used in the report)

Make the response factual, professional, and easy to cite.
Use clear headings and keep the final answer readable for a user who wants to trust and verify the findings."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()


# critic_prompt feature:
# - reviews the generated report for strengths, weaknesses, and quality issues
# - helps improve the final output before it is presented to the user
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()
