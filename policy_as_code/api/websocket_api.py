"""
WebSocket API for Policy as Code Platform
Provides real-time updates for decision execution and system events
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from policy_as_code.core.enhanced_engine import DecisionEngine
from policy_as_code.core.types import DecisionContext, DecisionResult
from policy_as_code.tracing.enhanced_ledger import TraceEntryType


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket):
        """Accept a WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket"""
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_text(message)
            except Exception as e:
                print(f"Error sending message: {e}")
                self.disconnect(websocket)

    async def broadcast(self, message: str):
        """Broadcast a message to all connected WebSockets"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting message: {e}")
                disconnected.append(connection)

        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_to_subscribers(self, topic: str, message: str):
        """Broadcast a message to subscribers of a specific topic"""
        disconnected = []
        for websocket, subscriptions in self.subscriptions.items():
            if topic in subscriptions:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    print(f"Error sending to subscriber: {e}")
                    disconnected.append(websocket)

        # Remove disconnected connections
        for websocket in disconnected:
            self.disconnect(websocket)

    def subscribe(self, websocket: WebSocket, topic: str):
        """Subscribe a WebSocket to a topic"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].add(topic)

    def unsubscribe(self, websocket: WebSocket, topic: str):
        """Unsubscribe a WebSocket from a topic"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].discard(topic)


class WebSocketEventPublisher:
    """Publishes events to WebSocket subscribers"""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    async def publish_decision_execution(
        self, context: DecisionContext, result: DecisionResult
    ):
        """Publish decision execution event"""
        event = {
            "type": "decision_execution",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "trace_id": result.trace_id,
                "function_id": result.function_id,
                "version": result.version,
                "success": result.success,
                "execution_time_ms": result.execution_time_ms,
                "error_message": result.error_message,
            },
        }

        # Broadcast to all subscribers of decision events
        await self.connection_manager.broadcast_to_subscribers(
            "decisions", json.dumps(event)
        )

        # Broadcast to function-specific subscribers
        await self.connection_manager.broadcast_to_subscribers(
            f"function:{result.function_id}", json.dumps(event)
        )

    async def publish_function_registration(self, function_id: str, version: str):
        """Publish function registration event"""
        event = {
            "type": "function_registration",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "function_id": function_id,
                "version": version,
                "action": "registered",
            },
        }

        await self.connection_manager.broadcast_to_subscribers(
            "functions", json.dumps(event)
        )

    async def publish_trace_entry(self, entry_data: Dict[str, Any]):
        """Publish trace entry event"""
        event = {
            "type": "trace_entry",
            "timestamp": datetime.now().isoformat(),
            "data": entry_data,
        }

        await self.connection_manager.broadcast_to_subscribers(
            "trace", json.dumps(event)
        )

    async def publish_system_event(self, event_type: str, data: Dict[str, Any]):
        """Publish system event"""
        event = {
            "type": "system_event",
            "timestamp": datetime.now().isoformat(),
            "data": {"event_type": event_type, **data},
        }

        await self.connection_manager.broadcast_to_subscribers(
            "system", json.dumps(event)
        )


