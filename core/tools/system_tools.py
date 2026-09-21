import datetime
from typing import Any
from pydantic import BaseModel, Field
from .base import BaseTool
from core.security import RiskLevel
from sysplatform import adapter

# --- Get System Info Tool ---

class GetSystemInfoSchema(BaseModel):
    pass # No arguments needed

class GetSystemInfoTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_system_info"
        
    @property
    def description(self) -> str:
        return "Retrieves information about the host computer (OS, memory, CPU, hostname)."
        
    @property
    def input_schema(self) -> type[BaseModel]:
        return GetSystemInfoSchema
        
    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.READ_ONLY
        
    async def execute(self, **kwargs: Any) -> Any:
        info = adapter.get_system_info()
        return info.model_dump()


# --- Get Current Time Tool ---

class GetCurrentTimeSchema(BaseModel):
    pass # No arguments needed

class GetCurrentTimeTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_current_time"
        
    @property
    def description(self) -> str:
        return "Returns the current local time of the host system."
        
    @property
    def input_schema(self) -> type[BaseModel]:
        return GetCurrentTimeSchema
        
    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.READ_ONLY
        
    async def execute(self, **kwargs: Any) -> Any:
        now = datetime.datetime.now()
        return {"current_time": now.isoformat()}


# --- Open Application Tool ---

class OpenApplicationSchema(BaseModel):
    app_name: str = Field(..., description="The name of the application to open (e.g., 'Google Chrome', 'Calculator').")

class OpenApplicationTool(BaseTool):
    @property
    def name(self) -> str:
        return "open_application"
        
    @property
    def description(self) -> str:
        return "Attempts to launch a standard graphical application on the host computer by name."
        
    @property
    def input_schema(self) -> type[BaseModel]:
        return OpenApplicationSchema
        
    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.APPLICATION_CONTROL # This is HIGH risk, but we explicitly allow it in engine.py for Phase 1
        
    async def execute(self, app_name: str, **kwargs: Any) -> Any:
        success = adapter.open_application(app_name)
        if success:
            return {"status": "success", "message": f"Successfully launched {app_name}"}
        else:
            return {"status": "error", "message": f"Failed to launch {app_name}"}