import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent import Agent
from app.models.workflow import Workflow, WorkflowNode, WorkflowEdge


async def create_content_pipeline(db: AsyncSession) -> dict:
    researcher_id = str(uuid.uuid4())
    writer_id = str(uuid.uuid4())
    editor_id = str(uuid.uuid4())

    agents_data = [
        Agent(
            id=researcher_id, name="Topic Researcher", role="researcher",
            description="Gathers source material, facts, and background information on the content topic",
            system_prompt=(
                "You are a thorough content researcher. Given a topic or content brief, you:\n"
                "1. Search the web for authoritative sources, recent news, and relevant data\n"
                "2. Identify key facts, statistics, and expert opinions\n"
                "3. Find compelling angles and unique insights\n"
                "4. Gather supporting examples and case studies\n\n"
                "Structure your findings clearly with source references. Focus on accuracy and recency. "
                "Aim for breadth — cover multiple perspectives before handing off to the writer."
            ),
            model="gpt-4o-mini", provider="openai", temperature=0.3,
            max_iterations=10, memory_enabled=True,
            tools=["web_search", "web_scraper", "get_current_datetime"],
            avatar_color="#3b82f6",
            memory_collection=f"agent_{researcher_id.replace('-', '_')}",
        ),
        Agent(
            id=writer_id, name="Content Writer", role="writer",
            description="Produces engaging, well-structured long-form content from research findings",
            system_prompt=(
                "You are an expert content writer and storyteller. You receive research findings and turn them into "
                "compelling, well-structured content.\n\n"
                "Your writing principles:\n"
                "1. Hook the reader in the opening paragraph\n"
                "2. Use clear headings and logical flow\n"
                "3. Balance data with narrative — make facts feel human\n"
                "4. Write in an active voice, concrete and specific\n"
                "5. Include actionable takeaways for the reader\n"
                "6. Aim for 600-1200 words unless instructed otherwise\n\n"
                "Adapt your tone to the content type (blog post, newsletter, report, etc.) specified in the brief. "
                "Produce complete, publication-ready drafts."
            ),
            model="gpt-4o-mini", provider="openai", temperature=0.7,
            max_iterations=5, memory_enabled=True, tools=[],
            avatar_color="#10b981",
            memory_collection=f"agent_{writer_id.replace('-', '_')}",
        ),
        Agent(
            id=editor_id, name="Senior Editor", role="editor",
            description="Reviews drafts for clarity, accuracy, and impact; delivers polished final copy",
            system_prompt=(
                "You are a senior editor with high standards for clarity and impact. You review content drafts and:\n"
                "1. Fix grammar, spelling, and punctuation errors\n"
                "2. Improve sentence rhythm and readability\n"
                "3. Strengthen the headline and opening hook\n"
                "4. Cut redundancy — tighten every paragraph\n"
                "5. Ensure the conclusion is punchy and memorable\n"
                "6. Verify the content achieves its stated goal\n\n"
                "Output the fully edited, publication-ready version of the content. "
                "Add a brief editor's note at the end explaining the key changes you made."
            ),
            model="gpt-4o-mini", provider="openai", temperature=0.4,
            max_iterations=3, memory_enabled=False, tools=[],
            avatar_color="#f59e0b",
            memory_collection=f"agent_{editor_id.replace('-', '_')}",
        ),
    ]

    for a in agents_data:
        db.add(a)
    await db.flush()

    workflow_id = str(uuid.uuid4())
    workflow = Workflow(
        id=workflow_id,
        name="Content Marketing Pipeline",
        description="Researcher gathers material, Writer drafts content, Editor polishes for publication",
        trigger_type="manual",
        template_slug="content-pipeline",
    )
    db.add(workflow)
    await db.flush()

    start_id = str(uuid.uuid4())
    researcher_node_id = str(uuid.uuid4())
    writer_node_id = str(uuid.uuid4())
    editor_node_id = str(uuid.uuid4())
    end_id = str(uuid.uuid4())

    nodes = [
        WorkflowNode(id=start_id, workflow_id=workflow_id, node_type="start", label="Start", position_x=50, position_y=250),
        WorkflowNode(id=researcher_node_id, workflow_id=workflow_id, node_type="agent", agent_id=researcher_id, label="Topic Researcher", position_x=270, position_y=250),
        WorkflowNode(id=writer_node_id, workflow_id=workflow_id, node_type="agent", agent_id=writer_id, label="Content Writer", position_x=530, position_y=250),
        WorkflowNode(id=editor_node_id, workflow_id=workflow_id, node_type="agent", agent_id=editor_id, label="Senior Editor", position_x=790, position_y=250),
        WorkflowNode(id=end_id, workflow_id=workflow_id, node_type="end", label="End", position_x=1050, position_y=250),
    ]
    for n in nodes:
        db.add(n)

    edges = [
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=start_id, target_node_id=researcher_node_id, label=""),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=researcher_node_id, target_node_id=writer_node_id, label=""),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=writer_node_id, target_node_id=editor_node_id, label=""),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=editor_node_id, target_node_id=end_id, label=""),
    ]
    for e in edges:
        db.add(e)

    await db.commit()

    return {
        "workflow_id": workflow_id,
        "workflow_name": workflow.name,
        "agents": [researcher_id, writer_id, editor_id],
        "message": "Content Marketing Pipeline created successfully",
    }