class WebSocketHandler:
    """Handles WebSocket connections and messages"""

    def __init__(self, decision_engine: DecisionEngine):
        self.decision_engine = decision_engine
        self.connection_manager = ConnectionManager()
        self.event_publisher = WebSocketEventPublisher(self.connection_manager)

    async def handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection"""
        await self.connection_manager.connect(websocket)

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                await self._handle_message(websocket, message)

        except WebSocketDisconnect:
            self.connection_manager.disconnect(websocket)
        except Exception as e:
            print(f"WebSocket error: {e}")
            self.connection_manager.disconnect(websocket)

    async def _handle_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        message_type = message.get("type")

        if message_type == "subscribe":
            await self._handle_subscribe(websocket, message)
        elif message_type == "unsubscribe":
            await self._handle_unsubscribe(websocket, message)
        elif message_type == "execute_decision":
            await self._handle_execute_decision(websocket, message)
        elif message_type == "get_status":
            await self._handle_get_status(websocket, message)
        else:
            await self._send_error(websocket, f"Unknown message type: {message_type}")

    async def _handle_subscribe(self, websocket: WebSocket, message: Dict[str, Any]):
        """Handle subscription request"""
        topic = message.get("topic")
        if topic:
            self.connection_manager.subscribe(websocket, topic)
            await self._send_success(websocket, f"Subscribed to {topic}")
        else:
            await self._send_error(websocket, "Topic required for subscription")

    async def _handle_unsubscribe(self, websocket: WebSocket, message: Dict[str, Any]):
        """Handle unsubscription request"""
        topic = message.get("topic")
        if topic:
            self.connection_manager.unsubscribe(websocket, topic)
            await self._send_success(websocket, f"Unsubscribed from {topic}")
        else:
            await self._send_error(websocket, "Topic required for unsubscription")

    async def _handle_execute_decision(
        self, websocket: WebSocket, message: Dict[str, Any]
    ):
        """Handle decision execution request"""
        try:
            function_id = message.get("function_id")
            version = message.get("version", "latest")
            input_data = message.get("input_data", {})

            if not function_id:
                await self._send_error(websocket, "function_id required")
                return

            # Create context
            context = DecisionContext(
                function_id=function_id,
                version=version,
                input_hash="",  # Will be calculated by engine
                timestamp=datetime.now(),
                trace_id="",
            )

            # Execute decision
            result = await self.decision_engine.execute_decision(
                function_id=function_id,
                version=version,
                input_data=input_data,
                context=context,
            )

            # Send result
            response = {
                "type": "decision_result",
                "data": {
                    "trace_id": result.trace_id,
                    "function_id": result.function_id,
                    "version": result.version,
                    "success": result.success,
                    "execution_time_ms": result.execution_time_ms,
                    "result": result.result,
                    "error_message": result.error_message,
                },
            }

            await self.connection_manager.send_personal_message(
                json.dumps(response), websocket
            )

        except Exception as e:
            await self._send_error(websocket, f"Decision execution failed: {str(e)}")

    async def _handle_get_status(self, websocket: WebSocket, message: Dict[str, Any]):
        """Handle status request"""
        try:
            health_data = await self.decision_engine.health_check()

            response = {"type": "status", "data": health_data}

            await self.connection_manager.send_personal_message(
                json.dumps(response), websocket
            )

        except Exception as e:
            await self._send_error(websocket, f"Status request failed: {str(e)}")

    async def _send_success(self, websocket: WebSocket, message: str):
        """Send success message"""
        response = {"type": "success", "message": message}
        await self.connection_manager.send_personal_message(
            json.dumps(response), websocket
        )

    async def _send_error(self, websocket: WebSocket, message: str):
        """Send error message"""
        response = {"type": "error", "message": message}
        await self.connection_manager.send_personal_message(
            json.dumps(response), websocket
        )

    async def publish_decision_event(
        self, context: DecisionContext, result: DecisionResult
    ):
        """Publish decision execution event to WebSocket subscribers"""
        await self.event_publisher.publish_decision_execution(context, result)

    async def publish_function_event(self, function_id: str, version: str):
        """Publish function registration event to WebSocket subscribers"""
        await self.event_publisher.publish_function_registration(function_id, version)

    async def publish_trace_event(self, entry_data: Dict[str, Any]):
        """Publish trace entry event to WebSocket subscribers"""
        await self.event_publisher.publish_trace_entry(entry_data)

    async def publish_system_event(self, event_type: str, data: Dict[str, Any]):
        """Publish system event to WebSocket subscribers"""
        await self.event_publisher.publish_system_event(event_type, data)

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.connection_manager.active_connections)

    def get_subscription_stats(self) -> Dict[str, int]:
        """Get subscription statistics"""
        stats = {}
        for subscriptions in self.connection_manager.subscriptions.values():
            for topic in subscriptions:
                stats[topic] = stats.get(topic, 0) + 1
        return stats
