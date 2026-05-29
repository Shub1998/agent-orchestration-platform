from langchain_core.tools import tool
import ast
import operator


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression safely. Supports basic arithmetic: +, -, *, /, **, //, %."""
    allowed_ops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod, ast.USub: operator.neg,
    }

    def _eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp):
            op = allowed_ops.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op)}")
            return op(_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -_eval(node.operand)
        raise ValueError(f"Unsupported expression: {type(node)}")

    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval(tree.body)
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"
