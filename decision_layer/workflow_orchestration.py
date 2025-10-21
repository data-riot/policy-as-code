"""
Workflow Orchestration for Agentic Government Services

This module provides workflow orchestration capabilities that enable
self-orchestrating government workflows with intelligent resource allocation
and exception handling.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field

from .core import DecisionContext, DecisionEngine
from .llm_integration import LLMIntegration, AgenticContext, ReasoningMode
from .errors import DecisionLayerError, ValidationError

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskStatus(str, Enum):
    """Individual task status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ResourceType(str, Enum):
    """Types of resources that can be allocated"""

    HUMAN_AGENT = "human_agent"
    AI_AGENT = "ai_agent"
    COMPUTATIONAL = "computational"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"


@dataclass
class WorkflowTask:
    """Individual task in a workflow"""

    task_id: str
    name: str
    description: str
    task_type: str
    required_capabilities: List[str]
    estimated_duration: int  # minutes
    dependencies: List[str] = field(default_factory=list)
    resource_requirements: Dict[ResourceType, int] = field(default_factory=dict)
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class WorkflowDefinition:
    """Definition of a complete workflow"""

    workflow_id: str
    name: str
    description: str
    version: str
    tasks: List[WorkflowTask]
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    failure_handling: Dict[str, Any] = field(default_factory=dict)
    sla_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    """Active workflow execution"""

    execution_id: str
    workflow_definition: WorkflowDefinition
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    current_tasks: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceAllocation:
    """Resource allocation for a task"""

    task_id: str
    resource_type: ResourceType
    agent_id: str
    allocated_at: datetime
    estimated_completion: datetime
    priority: int = 1


