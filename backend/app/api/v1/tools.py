from typing import Optional

from fastapi import APIRouter, HTTPException

from app.core.capability.base import CapabilityCategory, CapabilityPlatform, CapabilitySource
from app.core.capability.executor import capability_executor
from app.core.capability.registry import capability_registry
from app.core.connector.device_manager import device_manager
from app.core.hub.client import clawhub_client
from app.core.mcp.client import mcp_client
from app.core.skills.loader import skill_loader
from app.core.tool.registry import tool_registry
from app.core.tool.unified_spec import ToolCategory, ToolPlatform, unified_tool_registry

router = APIRouter()


@router.get("/list")
async def list_tools(include_remote: bool = True):
    tools = tool_registry.list_tools()
    if not include_remote:
        tools = [t for t in tools if not t.get("is_remote", False)]
    return {"tools": tools}


@router.get("/definitions")
async def get_tool_definitions(include_remote: bool = True):
    if include_remote:
        definitions = tool_registry.get_definitions()
    else:
        definitions = tool_registry.get_local_definitions()
    return {"definitions": definitions}


@router.get("/remote-definitions")
async def get_remote_tool_definitions():
    return {"definitions": tool_registry.get_remote_definitions()}


@router.post("/call/{tool_name}")
async def call_tool(tool_name: str, params: Optional[dict] = None, device_id: Optional[str] = None):
    params = params or {}
    try:
        if device_id:
            action = params.get("action", "execute")
            remote_params = {k: v for k, v in params.items() if k != "action"}
            result = await device_manager.execute_on_device(
                device_id=device_id,
                tool_name=tool_name,
                action=action,
                params=remote_params,
            )
            return {"status": "ok", "result": result, "device_id": device_id}

        result = await tool_registry.call_tool(tool_name, **params)
        return {"status": "ok", "result": result}
    except KeyError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/activate/{tool_name}")
async def activate_tool(tool_name: str):
    try:
        await tool_registry.activate_tool(tool_name)
        return {"status": "ok", "tool": tool_name, "state": "active"}
    except KeyError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")


@router.post("/hibernate/{tool_name}")
async def hibernate_tool(tool_name: str):
    try:
        await tool_registry.hibernate_tool(tool_name)
        return {"status": "ok", "tool": tool_name, "state": "inactive"}
    except KeyError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")


@router.get("/mcp/servers")
async def list_mcp_servers():
    return {
        "registered": mcp_client.get_registered_servers(),
        "connected": mcp_client.get_connected_servers(),
    }


@router.post("/mcp/register")
async def register_mcp_server(config: dict):
    from app.core.mcp.client import MCPServerConfig
    server_config = MCPServerConfig(
        name=config.get("name", ""),
        command=config.get("command", ""),
        args=config.get("args", []),
        env=config.get("env", {}),
        cwd=config.get("cwd"),
    )
    mcp_client.register_server(server_config)
    return {"status": "ok", "server": server_config.name}


@router.post("/mcp/connect/{server_name}")
async def connect_mcp_server(server_name: str):
    connected = await mcp_client.connect(server_name)
    if connected:
        tools = await mcp_client.list_tools()
        return {"status": "ok", "server": server_name, "tools_count": len(tools)}
    from fastapi import HTTPException
    raise HTTPException(status_code=500, detail=f"Failed to connect to MCP server: {server_name}")


@router.post("/mcp/disconnect/{server_name}")
async def disconnect_mcp_server(server_name: str):
    await mcp_client.disconnect(server_name)
    return {"status": "ok", "server": server_name}


@router.delete("/mcp/servers/{server_name}")
async def unregister_mcp_server(server_name: str):
    await mcp_client.disconnect(server_name)
    mcp_client.unregister_server(server_name)
    return {"status": "ok", "server": server_name}


@router.get("/mcp/tools")
async def list_mcp_tools():
    tools = await mcp_client.list_tools()
    return {"tools": [
        {"name": t.name, "description": t.description, "server": t.server_name}
        for t in tools
    ]}


@router.get("/skills")
async def list_skills():
    skills = skill_loader.list_skills()
    return {"skills": [
        {"name": s.name, "description": s.description, "version": s.version, "category": s.category}
        for s in skills
    ]}


@router.post("/skills/discover")
async def discover_skills():
    discovered = skill_loader.discover()
    return {"discovered": len(discovered), "skills": [
        {"name": s.name, "description": s.description}
        for s in discovered
    ]}


@router.post("/skills/execute/{skill_name}")
async def execute_skill(skill_name: str, params: Optional[dict] = None):
    params = params or {}
    try:
        result = await skill_loader.execute_skill(skill_name, **params)
        return {"status": "ok", "result": result}
    except KeyError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hub/search")
async def search_hub(query: str, category: str | None = None, limit: int = 20):
    items = await clawhub_client.search(query, category, limit)
    return {"items": [
        {
            "id": i.id, "name": i.name, "description": i.description,
            "version": i.version, "category": i.category, "installed": i.installed,
        }
        for i in items
    ]}


