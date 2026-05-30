from typing import Callable
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from app.core.state import AgentFlowState
from app.core.tool_registry import get_tools, load_custom_tools_sync, TOOL_REGISTRY
from app.core.log_emitter import log_emitter
from app.core.memory_manager import memory_manager
from app.core.cost_calculator import extract_token_usage, calculate_cost
from app.config import settings


class AgentBuilder:
    def build(self, agent_data: dict) -> Callable[[AgentFlowState], dict]:
        agent_id = agent_data["id"]
        agent_name = agent_data["name"]
        system_prompt = agent_data["system_prompt"]
        model = agent_data["model"]
        provider = agent_data["provider"]
        temperature = agent_data.get("temperature", 0.7)
        max_iterations = agent_data.get("max_iterations", 10)
        memory_enabled = agent_data.get("memory_enabled", True)
        tool_names = agent_data.get("tools", [])
        # Guardrails
        max_output_tokens = agent_data.get("max_output_tokens", 4096)
        guardrail_keywords = agent_data.get("guardrail_keywords", [])

        input_guardrail_keywords = agent_data.get("input_guardrail_keywords", [])
        max_input_length = agent_data.get("max_input_length", 0)
        response_format = agent_data.get("response_format", "text")

        tools = get_tools(tool_names)

        # Load any custom webhook tools requested but not in TOOL_REGISTRY
        custom_names = [n for n in tool_names if n not in TOOL_REGISTRY]
        if custom_names:
            import re
            from app.config import settings
            db_path = re.sub(r"^sqlite\+aiosqlite:///", "", settings.DATABASE_URL)
            custom = load_custom_tools_sync(db_path)
            tools += [t for t in custom if t.name in custom_names]
        llm = self._create_llm(provider, model, temperature, max_output_tokens,
                               role=agent_data.get("role", "assistant"),
                               response_format=response_format)
        llm_with_tools = llm.bind_tools(tools) if tools and provider != "demo" else llm

        def agent_node(state: AgentFlowState) -> dict:
            execution_id = state.get("execution_id", "")
            input_text = state.get("input", "")
            total_input_tokens = 0
            total_output_tokens = 0

            # --- Input guardrails ---
            if max_input_length and max_input_length > 0 and len(input_text) > max_input_length:
                input_text = input_text[:max_input_length]
                log_emitter.emit(execution_id, "info",
                                 f"Input truncated to {max_input_length} characters",
                                 agent_id=agent_id, agent_name=agent_name)

            if input_guardrail_keywords:
                input_lower = input_text.lower()
                for kw in input_guardrail_keywords:
                    if kw.lower() in input_lower:
                        blocked_output = f"[Input blocked by guardrail: contains forbidden content]"
                        log_emitter.emit(execution_id, "error",
                                         f"Input guardrail triggered: keyword '{kw}' found in input",
                                         agent_id=agent_id, agent_name=agent_name)
                        log_emitter.emit(execution_id, "llm_end", blocked_output,
                                         agent_id=agent_id, agent_name=agent_name,
                                         metadata={"output": blocked_output, "input_tokens": 0,
                                                   "output_tokens": 0, "cost_usd": 0.0})
                        return {"messages": [], "current_agent": agent_name,
                                "output": blocked_output, "iteration": state.get("iteration", 0) + 1,
                                "approval_decision": None, "token_usage": {"input_tokens": 0,
                                                                           "output_tokens": 0, "cost_usd": 0.0}}

            log_emitter.emit(
                execution_id, "llm_start",
                f"Agent '{agent_name}' starting ({model})",
                agent_id=agent_id, agent_name=agent_name,
                metadata={"model": model, "provider": provider},
            )

            messages = [SystemMessage(content=system_prompt)]

            if memory_enabled and input_text:
                memories = memory_manager.retrieve(agent_id, input_text)
                if memories:
                    messages.append(HumanMessage(content=f"[Relevant memory from previous interactions]\n{memories}"))
                    log_emitter.emit(execution_id, "info", f"Retrieved {len(memories.split('---'))} memory entries",
                                     agent_id=agent_id, agent_name=agent_name)

            messages += state["messages"]

            # Inject reviewer feedback when retrying after a rejection
            rejection_comment = state.get("rejection_comment")
            if rejection_comment:
                feedback_msg = (
                    f"[Reviewer feedback — your previous output was REJECTED]\n"
                    f"Reason: {rejection_comment}\n\n"
                    f"Please revise your response addressing this feedback."
                )
                messages.append(HumanMessage(content=feedback_msg))
                log_emitter.emit(
                    execution_id, "info",
                    f"Agent '{agent_name}' retrying after rejection: {rejection_comment[:120]}",
                    agent_id=agent_id, agent_name=agent_name,
                )

            iteration = 0
            response = llm_with_tools.invoke(messages)
            inp, out = extract_token_usage(response)
            total_input_tokens += inp
            total_output_tokens += out

            while hasattr(response, "tool_calls") and response.tool_calls and iteration < max_iterations:
                messages.append(response)
                tool_results = []
                for tc in response.tool_calls:
                    tool_name = tc["name"]
                    tool_args = tc["args"]
                    log_emitter.emit(
                        execution_id, "tool_call",
                        f"Calling tool: {tool_name}",
                        agent_id=agent_id, agent_name=agent_name,
                        metadata={"tool": tool_name, "args": str(tool_args)[:300]},
                    )
                    tool_fn = next((t for t in tools if t.name == tool_name), None)
                    if tool_fn:
                        result = tool_fn.invoke(tool_args)
                        log_emitter.emit(
                            execution_id, "tool_call",
                            f"Tool '{tool_name}' → {str(result)[:200]}",
                            agent_id=agent_id, agent_name=agent_name,
                        )
                    else:
                        result = f"Tool {tool_name} not found"
                    tool_results.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

                messages += tool_results
                response = llm_with_tools.invoke(messages)
                inp, out = extract_token_usage(response)
                total_input_tokens += inp
                total_output_tokens += out
                iteration += 1

            output = response.content if hasattr(response, "content") else str(response)

            # Guardrail: block forbidden keywords
            if guardrail_keywords:
                output_lower = output.lower()
                for kw in guardrail_keywords:
                    if kw.lower() in output_lower:
                        output = f"[Output blocked by guardrail: contains forbidden content]"
                        log_emitter.emit(execution_id, "error",
                                         f"Guardrail triggered: keyword '{kw}' found in output",
                                         agent_id=agent_id, agent_name=agent_name)
                        break

            cost = calculate_cost(model, total_input_tokens, total_output_tokens)
            log_emitter.emit(
                execution_id, "llm_end",
                f"Agent '{agent_name}' completed — {total_input_tokens} in / {total_output_tokens} out tokens (${cost:.4f})",
                agent_id=agent_id, agent_name=agent_name,
                metadata={
                    "output": output[:4000],
                    "truncated": len(output) > 4000,
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "cost_usd": cost,
                    "model": model,
                },
            )

            if memory_enabled and input_text and output:
                memory_manager.store(agent_id, input_text, output, execution_id)

            return {
                "messages": [AIMessage(content=output)],
                "current_agent": agent_name,
                "output": output,
                "iteration": state.get("iteration", 0) + 1,
                "approval_decision": None,  # reset so next approval gate starts fresh
                "token_usage": {
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "cost_usd": cost,
                },
            }

        return agent_node

    def _create_llm(self, provider: str, model: str, temperature: float,
                    max_tokens: int = 4096, role: str = "assistant", response_format: str = "text"):
        if provider == "demo":
            from app.core.demo_llm import DemoLLM
            return DemoLLM(agent_role=role)
        if provider == "anthropic":
            return ChatAnthropic(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
            )
        kwargs: dict = dict(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        if response_format == "json":
            kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
        return ChatOpenAI(**kwargs)


agent_builder = AgentBuilder()
