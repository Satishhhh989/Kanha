from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel
from core.security import RiskLevel

@runtime_checkable
class BaseTool(Protocol):
    """
    Protocol defining the contract for a KAHNA tool.
    """
    
    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        ...
        
    @property
    def description(self) -> str:
        """Description of what the tool does, passed to the AI."""
        ...
        
    @property
    def input_schema(self) -> type[BaseModel]:
        """Pydantic model defining the expected arguments."""
        ...
        
    @property
    def risk_level(self) -> RiskLevel:
        """The risk classification of this tool."""
        ...
        
    async def execute(self, **kwargs: Any) -> Any:
        """
        Executes the tool with the validated arguments.
        Should return a serializable result (dict, string, etc.).
        """
        ...
