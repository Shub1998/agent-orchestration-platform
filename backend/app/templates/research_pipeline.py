import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent import Agent
from app.models.workflow import Workflow, WorkflowNode, WorkflowEdge


async def create_research_pipeline(db: AsyncSession) -> dict:
    researcher_id = str(uuid.uuid4())
    summarizer_id = str(uuid.uuid4())

    researcher = Agent(
        id=researcher_id,
        name="Research Agent",
        role="researcher",
        description="Searches the web and gathers comprehensive information on a given topic",
        system_prompt=(
            "You are an expert researcher. Your job is to thoroughly investigate the given topic using web search and scraping tools. "
            "Gather facts, statistics, recent developments, and multiple perspectives. "
            "Present your findings in a structured format with key points and sources. "
            "Be comprehensive but accurate - only include information you have verified."
        ),
        model="gpt-4o-mini",
        provider="openai",
        temperature=0.3,
        max_iterations=10,
        memory_enabled=True,
        tools=["web_search", "web_scraper", "get_current_datetime"],
        avatar_color="#3b82f6",
        memory_collection=f"agent_{researcher_id.replace('-', '_')}",
    )

    summarizer = Agent(
        id=summarizer_id,
        name="Summarizer Agent",
        role="summarizer",
        description="Creates concise, actionable summaries from research findings",
        system_prompt=(
            "You are an expert at synthesizing information into clear, concise executive summaries. "
            "You will receive research findings from a researcher agent. "
            "Your job is to:\n"
            "1. Identify the 3-5 most important insights\n"
            "2. Synthesize the information into a coherent narrative\n"
            "3. Highlight actionable takeaways\n"
            "4. Keep the summary under 500 words\n"
            "5. Use clear headings and bullet points for readability\n\n"
            "Write for a busy executive who needs to understand the key points quickly."
        ),
        model="gpt-4o-mini",
        provider="openai",
        temperature=0.5,
        max_iterations=3,
        memory_enabled=True,
        tools=[],
        avatar_color="#8b5cf6",
        memory_collection=f"agent_{summarizer_id.replace('-', '_')}",
    )

    db.add(researcher)
    db.add(summarizer)
    await db.flush()

    workflow_id = str(uuid.uuid4())
    workflow = Workflow(
        id=workflow_id,
        name="Research + Summarizer Pipeline",
        description="Researcher gathers web information, Summarizer creates an executive summary",
        trigger_type="manual",
        template_slug="research-pipeline",
    )
    db.add(workflow)
    await db.flush()

    start_id = str(uuid.uuid4())
    researcher_node_id = str(uuid.uuid4())
    summarizer_node_id = str(uuid.uuid4())
    end_id = str(uuid.uuid4())

    nodes = [
        WorkflowNode(id=start_id, workflow_id=workflow_id, node_type="start", label="Start", position_x=100, position_y=250),
        WorkflowNode(id=researcher_node_id, workflow_id=workflow_id, node_type="agent", agent_id=researcher_id, label="Research Agent", position_x=350, position_y=250),
        WorkflowNode(id=summarizer_node_id, workflow_id=workflow_id, node_type="agent", agent_id=summarizer_id, label="Summarizer Agent", position_x=650, position_y=250),
        WorkflowNode(id=end_id, workflow_id=workflow_id, node_type="end", label="End", position_x=900, position_y=250),
    ]
    for n in nodes:
        db.add(n)

    edges = [
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=start_id, target_node_id=researcher_node_id, label=""),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=researcher_node_id, target_node_id=summarizer_node_id, label=""),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=summarizer_node_id, target_node_id=end_id, label=""),
    ]
    for e in edges:
        db.add(e)

    await db.commit()

    return {
        "workflow_id": workflow_id,
        "workflow_name": workflow.name,
        "agents": [researcher_id, summarizer_id],
        "message": "Research Pipeline created successfully",
    }
