import os
from typing import Any
from pydantic import BaseModel, Field
from .base import BaseTool
from core.security import RiskLevel
from core.errors import ToolExecutionError

# --- List Directory Tool ---

class ListDirectorySchema(BaseModel):
    path: str = Field(..., description="The absolute or relative path to the directory to list.")

class ListDirectoryTool(BaseTool):
    @property
    def name(self) -> str:
        return "list_directory"
        
    @property
    def description(self) -> str:
        return "Lists the contents (files and folders) of a specified directory."
        
    @property
    def input_schema(self) -> type[BaseModel]:
        return ListDirectorySchema
        
    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.READ_ONLY
        
    async def execute(self, path: str, **kwargs: Any) -> Any:
        try:
            expanded_path = os.path.expanduser(path)
            if not os.path.exists(expanded_path):
                return {"status": "error", "message": f"Path '{path}' does not exist."}
            if not os.path.isdir(expanded_path):
                return {"status": "error", "message": f"Path '{path}' is not a directory."}
                
            entries = os.listdir(expanded_path)
            results = []
            for entry in entries:
                full_path = os.path.join(expanded_path, entry)
                is_dir = os.path.isdir(full_path)
                results.append({
                    "name": entry,
                    "type": "directory" if is_dir else "file"
                })
            return {"path": expanded_path, "contents": results}
        except Exception as e:
            raise ToolExecutionError(f"Failed to list directory '{path}': {str(e)}")


# --- Read Text File Tool ---

class ReadTextFileSchema(BaseModel):
    path: str = Field(..., description="The absolute or relative path to the text file to read.")

class ReadTextFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "read_text_file"
        
    @property
    def description(self) -> str:
        return "Reads and returns the contents of a text file."
        
    @property
    def input_schema(self) -> type[BaseModel]:
        return ReadTextFileSchema
        
    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.READ_ONLY
        
    async def execute(self, path: str, **kwargs: Any) -> Any:
        try:
            expanded_path = os.path.expanduser(path)
            if not os.path.exists(expanded_path):
                return {"status": "error", "message": f"File '{path}' does not exist."}
            if not os.path.isfile(expanded_path):
                return {"status": "error", "message": f"Path '{path}' is not a file."}
                
            with open(expanded_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"path": expanded_path, "content": content}
        except UnicodeDecodeError:
            return {"status": "error", "message": f"File '{path}' is not a valid UTF-8 text file."}
        except Exception as e:
            raise ToolExecutionError(f"Failed to read file '{path}': {str(e)}")