@router.post("/hub/install/{item_id}")
async def install_hub_item(item_id: str):
    item = await clawhub_client.install(item_id)
    if item:
        return {"status": "ok", "item": {"id": item.id, "name": item.name}}
    from fastapi import HTTPException
    raise HTTPException(status_code=500, detail=f"Failed to install item: {item_id}")


@router.post("/hub/uninstall/{item_id}")
async def uninstall_hub_item(item_id: str):
    success = await clawhub_client.uninstall(item_id)
    if success:
        return {"status": "ok"}
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"Item not installed: {item_id}")


@router.get("/hub/installed")
async def list_installed_hub_items(category: str | None = None):
    items = clawhub_client.list_installed(category)
    return {"items": [
        {"id": i.id, "name": i.name, "version": i.version, "category": i.category}
        for i in items
    ]}


@router.get("/unified/specs")
async def get_unified_tool_specs(platform: Optional[str] = None, category: Optional[str] = None):
    if platform:
        try:
            pf = ToolPlatform(platform.lower())
            specs = unified_tool_registry.get_specs_by_platform(pf)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")
    elif category:
        try:
            cat = ToolCategory(category.lower())
            specs = unified_tool_registry.get_specs_by_category(cat)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    else:
        specs = unified_tool_registry.get_all_specs()
    return {"specs": [s.to_dict() for s in specs], "count": len(specs)}


@router.get("/unified/platform-summary")
async def get_platform_summary():
    return unified_tool_registry.get_platform_summary()


@router.get("/unified/specs/{tool_name}")
async def get_unified_tool_spec(tool_name: str):
    spec = unified_tool_registry.get_spec(tool_name)
    if not spec:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Tool spec '{tool_name}' not found")
    return spec.to_dict()


@router.get("/unified/specs/{tool_name}/openai")
async def get_unified_tool_spec_openai(tool_name: str):
    spec = unified_tool_registry.get_spec(tool_name)
    if not spec:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Tool spec '{tool_name}' not found")
    return spec.to_openai_function()


@router.get("/capabilities")
async def list_capabilities(
    source_type: Optional[str] = None,
    platform: Optional[str] = None,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
):
    st = CapabilitySource(source_type) if source_type else None
    pf = CapabilityPlatform(platform) if platform else None
    cat = CapabilityCategory(category) if category else None
    metas = capability_registry.discover(source_type=st, platform=pf, category=cat, keyword=keyword)
    return {
        "capabilities": [m.to_dict() for m in metas],
        "count": len(metas),
        "summary": capability_registry.get_summary_by_source(),
    }


@router.get("/capabilities/definitions")
async def get_capability_definitions(
    source_type: Optional[str] = None,
    platform: Optional[str] = None,
):
    st = CapabilitySource(source_type) if source_type else None
    pf = CapabilityPlatform(platform) if platform else None
    definitions = capability_registry.get_definitions(source_type=st, platform=pf)
    return {"definitions": definitions, "count": len(definitions)}


@router.get("/capabilities/{capability_name}")
async def get_capability_detail(capability_name: str):
    meta = capability_registry.get(capability_name)
    if not meta:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Capability '{capability_name}' not found")
    return meta.to_dict()


@router.post("/capabilities/{capability_name}/execute")
async def execute_capability(capability_name: str, params: Optional[dict] = None):
    params = params or {}
    from app.core.capability.base import CapabilityCallContext
    context = CapabilityCallContext()
    result = await capability_executor.execute(capability_name, params, context)
    return result.to_dict()


@router.post("/capabilities/{capability_name}/activate")
async def activate_capability(capability_name: str):
    try:
        await capability_executor.activate(capability_name)
        return {"status": "ok", "capability": capability_name, "state": "active"}
    except KeyError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Capability '{capability_name}' not found")


@router.post("/capabilities/{capability_name}/deactivate")
async def deactivate_capability(capability_name: str):
    try:
        await capability_executor.deactivate(capability_name)
        return {"status": "ok", "capability": capability_name, "state": "inactive"}
    except KeyError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Capability '{capability_name}' not found")


@router.post("/capabilities/{capability_name}/health-check")
async def health_check_capability(capability_name: str):
    healthy = await capability_executor.health_check(capability_name)
    return {"capability": capability_name, "healthy": healthy}


@router.post("/capabilities/initialize")
async def initialize_capabilities():
    registered = await capability_registry.initialize()
    return {
        "status": "ok",
        "registered_count": len(registered),
        "registered": registered,
        "summary": capability_registry.get_summary_by_source(),
    }


@router.get("/capabilities/summary/sources")
async def get_capability_source_summary():
    return capability_registry.get_summary_by_source()


@router.get("/capabilities/summary/categories")
async def get_capability_category_summary():
    return capability_registry.get_summary_by_category()


@router.post("/cli/scan")
async def scan_cli_tools():
    from app.core.capability.providers.cli import CLISniffer
    sniffer = CLISniffer()
    tool_defs = await sniffer.scan()
    return {
        "found": len(tool_defs),
        "tools": [
            {"name": t.name, "path": t.path, "version": t.version}
            for t in tool_defs
        ],
    }
