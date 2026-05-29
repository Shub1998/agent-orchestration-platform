# Cost per 1M tokens (input, output) in USD — updated May 2026
COST_TABLE: dict[str, tuple[float, float]] = {
    "gpt-4o": (5.00, 15.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "claude-3-5-sonnet-20241022": (3.00, 15.00),
    "claude-3-5-haiku-20241022": (0.80, 4.00),
    "claude-3-opus-20240229": (15.00, 75.00),
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = COST_TABLE.get(model, (1.00, 3.00))  # fallback to gpt-4o-mini-ish
    cost = (input_tokens * rates[0] + output_tokens * rates[1]) / 1_000_000
    return round(cost, 6)


def extract_token_usage(response) -> tuple[int, int]:
    """Extract (input_tokens, output_tokens) from a LangChain AIMessage."""
    usage = getattr(response, "usage_metadata", None)
    if usage:
        return usage.get("input_tokens", 0), usage.get("output_tokens", 0)
    # Fallback for older LangChain response_metadata format
    meta = getattr(response, "response_metadata", {})
    token_usage = meta.get("token_usage", meta.get("usage", {}))
    input_t = token_usage.get("prompt_tokens", token_usage.get("input_tokens", 0))
    output_t = token_usage.get("completion_tokens", token_usage.get("output_tokens", 0))
    return input_t, output_t
