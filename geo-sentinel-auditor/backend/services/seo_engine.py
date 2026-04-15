import os
from crewai import Agent, Task, Crew, Process
from langchain.tools import tool, BaseTool   # ✅ use langchain decorators/classes for crewai v0.11.2 compatibility
from langchain_community.llms import Ollama
from dotenv import load_dotenv
from tavily import TavilyClient
from pydantic import BaseModel, Field

load_dotenv()

local_llm = Ollama(model="llama3.2:3b")

tavily_api_key = os.environ.get("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=tavily_api_key) if tavily_api_key else None


class SearchInput(BaseModel):
    query: str = Field(description="Search query string")


class WebSearchTool(BaseTool):
    name: str = "search_the_web"
    description: str = "Search the web for real-time information about business location, reviews, and online presence."
    args_schema: type[BaseModel] = SearchInput

    def _run(self, query: str) -> str:
        # ✅ Robustness: handle case where agent passes a dict instead of a string
        if isinstance(query, dict):
            query = query.get("query", "")

        if not tavily_client:
            return "Error: TAVILY_API_KEY not set."
        if not query or not str(query).strip():
            return "No valid search query provided."
        
        query_str = str(query).strip()
        try:
            response = tavily_client.search(
                query=query_str,
                max_results=5,
                search_depth="basic"
            )
            results = response.get("results", [])
            if not results:
                return "No results found for this query."
            return "\n".join([
                f"- {r.get('title', 'No title')}: {r.get('content', '')[:200]}..."
                for r in results
            ])
        except Exception as e:
            return f"Search failed: {str(e)}"


search_tool = WebSearchTool()   # ✅ instantiate once, reuse across agents


def create_seo_audit_crew(business_name: str, industry: str, location: str):
    data_collector = Agent(
        role="Local SEO Data Collector",
        goal=f"Gather detailed local search data, directory listings, and presence information for {business_name} in {location}.",
        backstory="An expert web scraper and data gatherer who specializes in finding local business information across directories and search engines.",
        verbose=True,
        allow_delegation=False,
        tools=[search_tool],
        llm=local_llm
    )

    social_sentinel = Agent(
        role="Social Media & Reputation Analyst",
        goal=f"Analyze the social media presence, customer sentiment, and reputation for {business_name} in {location}.",
        backstory="A specialist in tracking brand mentions, social media engagement, and online reviews to judge a business's local reputation.",
        verbose=True,
        allow_delegation=False,
        tools=[search_tool],
        llm=local_llm
    )

    seo_strategist = Agent(
        role="Competitor & SEO Analyst",
        goal=f"Analyze the gathered data for {business_name} ({industry}) against typical local competitors to identify strategic gaps and SEO score.",
        backstory="A seasoned local SEO strategist who knows exactly what it takes to rank #1 in local map packs and organic search.",
        verbose=True,
        allow_delegation=False,
        llm=local_llm
    )

    optimization_expert = Agent(
        role="SEO Action Plan Writer",
        goal="Draft a clear, text-based checklist of actionable SEO steps based strictly on the provided strategy analysis. Do not attempt to use any tools.",
        backstory="A concise technical writer who specializes in summarizing complex SEO strategies into simple, readable bullet points for business owners.",
        verbose=True,
        allow_delegation=False,
        llm=local_llm
    )

    gather_data_task = Task(
        description=f"Search for '{business_name}' in '{location}'. Summarize their online presence, reviews (if found), and directory consistency.",
        expected_output="A summary of the business's online presence, directory mentions, and general visibility.",
        agent=data_collector
    )

    social_analysis_task = Task(
        description=f"Analyze social media presence (Facebook, Instagram, etc.) and online sentiment for '{business_name}'. Mandatory: Include a line 'Social Score: X/100' where X is your rating.",
        expected_output="A review of social presence and a clear label: 'Social Score: X/100'.",
        agent=social_sentinel
    )

    analyze_strategy_task = Task(
        description=f"Using the gathered data and social analysis, rate {business_name}'s local SEO overall, google presence, and content out of 100. Mandatory: Include labels 'Overall Score: X/100', 'Google Presence Score: X/100', and 'Content Score: X/100'.",
        expected_output="A block with explicit labels: 'Overall Score: X/100', 'Google Presence Score: X/100', 'Content Score: X/100', followed by a competitor analysis.",
        agent=seo_strategist,
        context=[gather_data_task, social_analysis_task]
    )

    create_action_plan_task = Task(
        description="Extract the main weaknesses from the strategy analysis and create a formatted, actionable list of 3-5 steps. Briefly mention the Overall Score at the end.",
        expected_output="A bulleted list of actionable optimization steps and 'Overall Score: X/100' at the bottom.",
        agent=optimization_expert,
        context=[analyze_strategy_task]
    )

    return Crew(
        agents=[data_collector, social_sentinel, seo_strategist, optimization_expert],
        tasks=[gather_data_task, social_analysis_task, analyze_strategy_task, create_action_plan_task],
        process=Process.sequential
    )