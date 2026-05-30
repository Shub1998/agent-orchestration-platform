import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent import Agent
from app.models.workflow import Workflow, WorkflowNode, WorkflowEdge


async def create_data_intelligence(db: AsyncSession) -> dict:
    collector_id = str(uuid.uuid4())
    analyst_id = str(uuid.uuid4())
    reporter_id = str(uuid.uuid4())

    agents_data = [
        Agent(
            id=collector_id, name="Data Collector", role="data_collector",
            description="Gathers raw data from web sources, APIs, and public datasets",
            system_prompt=(
                "You are a data collection specialist. Given a research question or topic, you:\n"
                "1. Search for relevant quantitative data, market figures, and statistics\n"
                "2. Scrape structured data from authoritative sources (government databases, industry reports, etc.)\n"
                "3. Record all data points with their source, date, and context\n"
                "4. Note data quality issues — gaps, inconsistencies, or recency concerns\n\n"
                "Output a structured dataset with clear labels. Prioritize primary sources and recent data. "
                "Always include the source URL and publication date for each data point."
            ),
            model="gpt-4o-mini", provider="openai", temperature=0.2,
            max_iterations=12, memory_enabled=True,
            tools=["web_search", "web_scraper", "get_current_datetime"],
            avatar_color="#06b6d4",
            memory_collection=f"agent_{collector_id.replace('-', '_')}",
        ),
        Agent(
            id=analyst_id, name="Data Analyst", role="analyst",
            description="Analyzes collected data to identify trends, patterns, and actionable insights",
            system_prompt=(
                "You are a senior data analyst. You receive raw data from a collector and produce rigorous analysis.\n\n"
                "Your analysis framework:\n"
                "1. **Trend identification** — what is growing, declining, or plateauing?\n"
                "2. **Comparative analysis** — how do key metrics compare across segments, time periods, or competitors?\n"
                "3. **Anomaly detection** — what stands out as unexpected or noteworthy?\n"
                "4. **Root cause reasoning** — why are these patterns occurring?\n"
                "5. **Forecasting** — what are likely near-term developments based on the data?\n\n"
                "Be quantitative and specific. Cite exact figures. Flag confidence levels when data is limited. "
                "Separate facts from inferences clearly."
            ),
            model="gpt-4o-mini", provider="openai", temperature=0.3,
            max_iterations=5, memory_enabled=True, tools=[],
            avatar_color="#8b5cf6",
            memory_collection=f"agent_{analyst_id.replace('-', '_')}",
        ),
        Agent(
            id=reporter_id, name="Report Generator", role="reporter",
            description="Produces a professional, executive-ready intelligence report from analysis",
            system_prompt=(
                "You are a business intelligence report writer. You receive analytical findings and produce "
                "polished, executive-ready reports.\n\n"
                "Report structure to follow:\n"
                "# Executive Summary (3-5 bullet points — the most critical findings)\n"
                "# Key Findings (numbered, each with supporting data)\n"
                "# Analysis & Implications (what this means for decision-making)\n"
                "# Recommendations (3-5 concrete, actionable next steps)\n"
                "# Data Notes (sources, limitations, confidence levels)\n\n"
                "Write for a senior executive who has 5 minutes to read. Be direct, concrete, and jargon-free. "
                "Every claim must be supported by data from the analysis."
            ),
            model="gpt-4o-mini", provider="openai", temperature=0.5,
            max_iterations=3, memory_enabled=False, tools=[],
            avatar_color="#f59e0b",
            memory_collection=f"agent_{reporter_id.replace('-', '_')}",
        ),
    ]

    for a in agents_data:
        db.add(a)
    await db.flush()

    workflow_id = str(uuid.uuid4())
    workflow = Workflow(
        id=workflow_id,
        name="Data Intelligence Report",
        description="Collector gathers raw data, Analyst finds insights, Reporter produces an executive brief",
        trigger_type="manual",
        template_slug="data-intelligence",
    )
    db.add(workflow)
    await db.flush()

    start_id = str(uuid.uuid4())
    collector_node_id = str(uuid.uuid4())
    analyst_node_id = str(uuid.uuid4())
    reporter_node_id = str(uuid.uuid4())
    end_id = str(uuid.uuid4())

    nodes = [
        WorkflowNode(id=start_id, workflow_id=workflow_id, node_type="start", label="Start", position_x=50, position_y=250),
        WorkflowNode(id=collector_node_id, workflow_id=workflow_id, node_type="agent", agent_id=collector_id, label="Data Collector", position_x=270, position_y=250),
        WorkflowNode(id=analyst_node_id, workflow_id=workflow_id, node_type="agent", agent_id=analyst_id, label="Data Analyst", position_x=530, position_y=250),
        WorkflowNode(id=reporter_node_id, workflow_id=workflow_id, node_type="agent", agent_id=reporter_id, label="Report Generator", position_x=790, position_y=250),
        WorkflowNode(id=end_id, workflow_id=workflow_id, node_type="end", label="End", position_x=1050, position_y=250),
    ]
    for n in nodes:
        db.add(n)

    edges = [
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=start_id, target_node_id=collector_node_id, label=""),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=collector_node_id, target_node_id=analyst_node_id, label=""),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=analyst_node_id, target_node_id=reporter_node_id, label=""),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=reporter_node_id, target_node_id=end_id, label=""),
    ]
    for e in edges:
        db.add(e)

    await db.commit()

    return {
        "workflow_id": workflow_id,
        "workflow_name": workflow.name,
        "agents": [collector_id, analyst_id, reporter_id],
        "message": "Data Intelligence Report pipeline created successfully",
    }
