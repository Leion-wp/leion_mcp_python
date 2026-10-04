"""
Leion Engine API Integration Tools (Phase D.0.2 Complete)

MCP tools pour piloter le Leion Workflow Engine via REST API.
Control plane (MCP) → Data plane (Engine :8001) intégration exhaustive.
"""

import os
import httpx
from typing import Any, Dict, Optional, List
from fastmcp import FastMCP

# Engine API configuration
ENGINE_API_URL = os.getenv("LEION_ENGINE_API_URL", "http://host.docker.internal:8001")
ENGINE_API_TIMEOUT = int(os.getenv("LEION_ENGINE_API_TIMEOUT", "60"))


async def _engine_request(
    method: str,
    endpoint: str,
    json_data: Optional[Dict] = None,
    timeout: int = ENGINE_API_TIMEOUT
) -> Dict[str, Any]:
    """HTTP client wrapper for Engine API calls
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint (e.g., /api/v1/workflows)
        json_data: Request body for POST/PUT
        timeout: Request timeout in seconds
    
    Returns:
        Engine API response JSON
    
    Raises:
        Exception: HTTP error or timeout
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        url = f"{ENGINE_API_URL}{endpoint}"
        
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            response = await client.post(url, json=json_data or {})
        elif method == "PUT":
            response = await client.put(url, json=json_data or {})
        elif method == "DELETE":
            response = await client.delete(url)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        if response.status_code not in (200, 201, 202, 204):
            raise Exception(
                f"Engine API error {response.status_code}: {response.text}"
            )
        
        # DELETE returns 204 No Content
        if response.status_code == 204:
            return {"status": "deleted"}
        
        return response.json()


def register_leion_engine_tools(server: FastMCP):
    """Register Leion Engine control plane tools (Phase D.0.2 complete)"""

    # ==================== WORKFLOWS CRUD ====================

    @server.tool()
    async def leion_engine_list_workflows(
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List all workflows (paginated)
        
        Workflow discovery and inventory.
        
        Args:
            limit: Max workflows to return (default 50)
            offset: Pagination offset (default 0)
        
        Returns:
            {
                "workflows": [
                    {"id": str, "name": str, "nodes_count": int, "created_at": str},
                    ...
                ],
                "total": int,
                "limit": int,
                "offset": int
            }
        
        Example:
            ChatGPT: "Show me all workflows"
            MCP: leion_engine_list_workflows()
        """
        result = await _engine_request(
            method="GET",
            endpoint=f"/api/v1/workflows?limit={limit}&offset={offset}"
        )
        
        workflows = [
            {
                "id": wf["id"],
                "name": wf["name"],
                "nodes_count": len(wf.get("nodes", [])),
                "created_at": wf.get("created_at")
            }
            for wf in result.get("workflows", [])
        ]
        
        return {
            "workflows": workflows,
            "total": result.get("total", len(workflows)),
            "limit": limit,
            "offset": offset
        }

    @server.tool()
    async def leion_engine_get_workflow(
        workflow_id: str
    ) -> Dict[str, Any]:
        """Get workflow details by ID
        
        Inspect workflow structure, nodes, connections.
        
        Args:
            workflow_id: Workflow UUID
        
        Returns:
            {
                "id": str,
                "name": str,
                "description": str,
                "nodes": [...],
                "connections": [...],
                "created_at": str
            }
        
        Example:
            ChatGPT: "Show me workflow abc123"
            MCP: leion_engine_get_workflow(workflow_id="abc123")
        """
        result = await _engine_request(
            method="GET",
            endpoint=f"/api/v1/workflows/{workflow_id}"
        )
        
        return {
            "id": result["id"],
            "name": result["name"],
            "description": result.get("description"),
            "nodes": result.get("nodes", []),
            "connections": result.get("connections", []),
            "nodes_count": len(result.get("nodes", [])),
            "created_at": result.get("created_at")
        }

    @server.tool()
    async def leion_engine_create_workflow(
        name: str,
        description: str,
        dag_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create workflow via Leion Engine API
        
        ChatGPT conversational workflow creation.
        
        Args:
            name: Workflow human-readable name
            description: Workflow purpose description
            dag_structure: {
                "steps": [
                    {"name": "step1", "type": "agent", "config": {...}},
                    ...
                ],
                "dependencies": {
                    "step2": ["step1"],
                    ...
                }
            }
        
        Returns:
            {
                "workflow_id": str,
                "nodes_count": int,
                "connections_count": int,
                "status": "created"
            }
        
        Example:
            ChatGPT: "Create 3-step ETL workflow: extract CSV, transform, load DB"
            MCP: leion_engine_create_workflow(...)
        """
        result = await _engine_request(
            method="POST",
            endpoint="/api/v1/workflows",
            json_data={
                "name": name,
                "description": description,
                "dag_structure": dag_structure
            }
        )
        
        return {
            "workflow_id": result["id"],
            "nodes_count": len(result.get("nodes", [])),
            "connections_count": len(result.get("connections", [])),
            "status": "created"
        }

    @server.tool()
    async def leion_engine_update_workflow(
        workflow_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        dag_structure: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update existing workflow
        
        Mutation: modify name, description, or DAG structure.
        
        Args:
            workflow_id: Workflow UUID to update
            name: New name (optional)
            description: New description (optional)
            dag_structure: New DAG structure (optional)
        
        Returns:
            {
                "workflow_id": str,
                "updated_fields": List[str],
                "status": "updated"
            }
        
        Example:
            ChatGPT: "Rename workflow abc123 to 'ETL v2'"
            MCP: leion_engine_update_workflow(
                workflow_id="abc123",
                name="ETL v2"
            )
        """
        update_data = {}
        updated_fields = []
        
        if name:
            update_data["name"] = name
            updated_fields.append("name")
        if description:
            update_data["description"] = description
            updated_fields.append("description")
        if dag_structure:
            update_data["dag_structure"] = dag_structure
            updated_fields.append("dag_structure")
        
        result = await _engine_request(
            method="PUT",
            endpoint=f"/api/v1/workflows/{workflow_id}",
            json_data=update_data
        )
        
        return {
            "workflow_id": result["id"],
            "updated_fields": updated_fields,
            "status": "updated"
        }

    @server.tool()
    async def leion_engine_delete_workflow(
        workflow_id: str
    ) -> Dict[str, Any]:
        """Delete workflow permanently
        
        Cleanup: removes workflow + all executions.
        
        Args:
            workflow_id: Workflow UUID to delete
        
        Returns:
            {
                "workflow_id": str,
                "status": "deleted"
            }
        
        Example:
            ChatGPT: "Delete workflow abc123"
            MCP: leion_engine_delete_workflow(workflow_id="abc123")
        """
        await _engine_request(
            method="DELETE",
            endpoint=f"/api/v1/workflows/{workflow_id}"
        )
        
        return {
            "workflow_id": workflow_id,
            "status": "deleted"
        }

    # ==================== EXECUTIONS LIFECYCLE ====================

    @server.tool()
    async def leion_engine_list_executions(
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List executions (paginated, filterable)
        
        History and monitoring across workflows.
        
        Args:
            workflow_id: Filter by workflow UUID (optional)
            status: Filter by status (pending|running|completed|failed)
            limit: Max executions to return (default 50)
            offset: Pagination offset (default 0)
        
        Returns:
            {
                "executions": [
                    {
                        "id": str,
                        "workflow_id": str,
                        "status": str,
                        "duration_ms": int,
                        "cost_usd": float,
                        "created_at": str
                    },
                    ...
                ],
                "total": int
            }
        
        Example:
            ChatGPT: "Show me all failed executions"
            MCP: leion_engine_list_executions(status="failed")
        """
        params = f"?limit={limit}&offset={offset}"
        if workflow_id:
            params += f"&workflow_id={workflow_id}"
        if status:
            params += f"&status={status}"
        
        result = await _engine_request(
            method="GET",
            endpoint=f"/api/v1/executions{params}"
        )
        
        executions = [
            {
                "id": ex["id"],
                "workflow_id": ex["workflow_id"],
                "status": ex["status"],
                "duration_ms": ex.get("duration_ms"),
                "cost_usd": ex.get("total_cost_usd"),
                "created_at": ex.get("start_time")
            }
            for ex in result.get("executions", [])
        ]
        
        return {
            "executions": executions,
            "total": result.get("total", len(executions))
        }

    @server.tool()
    async def leion_engine_execute_workflow(
        workflow_id: str,
        inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute workflow by ID (async)
        
        Returns execution_id immediately.
        Use leion_engine_get_execution_status() or streaming variant.
        
        Args:
            workflow_id: Workflow UUID
            inputs: Runtime input parameters (optional)
        
        Returns:
            {
                "execution_id": str,
                "status": str,
                "workflow_id": str
            }
        
        Example:
            ChatGPT: "Execute workflow abc123 with file: data.csv"
            MCP: leion_engine_execute_workflow(
                workflow_id="abc123",
                inputs={"file": "data.csv"}
            )
        """
        result = await _engine_request(
            method="POST",
            endpoint=f"/api/v1/workflows/{workflow_id}/execute",
            json_data={"inputs": inputs or {}}
        )
        
        return {
            "execution_id": result["id"],
            "status": result["status"],
            "workflow_id": workflow_id
        }

    @server.tool()
    async def leion_engine_get_execution_status(
        execution_id: str
    ) -> Dict[str, Any]:
        """Query execution status and metrics
        
        Poll execution progress.
        
        Args:
            execution_id: Execution UUID
        
        Returns:
            {
                "execution_id": str,
                "status": str,
                "duration_ms": int,
                "total_cost_usd": float,
                "nodes_completed": int,
                "nodes_total": int,
                "error": str
            }
        
        Example:
            ChatGPT: "What's status of execution def456?"
            MCP: leion_engine_get_execution_status(execution_id="def456")
        """
        result = await _engine_request(
            method="GET",
            endpoint=f"/api/v1/executions/{execution_id}"
        )
        
        nodes = result.get("nodes", [])
        nodes_total = len(nodes)
        nodes_completed = len([n for n in nodes if n.get("status") == "completed"])
        
        return {
            "execution_id": result["id"],
            "status": result["status"],
            "duration_ms": result.get("duration_ms"),
            "total_cost_usd": result.get("total_cost_usd"),
            "nodes_completed": nodes_completed,
            "nodes_total": nodes_total,
            "error": result.get("error")
        }

    @server.tool()
    async def leion_engine_resume_execution(
        execution_id: str
    ) -> Dict[str, Any]:
        """Resume crashed execution from checkpoint
        
        Crash resilience via checkpoint recovery.
        
        Args:
            execution_id: Execution UUID to resume
        
        Returns:
            {
                "execution_id": str,
                "status": str,
                "resume_count": int
            }
        
        Example:
            ChatGPT: "Execution def456 crashed. Resume it."
            MCP: leion_engine_resume_execution(execution_id="def456")
        """
        result = await _engine_request(
            method="POST",
            endpoint=f"/api/v1/executions/{execution_id}/resume"
        )
        
        return {
            "execution_id": result["id"],
            "status": result["status"],
            "resume_count": result.get("resume_count", 0)
        }

    @server.tool()
    async def leion_engine_cancel_execution(
        execution_id: str
    ) -> Dict[str, Any]:
        """Cancel running execution gracefully
        
        Phase C.5: Redis persistent cancellation flags.
        
        Args:
            execution_id: UUID of execution to cancel
        
        Returns:
            {
                "execution_id": str,
                "status": "failed",
                "nodes_completed": int
            }
        
        Example:
            ChatGPT: "Cancel execution def456"
            MCP: leion_engine_cancel_execution(execution_id="def456")
        """
        try:
            result = await _engine_request(
                method="POST",
                endpoint=f"/api/v1/executions/{execution_id}/cancel"
            )
            
            nodes_completed = len([
                n for n in result.get("nodes", [])
                if n.get("status") == "completed"
            ])
            
            return {
                "execution_id": result["id"],
                "status": result["status"],
                "nodes_completed": nodes_completed
            }
        
        except Exception as e:
            if "404" in str(e):
                return {"error": "Execution not found", "execution_id": execution_id}
            elif "400" in str(e):
                return {"error": "Cannot cancel: not running", "execution_id": execution_id}
            raise

    @server.tool()
    async def leion_engine_delete_execution(
        execution_id: str
    ) -> Dict[str, Any]:
        """Delete execution permanently
        
        Cleanup history, checkpoints removed.
        
        Args:
            execution_id: Execution UUID to delete
        
        Returns:
            {
                "execution_id": str,
                "status": "deleted"
            }
        
        Example:
            ChatGPT: "Delete execution def456"
            MCP: leion_engine_delete_execution(execution_id="def456")
        """
        await _engine_request(
            method="DELETE",
            endpoint=f"/api/v1/executions/{execution_id}"
        )
        
        return {
            "execution_id": execution_id,
            "status": "deleted"
        }

    # ==================== BUDGET TRACKING ====================

    @server.tool()
    async def leion_engine_get_budget() -> Dict[str, Any]:
        """Get global budget status and usage
        
        Cost monitoring across all workflows.
        
        Returns:
            {
                "current_usage_usd": float,
                "limit_usd": float,
                "remaining_usd": float,
                "utilization_pct": float,
                "workflows_count": int,
                "executions_count": int
            }
        
        Example:
            ChatGPT: "How much budget have I used?"
            MCP: leion_engine_get_budget()
        """
        result = await _engine_request(
            method="GET",
            endpoint="/api/v1/budget"
        )
        
        return {
            "current_usage_usd": result.get("current_usage_usd", 0),
            "limit_usd": result.get("limit_usd", 0),
            "remaining_usd": result.get("remaining_usd", 0),
            "utilization_pct": result.get("utilization_pct", 0),
            "workflows_count": result.get("workflows_count", 0),
            "executions_count": result.get("executions_count", 0)
        }

    # ==================== STREAMING (Phase D.0.2) ====================

    @server.tool()
    async def leion_engine_execute_stream(
        workflow_id: str,
        inputs: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 300
    ):
        """Execute workflow with real-time event streaming
        
        Phase D.0.2: Backend → Redis PubSub → MCP → ChatGPT
        Yields execution events as they occur (no polling).
        
        Args:
            workflow_id: Workflow UUID to execute
            inputs: Runtime input parameters (optional)
            timeout_seconds: Max wait for events (default 5min)
        
        Yields:
            {
                "type": str (status_change|node_started|node_completed|...),
                "data": {...},
                "timestamp": str
            }
        
        Terminal events: execution_completed, execution_failed
        
        Example:
            ChatGPT: "Execute workflow abc123 and stream progress"
            MCP: leion_engine_execute_stream(workflow_id="abc123")
            → ChatGPT receives real-time updates:
              {"type": "node_started", "data": {"node_id": "step1"}}
              {"type": "node_completed", "data": {"node_id": "step1", "cost_usd": 0.05}}
              {"type": "execution_completed", "data": {"duration_ms": 5000}}
        """
        # Import Redis subscriber
        from services.redis_subscriber import get_subscriber
        
        # 1. Start execution
        exec_result = await _engine_request(
            method="POST",
            endpoint=f"/api/v1/workflows/{workflow_id}/execute",
            json_data={"inputs": inputs or {}}
        )
        
        execution_id = exec_result["id"]
        
        # Yield initial status
        yield {
            "type": "execution_started",
            "data": {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "status": exec_result["status"]
            },
            "timestamp": exec_result.get("start_time")
        }
        
        # 2. Subscribe to Redis PubSub events
        try:
            subscriber = await get_subscriber()
            
            async for event in subscriber.subscribe_execution(
                execution_id,
                timeout_seconds=timeout_seconds
            ):
                # Forward Backend events to ChatGPT
                yield {
                    "type": event.get("type"),
                    "data": event.get("data", {}),
                    "timestamp": event.get("timestamp")
                }
                
                # Terminal events: stop streaming
                if event.get("type") in ("execution_completed", "execution_failed"):
                    break
        
        except Exception as e:
            # Graceful degradation: fallback to polling
            yield {
                "type": "stream_error",
                "data": {
                    "error": str(e),
                    "fallback": "Use leion_engine_get_execution_status() to poll"
                },
                "timestamp": None
            }


    # ==================== PHASE D.1.4: RECURSIVE WORKFLOW SPAWNING ====================

    @server.tool()
    async def leion_engine_spawn_workflow(
        parent_execution_id: str,
        workflow_id: str,
        inputs: Optional[Dict[str, Any]] = None,
        budget_quota_ratio: float = 0.5
    ) -> Dict[str, Any]:
        """Spawn child workflow from parent execution (Phase D.1.4)
        
        Recursive workflow orchestration pattern:
        - Parent spawns children at depth+1
        - Children inherit root_execution_id
        - Depth validation (max 10 levels)
        - Circular spawn detection (workflow ancestry)
        - Budget quota allocation (parent reserves 20% minimum)
        
        Args:
            parent_execution_id: Parent execution UUID
            workflow_id: Child workflow UUID to spawn
            inputs: Runtime inputs for child (optional)
            budget_quota_ratio: Budget allocation 0.0-1.0 (default 0.5)
        
        Returns:
            {
                "child_execution_id": str,
                "parent_execution_id": str,
                "workflow_id": str,
                "depth": int,
                "root_execution_id": str,
                "status": "spawned",
                "message": str
            }
        
        Raises:
            ValueError: Parent not found, invalid parameters
            NonRetryableError: Depth exceeded, circular spawn, budget exhausted
        
        Example usage:
            # Single child spawn
            ChatGPT: "Spawn data-processor workflow from execution abc123"
            MCP: leion_engine_spawn_workflow(
                parent_execution_id="abc123",
                workflow_id="data-processor-uuid",
                inputs={"file": "data.csv"}
            )
            
            # Parallel fan-out (3 workers)
            ChatGPT: "Spawn 3 parallel workers from master execution"
            MCP: [call leion_engine_spawn_workflow() 3x with budget_quota=0.3 each]
            
            # Recursive tree (master → workers → tasks)
            ChatGPT: "Create 2-level tree: master spawns 5 workers, each spawns 3 tasks"
            MCP:
              1. Execute master workflow
              2. Master workflow internally spawns 5 workers via this tool
              3. Each worker spawns 3 tasks
              Result: 1 master + 5 workers + 15 tasks = 21 executions
        """
        try:
            result = await _engine_request(
                method="POST",
                endpoint=f"/api/v1/executions/{parent_execution_id}/spawn",
                json_data={
                    "workflow_id": workflow_id,
                    "inputs": inputs or {},
                    "budget_quota_ratio": budget_quota_ratio
                },
                timeout=30  # Spawn is fast (validation + DB insert)
            )
            
            return {
                "child_execution_id": result["child_execution_id"],
                "parent_execution_id": result["parent_execution_id"],
                "workflow_id": result["workflow_id"],
                "depth": result["depth"],
                "root_execution_id": result["root_execution_id"],
                "budget_allocated_usd": result.get("budget_allocated_usd", 0.0),
                "status": "spawned",
                "message": result.get("message", "Child workflow spawned successfully")
            }
        
        except Exception as e:
            error_msg = str(e)
            
            # Parse backend error types
            if "404" in error_msg:
                return {
                    "error": "ParentNotFound",
                    "detail": f"Parent execution {parent_execution_id} not found",
                    "parent_execution_id": parent_execution_id
                }
            
            elif "Maximum spawn depth" in error_msg:
                return {
                    "error": "DepthExceeded",
                    "detail": error_msg,
                    "parent_execution_id": parent_execution_id,
                    "max_depth": 10
                }
            
            elif "Circular spawn detected" in error_msg:
                return {
                    "error": "CircularSpawn",
                    "detail": error_msg,
                    "workflow_id": workflow_id,
                    "parent_execution_id": parent_execution_id
                }
            
            elif "budget" in error_msg.lower():
                return {
                    "error": "BudgetExhausted",
                    "detail": error_msg,
                    "parent_execution_id": parent_execution_id
                }
            
            else:
                # Generic error
                return {
                    "error": "SpawnFailed",
                    "detail": error_msg,
                    "parent_execution_id": parent_execution_id,
                    "workflow_id": workflow_id
                }

    @server.tool()
    async def leion_engine_get_children(
        parent_execution_id: str
    ) -> Dict[str, Any]:
        """Get all direct children of execution (Phase D.1.4)
        
        Tree navigation: query immediate descendants.
        
        Args:
            parent_execution_id: Parent execution UUID
        
        Returns:
            {
                "parent_execution_id": str,
                "children": [
                    {
                        "id": str,
                        "workflow_id": str,
                        "status": str,
                        "depth": int,
                        "duration_ms": int,
                        "cost_usd": float
                    },
                    ...
                ],
                "children_count": int
            }
        
        Example:
            ChatGPT: "Show me children of execution abc123"
            MCP: leion_engine_get_children(parent_execution_id="abc123")
        """
        try:
            children = await _engine_request(
                method="GET",
                endpoint=f"/api/v1/executions/{parent_execution_id}/children"
            )
            
            return {
                "parent_execution_id": parent_execution_id,
                "children": children,
                "children_count": len(children)
            }
        
        except Exception as e:
            if "404" in str(e):
                return {
                    "error": "ExecutionNotFound",
                    "parent_execution_id": parent_execution_id
                }
            raise

    @server.tool()
    async def leion_engine_get_execution_tree(
        execution_id: str
    ) -> Dict[str, Any]:
        """Get entire execution tree (root + all descendants) (Phase D.1.4)
        
        Tree visualization: full hierarchy from root.
        
        Args:
            execution_id: Any execution UUID in tree (navigates to root)
        
        Returns:
            {
                "root_execution_id": str,
                "tree": [
                    {
                        "id": str,
                        "workflow_id": str,
                        "status": str,
                        "parent_execution_id": str,
                        "depth": int,
                        "duration_ms": int,
                        "cost_usd": float
                    },
                    ...
                ],
                "tree_size": int,
                "max_depth": int
            }
        
        Example:
            ChatGPT: "Show me entire execution tree for abc123"
            MCP: leion_engine_get_execution_tree(execution_id="abc123")
            → Returns: root + all descendants ordered by depth
        """
        try:
            tree = await _engine_request(
                method="GET",
                endpoint=f"/api/v1/executions/{execution_id}/tree"
            )
            
            if not tree:
                return {
                    "error": "TreeEmpty",
                    "execution_id": execution_id
                }
            
            # Extract root (depth=0)
            root = next((ex for ex in tree if ex.get("depth") == 0), None)
            root_id = root["id"] if root else tree[0].get("root_execution_id")
            
            # Calculate max depth
            max_depth = max((ex.get("depth", 0) for ex in tree), default=0)
            
            return {
                "root_execution_id": root_id,
                "tree": tree,
                "tree_size": len(tree),
                "max_depth": max_depth
            }
        
        except Exception as e:
            if "404" in str(e):
                return {
                    "error": "ExecutionNotFound",
                    "execution_id": execution_id
                }
            raise

    @server.tool()
    async def leion_engine_cancel_cascade(
        execution_id: str
    ) -> Dict[str, Any]:
        """Cancel execution and all descendants recursively (Phase D.1.3)
        
        Cascading cancellation: parent + entire subtree.
        
        Args:
            execution_id: Root execution UUID to cancel
        
        Returns:
            {
                "root_execution_id": str,
                "cancelled_count": int,
                "cancelled_ids": List[str],
                "max_depth_reached": int,
                "status": "cancelled"
            }
        
        Example:
            ChatGPT: "Cancel execution abc123 and all its children"
            MCP: leion_engine_cancel_cascade(execution_id="abc123")
            → Recursively cancels entire tree
        """
        try:
            result = await _engine_request(
                method="POST",
                endpoint=f"/api/v1/executions/{execution_id}/cancel?cascade=true",
                timeout=60  # Cascade can take time for large trees
            )
            
            return {
                "root_execution_id": result["execution_id"],
                "cancelled_count": result.get("cancelled_count", 0),
                "cancelled_ids": result.get("cancelled_ids", []),
                "max_depth_reached": result.get("max_depth_reached", 0),
                "status": "cancelled"
            }
        
        except Exception as e:
            if "404" in str(e):
                return {
                    "error": "ExecutionNotFound",
                    "execution_id": execution_id
                }
            elif "Cannot cancel" in str(e):
                return {
                    "error": "CannotCancel",
                    "detail": "Execution not running",
                    "execution_id": execution_id
                }
            raise
