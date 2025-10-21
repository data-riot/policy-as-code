"""
Python SDK for Policy as Code Platform
Provides easy integration for Python applications
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import httpx
import websockets
from dataclasses import dataclass


@dataclass
class DecisionRequest:
    """Request for decision execution"""

    function_id: str
    version: str = "latest"
    input_data: Dict[str, Any] = None
    trace_id: Optional[str] = None


@dataclass
class DecisionResponse:
    """Response from decision execution"""

    trace_id: str
    function_id: str
    version: str
    result: Dict[str, Any]
    execution_time_ms: int
    timestamp: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class DecisionStats:
    """Decision statistics"""

    total_decisions: int
    success_rate: float
    avg_execution_time: float
    first_decision: Optional[str] = None
    last_decision: Optional[str] = None


class PolicyAsCodeClient:
    """Python SDK client for Policy as Code Platform"""

    def __init__(
        self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    async def execute_decision(self, request: DecisionRequest) -> DecisionResponse:
        """Execute a decision function"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/decisions",
                json={
                    "function_id": request.function_id,
                    "version": request.version,
                    "input_data": request.input_data or {},
                    "trace_id": request.trace_id,
                },
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()

            data = response.json()
            return DecisionResponse(
                trace_id=data["trace_id"],
                function_id=data["function_id"],
                version=data["version"],
                result=data["result"],
                execution_time_ms=data["execution_time_ms"],
                timestamp=data["timestamp"],
                success=data["success"],
                error_message=data.get("error_message"),
            )

    async def get_decision(self, trace_id: str) -> DecisionResponse:
        """Get a decision result by trace ID"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/decisions/{trace_id}", headers=self.headers
            )
            response.raise_for_status()

            data = response.json()
            return DecisionResponse(
                trace_id=data["trace_id"],
                function_id=data["function_id"],
                version=data["version"],
                result=data["result"],
                execution_time_ms=data["execution_time_ms"],
                timestamp=data["timestamp"],
                success=data["success"],
                error_message=data.get("error_message"),
            )

    async def get_functions(self) -> List[Dict[str, Any]]:
        """Get all registered functions"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/functions", headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_decision_history(
        self, function_id: str, limit: int = 100, offset: int = 0
    ) -> List[DecisionResponse]:
        """Get decision history for a function"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/functions/{function_id}/history",
                params={"limit": limit, "offset": offset},
                headers=self.headers,
            )
            response.raise_for_status()

            data = response.json()
            return [
                DecisionResponse(
                    trace_id=item["trace_id"],
                    function_id=item["function_id"],
                    version=item["version"],
                    result=item["result"],
                    execution_time_ms=item["execution_time_ms"],
                    timestamp=item["timestamp"],
                    success=item["success"],
                    error_message=item.get("error_message"),
                )
                for item in data["history"]
            ]

    async def get_decision_stats(self, function_id: str) -> DecisionStats:
        """Get decision statistics for a function"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/functions/{function_id}/stats", headers=self.headers
            )
            response.raise_for_status()

            data = response.json()
            return DecisionStats(
                total_decisions=data["total_decisions"],
                success_rate=data["success_rate"],
                avg_execution_time=data["avg_execution_time"],
                first_decision=data.get("first_decision"),
                last_decision=data.get("last_decision"),
            )

    async def health_check(self) -> Dict[str, Any]:
        """Get system health status"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health", headers=self.headers)
            response.raise_for_status()
            return response.json()


class GraphQLClient:
    """GraphQL client for Policy as Code Platform"""

    def __init__(
        self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    async def execute_query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a GraphQL query"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/graphql",
                json={"query": query, "variables": variables or {}},
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()

            data = response.json()
            if "errors" in data:
                raise Exception(f"GraphQL errors: {data['errors']}")

            return data["data"]

    async def execute_decision(
        self, function_id: str, input_data: Dict[str, Any], version: str = "latest"
    ) -> DecisionResponse:
        """Execute a decision using GraphQL"""
        query = """
        mutation ExecuteDecision($request: DecisionRequestInput!) {
            executeDecision(request: $request) {
                traceId
                functionId
                version
                executionTimeMs
                timestamp
                success
                errorMessage
            }
        }
        """

        variables = {
            "request": {
                "function_id": function_id,
                "version": version,
                "input_data": input_data,
            }
        }

        result = await self.execute_query(query, variables)
        decision_data = result["executeDecision"]

        return DecisionResponse(
            trace_id=decision_data["traceId"],
            function_id=decision_data["functionId"],
            version=decision_data["version"],
            result={},  # GraphQL mutation doesn't return full result
            execution_time_ms=decision_data["executionTimeMs"],
            timestamp=decision_data["timestamp"],
            success=decision_data["success"],
            error_message=decision_data.get("errorMessage"),
        )

    async def get_decision_history(
        self, function_id: str, limit: int = 100, offset: int = 0
    ) -> List[DecisionResponse]:
        """Get decision history using GraphQL"""
        query = """
        query GetDecisionHistory($functionId: String!, $limit: Int!, $offset: Int!) {
            decisionHistory(functionId: $functionId, limit: $limit, offset: $offset) {
                traceId
                functionId
                version
                executionTimeMs
                timestamp
                success
                errorMessage
            }
        }
        """

        variables = {"functionId": function_id, "limit": limit, "offset": offset}

        result = await self.execute_query(query, variables)
        history_data = result["decisionHistory"]

        return [
            DecisionResponse(
                trace_id=item["traceId"],
                function_id=item["functionId"],
                version=item["version"],
                result={},  # GraphQL query doesn't return full result
                execution_time_ms=item["executionTimeMs"],
                timestamp=item["timestamp"],
                success=item["success"],
                error_message=item.get("errorMessage"),
            )
            for item in history_data
        ]


class WebSocketClient:
    """WebSocket client for Policy as Code Platform"""

    def __init__(
        self, base_url: str = "ws://localhost:8000", api_key: Optional[str] = None
    ):
        self.base_url = base_url.replace("http://", "ws://").replace(
            "https://", "wss://"
        )
        self.api_key = api_key
        self.websocket = None
        self.subscriptions = set()

    async def connect(self):
        """Connect to WebSocket"""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.websocket = await websockets.connect(
            f"{self.base_url}/ws", extra_headers=headers
        )

    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def subscribe(self, topic: str):
        """Subscribe to a topic"""
        if not self.websocket:
            await self.connect()

        message = {"type": "subscribe", "topic": topic}

        await self.websocket.send(json.dumps(message))
        self.subscriptions.add(topic)

    async def unsubscribe(self, topic: str):
        """Unsubscribe from a topic"""
        if not self.websocket:
            return

        message = {"type": "unsubscribe", "topic": topic}

        await self.websocket.send(json.dumps(message))
        self.subscriptions.discard(topic)

    async def execute_decision(
        self, function_id: str, input_data: Dict[str, Any], version: str = "latest"
    ) -> DecisionResponse:
        """Execute a decision via WebSocket"""
        if not self.websocket:
            await self.connect()

        message = {
            "type": "execute_decision",
            "function_id": function_id,
            "version": version,
            "input_data": input_data,
        }

        await self.websocket.send(json.dumps(message))

        # Wait for response
        response_data = await self.websocket.recv()
        response = json.loads(response_data)

        if response["type"] == "error":
            raise Exception(response["message"])

        decision_data = response["data"]
        return DecisionResponse(
            trace_id=decision_data["trace_id"],
            function_id=decision_data["function_id"],
            version=decision_data["version"],
            result=decision_data["result"],
            execution_time_ms=decision_data["execution_time_ms"],
            timestamp=datetime.now().isoformat(),
            success=decision_data["success"],
            error_message=decision_data.get("error_message"),
        )

    async def listen_for_events(self, callback):
        """Listen for events and call callback with each event"""
        if not self.websocket:
            await self.connect()

        try:
            while True:
                message_data = await self.websocket.recv()
                message = json.loads(message_data)
                await callback(message)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
        except Exception as e:
            print(f"WebSocket error: {e}")


# Convenience functions for easy usage
async def execute_decision(
    function_id: str,
    input_data: Dict[str, Any],
    base_url: str = "http://localhost:8000",
    version: str = "latest",
    api_key: Optional[str] = None,
) -> DecisionResponse:
    """Convenience function to execute a decision"""
    client = PolicyAsCodeClient(base_url, api_key)
    request = DecisionRequest(
        function_id=function_id, version=version, input_data=input_data
    )
    return await client.execute_decision(request)


def execute_decision_sync(
    function_id: str,
    input_data: Dict[str, Any],
    base_url: str = "http://localhost:8000",
    version: str = "latest",
    api_key: Optional[str] = None,
) -> DecisionResponse:
    """Synchronous convenience function to execute a decision"""
    return asyncio.run(
        execute_decision(function_id, input_data, base_url, version, api_key)
    )
