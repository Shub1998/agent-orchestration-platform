import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent import Agent
from app.models.workflow import Workflow, WorkflowNode, WorkflowEdge


async def create_hitl_content_approval(db: AsyncSession) -> dict:
    researcher_id = str(uuid.uuid4())
    writer_id = str(uuid.uuid4())
    publisher_id = str(uuid.uuid4())

    agents_data = [
        Agent(
            id=researcher_id, name="Brief Researcher", role="researcher",
            description="Researches the topic and prepares a structured brief for the writer",
            system_prompt=(
                "You are a research specialist who prepares content briefs. Given a content request, you:\n"
                "1. Research the topic using web search to find current information\n"
                "2. Identify the target audience and their key pain points\n"
                "3. Outline the main points to cover\n"
                "4. Suggest a headline and structure\n"
                "5. List 3-5 key statistics or quotes to include\n\n"
                "Deliver a structured brief that gives the writer everything they need to produce excellent content."
            ),
            model="gpt-4o-mini", provider="openai", temperature=0.3,
            max_iterations=8, memory_enabled=True,
            tools=["web_search", "get_current_datetime"],
            avatar_color="#3b82f6",
            memory_collection=f"agent_{researcher_id.replace('-', '_')}",
        ),
        Agent(
            id=writer_id, name="Content Drafter", role="writer",
            description="Produces the content draft based on the research brief",
            system_prompt=(
                "You are a skilled content writer. You receive a research brief and produce a well-crafted draft.\n\n"
                "Your draft should:\n"
                "1. Follow the structure outlined in the brief\n"
                "2. Incorporate the key statistics and quotes provided\n"
                "3. Be written clearly and engagingly for the target audience\n"
                "4. Include a compelling headline and strong opening\n"
                "5. End with a clear call-to-action\n\n"
                "Mark the draft clearly as 'DRAFT - PENDING REVIEW' at the top. "
                "Include a brief note to the reviewer explaining any editorial choices that need human judgment."
            ),
            model="gpt-4o-mini", provider="openai", temperature=0.7,
            max_iterations=4, memory_enabled=False, tools=[],
            avatar_color="#10b981",
            memory_collection=f"agent_{writer_id.replace('-', '_')}",
        ),
        Agent(
            id=publisher_id, name="Publisher", role="publisher",
            description="Applies reviewer feedback and finalizes content for publication",
            system_prompt=(
                "You are a publishing editor. You receive a content draft that has been approved (possibly with reviewer feedback) "
                "and prepare the final publication version.\n\n"
                "Your tasks:\n"
                "1. Apply any feedback from the human reviewer\n"
                "2. Remove the 'DRAFT - PENDING REVIEW' header\n"
                "3. Do a final proofread for grammar and formatting\n"
                "4. Add proper metadata suggestions (meta description, tags, estimated read time)\n"
                "5. Output the clean, publication-ready version\n\n"
                "If the reviewer left no specific feedback, just polish and finalize the approved draft."
            ),
            model="gpt-4o-mini", provider="openai", temperature=0.4,
            max_iterations=3, memory_enabled=False, tools=[],
            avatar_color="#8b5cf6",
            memory_collection=f"agent_{publisher_id.replace('-', '_')}",
        ),
    ]

    for a in agents_data:
        db.add(a)
    await db.flush()

    workflow_id = str(uuid.uuid4())
    workflow = Workflow(
        id=workflow_id,
        name="Content with Human Approval",
        description="Researcher briefs, Writer drafts, human reviews & approves, Publisher finalizes",
        trigger_type="manual",
        template_slug="hitl-content-approval",
    )
    db.add(workflow)
    await db.flush()

    start_id = str(uuid.uuid4())
    researcher_node_id = str(uuid.uuid4())
    writer_node_id = str(uuid.uuid4())
    approval_node_id = str(uuid.uuid4())
    publisher_node_id = str(uuid.uuid4())
    end_id = str(uuid.uuid4())

    nodes = [
        WorkflowNode(id=start_id, workflow_id=workflow_id, node_type="start", label="Start", position_x=50, position_y=250),
        WorkflowNode(id=researcher_node_id, workflow_id=workflow_id, node_type="agent", agent_id=researcher_id, label="Brief Researcher", position_x=250, position_y=250),
        WorkflowNode(id=writer_node_id, workflow_id=workflow_id, node_type="agent", agent_id=writer_id, label="Content Drafter", position_x=490, position_y=250),
        WorkflowNode(id=approval_node_id, workflow_id=workflow_id, node_type="approval", label="Human Review", position_x=730, position_y=250,
                     config={"prompt": "Please review the content draft above. Approve to publish or reject with feedback for revision."}),
        WorkflowNode(id=publisher_node_id, workflow_id=workflow_id, node_type="agent", agent_id=publisher_id, label="Publisher", position_x=970, position_y=250),
        WorkflowNode(id=end_id, workflow_id=workflow_id, node_type="end", label="End", position_x=1200, position_y=250),
    ]
    for n in nodes:
        db.add(n)

    edges = [
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=start_id, target_node_id=researcher_node_id, label=""),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=researcher_node_id, target_node_id=writer_node_id, label=""),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=writer_node_id, target_node_id=approval_node_id, label=""),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=approval_node_id, target_node_id=publisher_node_id, label="approved"),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=approval_node_id, target_node_id=writer_node_id, label="rejected", condition="rejected"),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=publisher_node_id, target_node_id=end_id, label=""),
    ]
    for e in edges:
        db.add(e)

    await db.commit()

    return {
        "workflow_id": workflow_id,
        "workflow_name": workflow.name,
        "agents": [researcher_id, writer_id, publisher_id],
        "message": "Content with Human Approval workflow created successfully",
    }
