import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent import Agent
from app.models.workflow import Workflow, WorkflowNode, WorkflowEdge


async def create_customer_support(db: AsyncSession) -> dict:
    triage_id = str(uuid.uuid4())
    billing_id = str(uuid.uuid4())
    tech_id = str(uuid.uuid4())
    general_id = str(uuid.uuid4())

    agents_data = [
        Agent(
            id=triage_id, name="Triage Agent", role="triage",
            description="Classifies customer issues and routes them to the right specialist",
            system_prompt=(
                "You are a customer support triage agent. Analyze the customer's message and classify it.\n"
                "Respond ONLY with a JSON object in this exact format:\n"
                '{"category": "billing", "priority": "high", "summary": "brief summary"}\n\n'
                "Categories:\n"
                "- 'billing': payment issues, invoices, subscription, charges, refunds\n"
                "- 'technical': bugs, errors, not working, integration, API, performance\n"
                "- 'general': feature requests, how-to questions, feedback, account settings\n\n"
                "Priority levels: 'low', 'medium', 'high', 'urgent'\n"
                "Be precise - only output the JSON, nothing else."
            ),
            model="gpt-4o-mini", provider="openai", temperature=0.1,
            max_iterations=3, memory_enabled=False, tools=[],
            avatar_color="#f59e0b",
            memory_collection=f"agent_{triage_id.replace('-', '_')}",
        ),
        Agent(
            id=billing_id, name="Billing Specialist", role="billing_support",
            description="Handles all billing, payment, and subscription inquiries",
            system_prompt=(
                "You are a friendly and empathetic billing support specialist. "
                "Help customers with billing issues, payment problems, refund requests, and subscription questions. "
                "Always be transparent about policies and timelines. "
                "If you need account-specific information you don't have, ask for it. "
                "Provide clear next steps and set realistic expectations."
            ),
            model="gpt-4o-mini", provider="openai", temperature=0.7,
            max_iterations=5, memory_enabled=True, tools=["get_current_datetime"],
            avatar_color="#10b981",
            memory_collection=f"agent_{billing_id.replace('-', '_')}",
        ),
        Agent(
            id=tech_id, name="Tech Support", role="technical_support",
            description="Resolves technical issues, bugs, and integration problems",
            system_prompt=(
                "You are an expert technical support engineer. "
                "Help customers debug issues, understand error messages, and resolve technical problems. "
                "Ask clarifying questions when needed. Provide step-by-step troubleshooting guides. "
                "Use web search to look up specific error codes or recent known issues when helpful. "
                "Document workarounds when direct fixes aren't available."
            ),
            model="gpt-4o-mini", provider="openai", temperature=0.4,
            max_iterations=8, memory_enabled=True, tools=["web_search"],
            avatar_color="#ef4444",
            memory_collection=f"agent_{tech_id.replace('-', '_')}",
        ),
        Agent(
            id=general_id, name="General Support", role="general_support",
            description="Handles feature requests, how-to questions, and general inquiries",
            system_prompt=(
                "You are a knowledgeable and friendly general support agent. "
                "Help customers with how-to questions, feature explanations, account settings, and general feedback. "
                "Be positive and solution-oriented. When you don't know something, say so honestly "
                "and offer to escalate to the appropriate team. "
                "Look up relevant documentation or information when needed."
            ),
            model="gpt-4o-mini", provider="openai", temperature=0.7,
            max_iterations=5, memory_enabled=True, tools=["web_search"],
            avatar_color="#6366f1",
            memory_collection=f"agent_{general_id.replace('-', '_')}",
        ),
    ]

    for a in agents_data:
        db.add(a)
    await db.flush()

    workflow_id = str(uuid.uuid4())
    workflow = Workflow(
        id=workflow_id,
        name="Customer Support Triage",
        description="Triage agent classifies issues and routes to billing, technical, or general specialists",
        trigger_type="manual",
        template_slug="customer-support",
    )
    db.add(workflow)
    await db.flush()

    start_id = str(uuid.uuid4())
    triage_node_id = str(uuid.uuid4())
    billing_node_id = str(uuid.uuid4())
    tech_node_id = str(uuid.uuid4())
    general_node_id = str(uuid.uuid4())
    end_billing_id = str(uuid.uuid4())
    end_tech_id = str(uuid.uuid4())
    end_general_id = str(uuid.uuid4())

    nodes = [
        WorkflowNode(id=start_id, workflow_id=workflow_id, node_type="start", label="Start", position_x=100, position_y=300),
        WorkflowNode(id=triage_node_id, workflow_id=workflow_id, node_type="agent", agent_id=triage_id, label="Triage Agent", position_x=300, position_y=300),
        WorkflowNode(id=billing_node_id, workflow_id=workflow_id, node_type="agent", agent_id=billing_id, label="Billing Specialist", position_x=600, position_y=100),
        WorkflowNode(id=tech_node_id, workflow_id=workflow_id, node_type="agent", agent_id=tech_id, label="Tech Support", position_x=600, position_y=300),
        WorkflowNode(id=general_node_id, workflow_id=workflow_id, node_type="agent", agent_id=general_id, label="General Support", position_x=600, position_y=500),
        WorkflowNode(id=end_billing_id, workflow_id=workflow_id, node_type="end", label="End", position_x=900, position_y=100),
        WorkflowNode(id=end_tech_id, workflow_id=workflow_id, node_type="end", label="End", position_x=900, position_y=300),
        WorkflowNode(id=end_general_id, workflow_id=workflow_id, node_type="end", label="End", position_x=900, position_y=500),
    ]
    for n in nodes:
        db.add(n)

    edges = [
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=start_id, target_node_id=triage_node_id, label=""),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=triage_node_id, target_node_id=billing_node_id, condition="billing", label="Billing"),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=triage_node_id, target_node_id=tech_node_id, condition="technical", label="Technical"),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=triage_node_id, target_node_id=general_node_id, condition="general", label="General"),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=billing_node_id, target_node_id=end_billing_id, label=""),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=tech_node_id, target_node_id=end_tech_id, label=""),
        WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, source_node_id=general_node_id, target_node_id=end_general_id, label=""),
    ]
    for e in edges:
        db.add(e)

    await db.commit()

    return {
        "workflow_id": workflow_id,
        "workflow_name": workflow.name,
        "agents": [triage_id, billing_id, tech_id, general_id],
        "message": "Customer Support Triage workflow created successfully",
    }
