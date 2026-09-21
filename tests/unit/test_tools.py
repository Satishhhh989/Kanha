import pytest
from core.tools.registry import ToolRegistry
from core.tools.system_tools import GetSystemInfoTool
from core.errors import ToolNotFoundError

def test_tool_registry():
    registry = ToolRegistry()
    tool = GetSystemInfoTool()
    
    # Test register
    registry.register(tool)
    assert len(registry.list_tools()) == 1
    
    # Test get
    retrieved = registry.get("get_system_info")
    assert retrieved.name == "get_system_info"
    
    # Test get nonexistent
    with pytest.raises(ToolNotFoundError):
        registry.get("nonexistent_tool")
        
    # Test unregister
    registry.unregister("get_system_info")
    assert len(registry.list_tools()) == 0

def test_tool_schema_generation():
    registry = ToolRegistry()
    registry.register(GetSystemInfoTool())
    
    schemas = registry.get_tool_schemas()
    assert len(schemas) == 1
    assert schemas[0]["type"] == "function"
    assert schemas[0]["function"]["name"] == "get_system_info"
    assert "properties" in schemas[0]["function"]["parameters"]
