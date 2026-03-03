from typing import Dict, Any, List, Optional
import asyncio
import logging
from sqlalchemy.orm import Session
from app.core.websocket import send_execution_update
from app.models.workflow_execution import WorkflowExecution

logger = logging.getLogger(__name__)

class WorkflowExecutor:
    """Core workflow execution engine"""

    def __init__(self, workflow_config: dict, execution_id: int, db: Session,
                 max_concurrent: int = 10, fail_fast: bool = False):
        self.workflow_config = workflow_config
        self.execution_id = execution_id
        self.db = db
        self.max_concurrent = max_concurrent
        self.fail_fast = fail_fast
        self.nodes = {}
        self.edges = []
        self.results = {}  # node_id -> output
        self.errors = []
        self.execution_order = []  # Track order for debugging
        self._shutdown_event = asyncio.Event()
        self._running_tasks = set()

    async def execute(self):
        """Execute the workflow"""
        logger.info(f"Starting workflow execution {self.execution_id}")

        try:
            # Extract nodes and edges from config
            nodes = self.workflow_config.get("nodes", [])
            edges = self.workflow_config.get("edges", [])

            if not nodes:
                raise ValueError("Workflow has no nodes")

            # Store edges for data gathering
            self.edges = edges

            # Build node lookup
            for node in nodes:
                self.nodes[node["id"]] = node

            # Get user_id from execution record
            execution = self.db.query(WorkflowExecution).filter(
                WorkflowExecution.id == self.execution_id
            ).first()
            user_id = execution.triggered_by if execution else None

            # Build and validate dependency graph
            dependencies = self._build_dependencies(nodes, edges)
            self._validate_dependencies(dependencies)
            logger.info(f"Built dependency graph for {len(nodes)} nodes")

            # Execute nodes in topological order with concurrency control
            await self._execute_nodes(dependencies, user_id)

            await self._send_update("completed", {
                "message": "Workflow executed successfully",
                "total_nodes": len(nodes),
                "executed_nodes": len(self.results),
                "errors": len(self.errors)
            })
            logger.info(f"Workflow execution {self.execution_id} completed")

        except Exception as e:
            logger.error(
                f"Workflow execution {self.execution_id} failed",
                extra={"execution_id": self.execution_id, "error": str(e)},
                exc_info=True
            )
            await self._send_update("failed", {
                "error": str(e),
                "errors": self.errors,
                "partial_results": self.results,
                "executed_nodes": list(self.results.keys())
            })
            raise

    def _build_dependencies(self, nodes: List[dict], edges: List[dict]) -> Dict[str, List[str]]:
        """Build dependency graph from nodes and edges"""
        # Initialize dependencies for all nodes
        dependencies = {node["id"]: [] for node in nodes}

        # Track edges referencing missing nodes for debugging
        missing_targets = set()
        missing_sources = set()

        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")

            if source and target:
                if target in dependencies:
                    dependencies[target].append(source)
                else:
                    missing_targets.add(target)
                    logger.warning(f"Edge references non-existent target node: {target}")

                # Track if source doesn't exist (will be validated later)
                if source not in dependencies:
                    missing_sources.add(source)
                    logger.warning(f"Edge references non-existent source node: {source}")

        if missing_targets or missing_sources:
            logger.warning(
                f"Dependency build issues - missing targets: {missing_targets}, missing sources: {missing_sources}"
            )

        return dependencies

    def _validate_dependencies(self, dependencies: Dict[str, List[str]]):
        """Validate dependency graph for cycles and missing nodes"""
        # First, check for dependencies on non-existent nodes
        all_node_ids = set(self.nodes.keys())
        for node_id, deps in dependencies.items():
            for dep in deps:
                if dep not in all_node_ids:
                    raise ValueError(
                        f"Node '{node_id}' depends on non-existent node '{dep}'"
                    )

        # Then check for cycles using DFS
        visited = set()
        recursion_stack = set()

        def dfs(node_id: str):
            if node_id in recursion_stack:
                raise RuntimeError(f"Circular dependency detected involving node {node_id}")
            if node_id in visited:
                return

            visited.add(node_id)
            recursion_stack.add(node_id)

            for dep in dependencies.get(node_id, []):
                if dep in self.nodes:  # Only check dependencies that exist (already validated above)
                    dfs(dep)

            recursion_stack.remove(node_id)

        for node_id in dependencies:
            if node_id in self.nodes:
                dfs(node_id)

    async def _execute_nodes(self, dependencies: Dict[str, List[str]], user_id: int = None):
        """Execute nodes respecting dependencies with concurrency control"""
        executed = set()
        in_progress = set()
        max_iterations = len(self.nodes) * 2  # Safety limit
        iterations = 0

        # Semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)

        while len(executed) < len(self.nodes) and iterations < max_iterations:
            iterations += 1

            if self._shutdown_event.is_set():
                raise RuntimeError("Workflow execution cancelled due to shutdown")

            # Find nodes ready to execute (all dependencies satisfied)
            ready_nodes = []
            for node_id, deps in dependencies.items():
                if node_id not in executed and node_id not in in_progress and node_id in self.nodes:
                    if all(dep in executed for dep in deps):
                        ready_nodes.append(node_id)

            if not ready_nodes and len(executed) < len(self.nodes):
                # Check for circular dependencies or missing nodes
                remaining = set(self.nodes.keys()) - executed
                unfulfilled = []
                for node_id in remaining:
                    deps = dependencies.get(node_id, [])
                    missing_deps = [d for d in deps if d not in executed]
                    if missing_deps:
                        unfulfilled.append(f"{node_id}(missing: {missing_deps})")

                raise RuntimeError(
                    f"Circular dependency or missing nodes detected. "
                    f"Remaining: {remaining}. Unfulfilled dependencies: {unfulfilled}"
                )

            # Execute ready nodes with semaphore control
            tasks = []
            for node_id in ready_nodes:
                # Create coroutine and task
                coro = self._execute_node_with_limit(node_id, semaphore, user_id)
                task = asyncio.create_task(coro)
                self._running_tasks.add(task)  # Add immediately to avoid race condition
                tasks.append(task)
                in_progress.add(node_id)

                # Add callback to remove from running tasks when done
                task.add_done_callback(lambda t: self._running_tasks.discard(t))

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for node_id, result in zip(ready_nodes, results):
                    in_progress.remove(node_id)
                    if isinstance(result, Exception):
                        self.errors.append((node_id, str(result)))
                        logger.error(
                            f"Node {node_id} failed",
                            extra={"execution_id": self.execution_id, "node_id": node_id},
                            exc_info=True
                        )

                        if self.fail_fast:
                            # Send failure update with partial results before raising
                            await self._send_update("failed", {
                                "error": f"Node {node_id} failed: {result}",
                                "errors": self.errors,
                                "partial_results": self.results,
                                "executed_nodes": list(executed)
                            })
                            raise RuntimeError(f"Node {node_id} failed: {result}")
                        else:
                            # Mark as executed with error to avoid blocking
                            executed.add(node_id)
                            self.results[node_id] = {"error": str(result)}
                    else:
                        executed.add(node_id)
                        self.results[node_id] = result
                        self.execution_order.append(node_id)

        if iterations >= max_iterations:
            raise RuntimeError(f"Workflow execution exceeded maximum iterations ({max_iterations})")

    async def _execute_node_with_limit(self, node_id: str, semaphore: asyncio.Semaphore, user_id: int = None) -> Dict[str, Any]:
        """Execute node with semaphore control"""
        async with semaphore:
            return await self._execute_node(node_id, user_id)

    async def _execute_node(self, node_id: str, user_id: int = None) -> Dict[str, Any]:
        """Execute a single node"""
        if self._shutdown_event.is_set():
            raise RuntimeError("Workflow execution cancelled due to shutdown")

        node = self.nodes[node_id]
        node_type = node.get("type")
        # Get config from node.data.config (frontend structure)
        config = node.get("data", {}).get("config", {})

        logger.debug(
            f"Executing node {node_id} (type: {node_type})",
            extra={"execution_id": self.execution_id, "node_id": node_id}
        )

        await self._send_update("node_started", {
            "node_id": node_id,
            "node_type": node_type,
            "node_name": node.get("name", node_id),
            "config": config
        }, retries=3)

        try:
            # Import node class dynamically based on type
            from app.nodes import get_node_class
            node_class = get_node_class(node_type)
            node_instance = node_class(node_id, config)

            # Prepare inputs from connected nodes
            inputs = self._gather_inputs(node_id)

            # Execute node with context including user_id
            result = await node_instance.execute(inputs, {
                "execution_id": self.execution_id,
                "db": self.db,
                "user_id": user_id
            })

            await self._send_update("node_completed", {
                "node_id": node_id,
                "result": result
            }, retries=2)

            logger.debug(
                f"Node {node_id} completed successfully",
                extra={"execution_id": self.execution_id, "node_id": node_id}
            )
            return result

        except Exception as e:
            await self._send_update("node_failed", {
                "node_id": node_id,
                "error": str(e)
            }, retries=2)

            logger.error(
                f"Node {node_id} failed with error",
                extra={"execution_id": self.execution_id, "node_id": node_id, "error": str(e)},
                exc_info=True
            )
            raise

    def _gather_inputs(self, node_id: str) -> Dict[str, Any]:
        """Gather input data from connected nodes"""
        inputs = {}

        # Find all incoming edges to this node
        incoming_edges = [
            edge for edge in self.edges
            if edge.get("target") == node_id
        ]

        for edge in incoming_edges:
            source_id = edge.get("source")
            source_output = self.results.get(source_id)

            if source_output is not None:
                # Support for port mapping
                source_port = edge.get("source_port", "output")
                target_port = edge.get("target_port", "default")

                # If source_output is a dict, extract the specific port
                if isinstance(source_output, dict) and source_port in source_output:
                    inputs[target_port] = source_output[source_port]
                else:
                    # Pass entire output
                    inputs[target_port] = source_output

        return inputs

    async def _send_update(self, event_type: str, data: dict, retries: int = 3):
        """Send execution update via WebSocket with retry logic"""
        for attempt in range(retries):
            try:
                await send_execution_update(self.execution_id, {
                    "type": event_type,
                    "data": data,
                    "timestamp": asyncio.get_event_loop().time()
                })
                return
            except Exception as e:
                if attempt == retries - 1:
                    logger.warning(
                        f"Failed to send WebSocket update after {retries} attempts",
                        extra={"execution_id": self.execution_id, "event_type": event_type}
                    )
                else:
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff

    async def shutdown(self, timeout: float = 30.0):
        """Graceful shutdown with timeout"""
        logger.info(f"Shutting down workflow execution {self.execution_id}")
        self._shutdown_event.set()

        if not self._running_tasks:
            return

        # Wait for tasks to complete with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._running_tasks, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Shutdown timeout reached, cancelling {len(self._running_tasks)} tasks")
            for task in self._running_tasks:
                task.cancel()
            # Wait for cancellation to complete
            await asyncio.gather(*self._running_tasks, return_exceptions=True)