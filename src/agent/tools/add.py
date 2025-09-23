from langchain.tools.base import BaseTool


class AddTool(BaseTool):
    name: str = "add"
    description: str = "Adds two numbers. Input should be two integers separated by a comma, e.g., '2,3'."
    return_direct: bool = False

    def _run(self, a: int, b: int) -> str:
        """Add two numbers and return the result."""
        result = a + b
        return str(result)

    async def _arun(self, a: int, b: int) -> str:
        """Async version of _run."""
        return self._run(a, b)