class WorkflowOrchestrator:
    """Orchestrates self-managing government workflows"""

    def __init__(
        self, decision_engine: DecisionEngine, llm_integration: LLMIntegration
    ):
        self.decision_engine = decision_engine
        self.llm_integration = llm_integration
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.available_agents: Dict[str, Dict[str, Any]] = {}
        self.resource_allocations: List[ResourceAllocation] = []

    async def start_workflow(
        self,
        workflow_definition: WorkflowDefinition,
        initial_context: Dict[str, Any] = None,
    ) -> str:
        """
        Start a new workflow execution

        Args:
            workflow_definition: The workflow to execute
            initial_context: Initial context data

        Returns:
            Execution ID
        """
        try:
            execution_id = f"exec_{workflow_definition.workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            execution = WorkflowExecution(
                execution_id=execution_id,
                workflow_definition=workflow_definition,
                status=WorkflowStatus.PENDING,
                started_at=datetime.now(timezone.utc),
                context=initial_context or {},
            )

            self.active_executions[execution_id] = execution

            # Start the workflow asynchronously
            asyncio.create_task(self._execute_workflow(execution_id))

            logger.info(f"Started workflow execution: {execution_id}")
            return execution_id

        except Exception as e:
            logger.error(f"Error starting workflow: {e}")
            raise DecisionLayerError(f"Failed to start workflow: {e}")

    async def _execute_workflow(self, execution_id: str):
        """Execute a workflow asynchronously"""
        try:
            execution = self.active_executions[execution_id]
            execution.status = WorkflowStatus.RUNNING

            # Optimize workflow dynamically
            await self._optimize_workflow_dynamically(execution)

            # Execute tasks in dependency order
            await self._execute_tasks_in_order(execution)

            # Check if workflow completed successfully
            if all(
                task.status == TaskStatus.COMPLETED
                for task in execution.workflow_definition.tasks
            ):
                execution.status = WorkflowStatus.COMPLETED
                execution.completed_at = datetime.now(timezone.utc)
                logger.info(f"Workflow completed successfully: {execution_id}")
            else:
                execution.status = WorkflowStatus.FAILED
                logger.error(f"Workflow failed: {execution_id}")

        except Exception as e:
            logger.error(f"Error executing workflow {execution_id}: {e}")
            execution = self.active_executions[execution_id]
            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.now(timezone.utc)

    async def _optimize_workflow_dynamically(self, execution: WorkflowExecution):
        """Dynamically optimize workflow based on current conditions"""
        try:
            # Analyze current performance
            performance_data = {
                "execution_time": (
                    datetime.now(timezone.utc) - execution.started_at
                ).total_seconds(),
                "completed_tasks": len(execution.completed_tasks),
                "failed_tasks": len(execution.failed_tasks),
                "available_resources": len(self.available_agents),
                "current_load": len(
                    [
                        a
                        for a in self.resource_allocations
                        if a.estimated_completion > datetime.now(timezone.utc)
                    ]
                ),
            }

            # Use LLM to optimize workflow
            prompt = f"""
            Optimize this government workflow based on current performance data.
            
            Workflow: {execution.workflow_definition.name}
            Performance Data: {json.dumps(performance_data, indent=2)}
            
            Current Tasks: {[task.name for task in execution.workflow_definition.tasks if task.status == TaskStatus.PENDING]}
            
            Suggest optimizations for:
            1. Task sequencing and parallelization
            2. Resource allocation
            3. Priority adjustments
            4. Risk mitigation
            
            Return JSON with optimization recommendations.
            """

            response = await self.llm_integration._call_llm(
                prompt, ReasoningMode.AUTONOMOUS
            )
            optimizations = json.loads(response)

            # Apply optimizations
            await self._apply_workflow_optimizations(execution, optimizations)

        except Exception as e:
            logger.error(f"Error optimizing workflow: {e}")

    async def _apply_workflow_optimizations(
        self, execution: WorkflowExecution, optimizations: Dict[str, Any]
    ):
        """Apply workflow optimizations"""
        # This would implement the actual optimization logic
        # For now, just log the optimizations
        logger.info(
            f"Applied optimizations to workflow {execution.execution_id}: {optimizations}"
        )

    async def _execute_tasks_in_order(self, execution: WorkflowExecution):
        """Execute tasks in dependency order"""
        tasks = execution.workflow_definition.tasks
        completed_tasks = set(execution.completed_tasks)

        while len(completed_tasks) < len(tasks):
            # Find tasks that can be executed (dependencies satisfied)
            ready_tasks = [
                task
                for task in tasks
                if task.task_id not in completed_tasks
                and all(dep in completed_tasks for dep in task.dependencies)
                and task.status == TaskStatus.PENDING
            ]

            if not ready_tasks:
                # Check for deadlock or failure
                remaining_tasks = [
                    task for task in tasks if task.task_id not in completed_tasks
                ]
                if remaining_tasks:
                    logger.error(
                        f"Workflow deadlock detected: {[task.task_id for task in remaining_tasks]}"
                    )
                    break
                else:
                    break

            # Execute ready tasks in parallel
            await asyncio.gather(
                *[self._execute_task(task, execution) for task in ready_tasks],
                return_exceptions=True,
            )

            # Update completed tasks
            completed_tasks.update(
                [task.task_id for task in tasks if task.status == TaskStatus.COMPLETED]
            )

    async def _execute_task(self, task: WorkflowTask, execution: WorkflowExecution):
        """Execute an individual task"""
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now(timezone.utc)

            # Allocate resources
            allocation = await self._allocate_resources(task, execution)
            if not allocation:
                task.status = TaskStatus.FAILED
                task.error_message = "Failed to allocate resources"
                return

            task.assigned_agent = allocation.agent_id

            # Execute the task based on type
            if task.task_type == "decision_function":
                await self._execute_decision_task(task, execution)
            elif task.task_type == "data_processing":
                await self._execute_data_processing_task(task, execution)
            elif task.task_type == "external_api":
                await self._execute_external_api_task(task, execution)
            elif task.task_type == "human_review":
                await self._execute_human_review_task(task, execution)
            else:
                await self._execute_generic_task(task, execution)

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)

            # Update execution context
            execution.context.update(task.output_data)
            execution.completed_tasks.append(task.task_id)

            logger.info(f"Completed task: {task.task_id}")

        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            execution.failed_tasks.append(task.task_id)

    async def _allocate_resources(
        self, task: WorkflowTask, execution: WorkflowExecution
    ) -> Optional[ResourceAllocation]:
        """Allocate resources for a task"""
        try:
            # Find available agents with required capabilities
            required_capabilities = task.required_capabilities
            available_agents = [
                agent_id
                for agent_id, agent_info in self.available_agents.items()
                if all(
                    cap in agent_info.get("capabilities", [])
                    for cap in required_capabilities
                )
                and agent_info.get("status") == "available"
            ]

            if not available_agents:
                logger.warning(f"No available agents for task {task.task_id}")
                return None

            # Select best agent (simple selection for now)
            selected_agent = available_agents[0]

            # Create allocation
            allocation = ResourceAllocation(
                task_id=task.task_id,
                resource_type=ResourceType.AI_AGENT,
                agent_id=selected_agent,
                allocated_at=datetime.now(timezone.utc),
                estimated_completion=datetime.now(timezone.utc)
                + timedelta(minutes=task.estimated_duration),
            )

            self.resource_allocations.append(allocation)

            # Mark agent as busy
            self.available_agents[selected_agent]["status"] = "busy"

            return allocation

        except Exception as e:
            logger.error(f"Error allocating resources for task {task.task_id}: {e}")
            return None

    async def _execute_decision_task(
        self, task: WorkflowTask, execution: WorkflowExecution
    ):
        """Execute a decision function task"""
        try:
            # Get decision function from registry
            function_id = task.input_data.get("function_id")
            if not function_id:
                raise ValueError("Decision function ID not specified")

            # Create decision context
            context = DecisionContext(
                function_id=function_id,
                version=task.input_data.get("version"),
                timestamp=datetime.now(timezone.utc),
                caller="workflow_orchestrator",
                metadata=execution.context,
            )

            # Execute decision function
            result = await self.decision_engine.execute(
                task.input_data.get("input_data", {}), context
            )

            # Store result
            task.output_data = {
                "decision_result": result,
                "execution_time": (
                    datetime.now(timezone.utc) - task.started_at
                ).total_seconds(),
            }

        except Exception as e:
            logger.error(f"Error executing decision task {task.task_id}: {e}")
            raise

    async def _execute_data_processing_task(
        self, task: WorkflowTask, execution: WorkflowExecution
    ):
        """Execute a data processing task"""
        # Mock implementation
        await asyncio.sleep(1)  # Simulate processing time
        task.output_data = {"processed_data": "mock_result"}

    async def _execute_external_api_task(
        self, task: WorkflowTask, execution: WorkflowExecution
    ):
        """Execute an external API task"""
        # Mock implementation
        await asyncio.sleep(2)  # Simulate API call
        task.output_data = {"api_response": "mock_response"}

    async def _execute_human_review_task(
        self, task: WorkflowTask, execution: WorkflowExecution
    ):
        """Execute a human review task"""
        # This would integrate with human workflow systems
        await asyncio.sleep(5)  # Simulate human review time
        task.output_data = {"human_decision": "approved"}

    async def _execute_generic_task(
        self, task: WorkflowTask, execution: WorkflowExecution
    ):
        """Execute a generic task"""
        # Mock implementation
        await asyncio.sleep(1)
        task.output_data = {"generic_result": "completed"}

    async def handle_workflow_exception(
        self, execution_id: str, exception: Exception
    ) -> Dict[str, Any]:
        """Handle workflow exceptions intelligently"""
        try:
            execution = self.active_executions.get(execution_id)
            if not execution:
                return {"error": "Execution not found"}

            # Use LLM to analyze exception and suggest resolution
            prompt = f"""
            Analyze this workflow exception and suggest resolution strategies.
            
            Workflow: {execution.workflow_definition.name}
            Exception: {str(exception)}
            Current Status: {execution.status.value}
            Failed Tasks: {execution.failed_tasks}
            
            Suggest:
            1. Immediate actions to resolve the issue
            2. Alternative approaches
            3. Whether to retry, skip, or abort
            4. Resource reallocation if needed
            
            Return JSON with resolution plan.
            """

            response = await self.llm_integration._call_llm(
                prompt, ReasoningMode.AUTONOMOUS
            )
            resolution_plan = json.loads(response)

            # Apply resolution
            await self._apply_exception_resolution(execution, resolution_plan)

            return resolution_plan

        except Exception as e:
            logger.error(f"Error handling workflow exception: {e}")
            return {"error": f"Failed to handle exception: {e}"}

    async def _apply_exception_resolution(
        self, execution: WorkflowExecution, resolution_plan: Dict[str, Any]
    ):
        """Apply exception resolution plan"""
        # This would implement the actual resolution logic
        logger.info(
            f"Applied exception resolution to workflow {execution.execution_id}: {resolution_plan}"
        )

    async def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get current workflow status"""
        execution = self.active_executions.get(execution_id)
        if not execution:
            return {"error": "Execution not found"}

        return {
            "execution_id": execution_id,
            "workflow_name": execution.workflow_definition.name,
            "status": execution.status.value,
            "started_at": execution.started_at.isoformat(),
            "completed_at": (
                execution.completed_at.isoformat() if execution.completed_at else None
            ),
            "progress": {
                "total_tasks": len(execution.workflow_definition.tasks),
                "completed_tasks": len(execution.completed_tasks),
                "failed_tasks": len(execution.failed_tasks),
                "current_tasks": execution.current_tasks,
            },
            "performance_metrics": execution.performance_metrics,
        }

    def register_agent(
        self, agent_id: str, capabilities: List[str], agent_type: str = "ai"
    ):
        """Register an available agent"""
        self.available_agents[agent_id] = {
            "capabilities": capabilities,
            "agent_type": agent_type,
            "status": "available",
            "registered_at": datetime.now(timezone.utc),
        }
        logger.info(f"Registered agent: {agent_id} with capabilities: {capabilities}")


def create_workflow_orchestrator(
    decision_engine: DecisionEngine, llm_integration: LLMIntegration
) -> WorkflowOrchestrator:
    """Factory function to create workflow orchestrator"""
    return WorkflowOrchestrator(decision_engine, llm_integration)
