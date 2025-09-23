from langchain.tools.base import BaseTool


class SubtractTool(BaseTool):
    name: str = "subtract"
    description: str = "Subtracts two numbers."
    return_direct: bool = False

    def _run(self, a: int, b: int) -> str:
        """Subtract b from a and return the result."""
        result = a - b
        return str(result)

    async def _arun(self, a: int, b: int) -> str:
        """Async version of _run."""
        return self._run(a, b)
