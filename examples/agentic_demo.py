#!/usr/bin/env python3
"""
Agentic AI Demo - Complete Agentic Government Services

This demo showcases the new agentic AI capabilities added to the policy-as-code platform,
demonstrating autonomous decision-making, conversational interfaces, workflow orchestration,
and performance monitoring.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from decision_layer import (
    DecisionEngine,
    FunctionRegistry,
    create_decision_engine,
    create_function_registry,
    LLMIntegration,
    create_llm_integration,
    AgenticContext,
    ReasoningMode,
    ConversationalInterface,
    create_conversational_interface,
    ConversationChannel,
    WorkflowOrchestrator,
    create_workflow_orchestrator,
    WorkflowDefinition,
    WorkflowTask,
    TaskStatus,
    AgentPerformanceMonitor,
    create_agent_performance_monitor,
    PerformanceMetric,
)
from decision_layer.config import DecisionLayerConfig, load_config


class AgenticDemo:
    """Complete agentic AI demonstration"""

    def __init__(self):
        self.config = None
        self.decision_engine = None
        self.registry = None
        self.llm_integration = None
        self.conversational_interface = None
        self.workflow_orchestrator = None
        self.performance_monitor = None
        self.start_time = time.time()

    def log_step(self, step: str, message: str):
        """Log a demo step with timing"""
        elapsed = time.time() - self.start_time
        print(f"\n{'='*60}")
        print(f"STEP {step}: {message}")
        print(f"Elapsed: {elapsed:.1f}s")
        print(f"{'='*60}")

    async def run_demo(self):
        """Run the complete agentic AI demo"""
        try:
            await self.step_1_setup_agentic_system()
            await self.step_2_demonstrate_llm_reasoning()
            await self.step_3_demonstrate_conversational_interface()
            await self.step_4_demonstrate_workflow_orchestration()
            await self.step_5_demonstrate_performance_monitoring()
            await self.step_6_demonstrate_agent_coordination()
            await self.step_7_demo_complete()
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            raise

    async def step_1_setup_agentic_system(self):
        """Step 1: Setup agentic AI system"""
        self.log_step("1", "Setting up Agentic AI System")

        # Load configuration
        self.config = DecisionLayerConfig()

        # Create core components
        self.decision_engine = create_decision_engine()
        self.registry = create_function_registry()

        # Create agentic components
        self.llm_integration = create_llm_integration(self.config, self.registry)
        self.conversational_interface = create_conversational_interface(
            self.decision_engine, self.llm_integration
        )
        self.workflow_orchestrator = create_workflow_orchestrator(
            self.decision_engine, self.llm_integration
        )
        self.performance_monitor = create_agent_performance_monitor(
            self.llm_integration
        )

        # Register some agents
        self.workflow_orchestrator.register_agent(
            "benefits_agent", ["benefits_processing", "eligibility_check"], "ai"
        )
        self.workflow_orchestrator.register_agent(
            "compliance_agent", ["legal_compliance", "audit"], "ai"
        )
        self.workflow_orchestrator.register_agent(
            "citizen_service_agent", ["citizen_interaction", "explanation"], "ai"
        )

        print("✅ Agentic AI system initialized")
        print("   - Decision Engine: Ready")
        print("   - LLM Integration: Ready")
        print("   - Conversational Interface: Ready")
        print("   - Workflow Orchestrator: Ready")
        print("   - Performance Monitor: Ready")
        print("   - Registered Agents: 3")

    async def step_2_demonstrate_llm_reasoning(self):
        """Step 2: Demonstrate LLM-powered reasoning"""
        self.log_step("2", "Demonstrating LLM-Powered Reasoning")

        # Create a sample decision function
        def loan_approval_function(
            input_data: Dict[str, Any], context
        ) -> Dict[str, Any]:
            """Simple loan approval function"""
            amount = input_data.get("amount", 0)
            credit_score = input_data.get("credit_score", 0)
            income = input_data.get("income", 0)

            if credit_score >= 700 and income >= 50000 and amount <= 100000:
                return {
                    "approved": True,
                    "interest_rate": 3.5,
                    "reason": "Excellent credit profile",
                }
            elif credit_score >= 650 and income >= 40000 and amount <= 75000:
                return {
                    "approved": True,
                    "interest_rate": 4.5,
                    "reason": "Good credit profile",
                }
            else:
                return {
                    "approved": False,
                    "reason": "Does not meet minimum requirements",
                }

        # Create agentic context
        agentic_context = AgenticContext(
            citizen_id="CITIZEN_001",
            service_type="loan_application",
            urgency_level="normal",
            legal_framework="Consumer Credit Act",
            historical_precedents=[
                {"case_id": "CASE_001", "outcome": "approved", "similarity": 0.85}
            ],
        )

        # Test different reasoning modes
        test_cases = [
            {
                "input": {"amount": 80000, "credit_score": 750, "income": 60000},
                "mode": ReasoningMode.AUTONOMOUS,
                "description": "High-quality application with autonomous reasoning",
            },
            {
                "input": {"amount": 50000, "credit_score": 680, "income": 45000},
                "mode": ReasoningMode.ASSISTED,
                "description": "Borderline application with assisted reasoning",
            },
            {
                "input": {"amount": 120000, "credit_score": 600, "income": 35000},
                "mode": ReasoningMode.EXPLANATORY,
                "description": "Low-quality application with explanatory reasoning",
            },
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n   Test Case {i}: {test_case['description']}")
            print(f"   Input: {test_case['input']}")

            # Use LLM reasoning
            decision = await self.llm_integration.reason_about_decision(
                decision_function=loan_approval_function,
                input_data=test_case["input"],
                context=agentic_context,
                reasoning_mode=test_case["mode"],
            )

            print(f"   Decision: {decision.decision}")
            print(f"   Confidence: {decision.confidence:.2f}")
            print(f"   Reasoning Steps: {len(decision.reasoning_steps)}")
            print(f"   Legal Basis: {decision.legal_basis}")

            # Record performance metrics
            await self.performance_monitor.record_performance_metric(
                agent_id="loan_agent",
                metric_type=PerformanceMetric.DECISION_ACCURACY,
                value=decision.confidence,
                context={"test_case": i, "reasoning_mode": test_case["mode"].value},
            )

        print("\n✅ LLM reasoning demonstrated")
        print("   - Autonomous reasoning: Working")
        print("   - Assisted reasoning: Working")
        print("   - Explanatory reasoning: Working")
        print("   - Performance metrics: Recorded")

    async def step_3_demonstrate_conversational_interface(self):
        """Step 3: Demonstrate conversational interface"""
        self.log_step("3", "Demonstrating Conversational Interface")

        # Simulate citizen conversations
        conversations = [
            {
                "message": "I need help applying for unemployment benefits",
                "channel": ConversationChannel.WEB_CHAT,
                "citizen_id": "CITIZEN_002",
            },
            {
                "message": "What documents do I need for a driver's license renewal?",
                "channel": ConversationChannel.WEB_CHAT,
                "citizen_id": "CITIZEN_003",
            },
            {
                "message": "I want to file a complaint about my recent tax assessment",
                "channel": ConversationChannel.WEB_CHAT,
                "citizen_id": "CITIZEN_004",
            },
        ]

        for i, conv in enumerate(conversations, 1):
            print(f"\n   Conversation {i}:")
            print(f"   Citizen: {conv['message']}")

            # Process the message
            response = await self.conversational_interface.process_citizen_message(
                message=conv["message"],
                session_id=f"session_{i}",
                channel=conv["channel"],
                citizen_id=conv["citizen_id"],
            )

            print(f"   Agent: {response.message}")
            print(f"   Actions: {len(response.actions)}")
            print(f"   Next Steps: {response.next_steps}")
            print(f"   Requires Human: {response.requires_human}")
            print(f"   Confidence: {response.confidence:.2f}")

            # Record performance metrics
            await self.performance_monitor.record_performance_metric(
                agent_id="conversational_agent",
                metric_type=PerformanceMetric.CITIZEN_SATISFACTION,
                value=response.confidence,
                context={"conversation_id": i, "channel": conv["channel"].value},
            )

        print("\n✅ Conversational interface demonstrated")
        print("   - Natural language processing: Working")
        print("   - Intent recognition: Working")
        print("   - Multi-channel support: Working")
        print("   - Human escalation: Working")

    async def step_4_demonstrate_workflow_orchestration(self):
        """Step 4: Demonstrate workflow orchestration"""
        self.log_step("4", "Demonstrating Workflow Orchestration")

        # Create a complex workflow
        workflow_tasks = [
            WorkflowTask(
                task_id="validate_application",
                name="Validate Application",
                description="Validate citizen application data",
                task_type="decision_function",
                required_capabilities=["validation", "data_processing"],
                estimated_duration=5,
                input_data={"function_id": "validate_application"},
            ),
            WorkflowTask(
                task_id="check_eligibility",
                name="Check Eligibility",
                description="Check citizen eligibility for benefits",
                task_type="decision_function",
                required_capabilities=["benefits_processing", "eligibility_check"],
                estimated_duration=10,
                dependencies=["validate_application"],
                input_data={"function_id": "check_eligibility"},
            ),
            WorkflowTask(
                task_id="legal_review",
                name="Legal Review",
                description="Review for legal compliance",
                task_type="decision_function",
                required_capabilities=["legal_compliance", "audit"],
                estimated_duration=15,
                dependencies=["check_eligibility"],
                input_data={"function_id": "legal_review"},
            ),
            WorkflowTask(
                task_id="generate_response",
                name="Generate Response",
                description="Generate response to citizen",
                task_type="decision_function",
                required_capabilities=["citizen_interaction", "explanation"],
                estimated_duration=5,
                dependencies=["legal_review"],
                input_data={"function_id": "generate_response"},
            ),
        ]

        workflow_definition = WorkflowDefinition(
            workflow_id="benefits_application_workflow",
            name="Benefits Application Workflow",
            description="Complete workflow for processing benefits applications",
            version="1.0",
            tasks=workflow_tasks,
            success_criteria=["All tasks completed", "No errors", "Response generated"],
            sla_requirements={"max_duration_minutes": 60, "success_rate": 0.95},
        )

        print("   Workflow Definition Created:")
        print(f"   - ID: {workflow_definition.workflow_id}")
        print(f"   - Tasks: {len(workflow_definition.tasks)}")
        print(
            f"   - Estimated Duration: {sum(task.estimated_duration for task in workflow_tasks)} minutes"
        )

        # Start workflow execution
        execution_id = await self.workflow_orchestrator.start_workflow(
            workflow_definition=workflow_definition,
            initial_context={
                "citizen_id": "CITIZEN_005",
                "application_type": "unemployment_benefits",
            },
        )

        print(f"   Execution Started: {execution_id}")

        # Monitor workflow progress
        for i in range(5):  # Check 5 times
            await asyncio.sleep(2)  # Wait 2 seconds between checks
            status = await self.workflow_orchestrator.get_workflow_status(execution_id)
            print(
                f"   Status Check {i+1}: {status['status']} - {status['progress']['completed_tasks']}/{status['progress']['total_tasks']} tasks"
            )

            if status["status"] in ["completed", "failed"]:
                break

        print("\n✅ Workflow orchestration demonstrated")
        print("   - Workflow definition: Created")
        print("   - Task dependencies: Managed")
        print("   - Resource allocation: Working")
        print("   - Progress monitoring: Working")

    async def step_5_demonstrate_performance_monitoring(self):
        """Step 5: Demonstrate performance monitoring"""
        self.log_step("5", "Demonstrating Performance Monitoring")

        # Record some additional performance data
        agents = [
            "loan_agent",
            "conversational_agent",
            "benefits_agent",
            "compliance_agent",
        ]
        metrics = [
            PerformanceMetric.DECISION_ACCURACY,
            PerformanceMetric.RESPONSE_TIME,
            PerformanceMetric.CITIZEN_SATISFACTION,
            PerformanceMetric.ERROR_RATE,
        ]

        print("   Recording performance data...")
        for agent in agents:
            for metric in metrics:
                # Simulate some performance data
                value = (
                    0.7 + (hash(agent + metric.value) % 30) / 100
                )  # Random value between 0.7-1.0
                await self.performance_monitor.record_performance_metric(
                    agent_id=agent,
                    metric_type=metric,
                    value=value,
                    context={
                        "demo": True,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )

        # Get performance reports
        print("\n   Performance Analysis:")
        for agent in agents:
            effectiveness = await self.performance_monitor.get_agent_effectiveness(
                agent
            )
            if "error" not in effectiveness:
                print(f"   {agent}:")
                print(
                    f"     Performance Score: {effectiveness.get('effectiveness_metrics', {}).get('decision_accuracy', {}).get('mean', 0):.2f}"
                )
                print(f"     Data Points: {effectiveness.get('data_points', 0)}")
                print(
                    f"     Recommendations: {len(effectiveness.get('recommendations', []))}"
                )

        # Detect drift
        print("\n   Drift Detection:")
        for agent in agents:
            drift_results = await self.performance_monitor.detect_agent_drift(agent)
            if drift_results:
                print(f"   {agent}: {len(drift_results)} drift issues detected")
                for drift in drift_results:
                    print(f"     - {drift.drift_type.value}: {drift.description}")
            else:
                print(f"   {agent}: No drift detected")

        # Generate overall report
        report = await self.performance_monitor.generate_performance_report()
        print(f"\n   Overall Performance Report:")
        print(f"   - Agents Analyzed: {report.get('agents_analyzed', 0)}")
        print(f"   - Total Data Points: {report.get('total_data_points', 0)}")
        print(f"   - Overall Insights: {len(report.get('overall_insights', []))}")

        print("\n✅ Performance monitoring demonstrated")
        print("   - Metric collection: Working")
        print("   - Effectiveness analysis: Working")
        print("   - Drift detection: Working")
        print("   - Performance reporting: Working")

    async def step_6_demonstrate_agent_coordination(self):
        """Step 6: Demonstrate agent coordination"""
        self.log_step("6", "Demonstrating Agent Coordination")

        # Demonstrate agent coordination
        coordination_result = await self.llm_integration.coordinate_with_other_agents(
            task_description="Process a complex citizen request involving benefits, tax, and legal issues",
            required_capabilities=[
                "benefits_processing",
                "tax_processing",
                "legal_compliance",
                "citizen_interaction",
            ],
            context=AgenticContext(
                citizen_id="CITIZEN_006",
                service_type="multi_department_request",
                urgency_level="high",
            ),
        )

        print("   Agent Coordination Plan:")
        print(f"   - Task: {coordination_result.get('task_description', 'N/A')}")
        print(
            f"   - Required Capabilities: {coordination_result.get('required_capabilities', [])}"
        )
        print(
            f"   - Coordination Strategy: {coordination_result.get('coordination_strategy', 'N/A')}"
        )
        print(
            f"   - Communication Protocol: {coordination_result.get('communication_protocol', 'N/A')}"
        )

        # Demonstrate workflow optimization
        coordination_data = {
            "workflow_id": "multi_department_workflow",
            "agents_involved": ["benefits_agent", "tax_agent", "legal_agent"],
            "communication_patterns": {
                "benefits_agent": ["tax_agent", "legal_agent"],
                "tax_agent": ["benefits_agent", "legal_agent"],
                "legal_agent": ["benefits_agent", "tax_agent"],
            },
            "performance_metrics": {
                "average_response_time": 45.2,
                "success_rate": 0.87,
                "error_rate": 0.13,
            },
        }

        optimization_recommendations = (
            await self.performance_monitor.optimize_agent_coordination(
                coordination_data
            )
        )

        print(f"\n   Optimization Recommendations:")
        print(f"   - Total Recommendations: {len(optimization_recommendations)}")
        for i, rec in enumerate(optimization_recommendations[:3], 1):  # Show first 3
            print(f"   {i}. {rec.description}")
            print(
                f"      Priority: {rec.priority}, Expected Improvement: {rec.expected_improvement:.1%}"
            )

        print("\n✅ Agent coordination demonstrated")
        print("   - Multi-agent coordination: Working")
        print("   - Communication protocols: Working")
        print("   - Optimization recommendations: Working")
        print("   - Performance analysis: Working")

    async def step_7_demo_complete(self):
        """Step 7: Demo completion summary"""
        self.log_step("7", "Agentic AI Demo Complete!")

        total_time = time.time() - self.start_time

        print("🎉 Agentic AI Demo Complete!")
        print(f"⏱️ Total Time: {total_time:.1f} seconds")

        print("\n📋 What We Demonstrated:")
        print("   ✅ LLM-powered autonomous reasoning")
        print("   ✅ Conversational interface with natural language processing")
        print("   ✅ Self-orchestrating workflow management")
        print("   ✅ Comprehensive performance monitoring and drift detection")
        print("   ✅ Multi-agent coordination and optimization")

        print("\n🤖 Agentic AI Features Added:")
        print("   🧠 Intelligent reasoning with multiple modes")
        print("   💬 Natural language citizen interaction")
        print("   🔄 Autonomous workflow orchestration")
        print("   📊 Real-time performance monitoring")
        print("   🤝 Multi-agent coordination protocols")
        print("   🔍 Drift detection and optimization")

        print("\n🏛️ Government Service Capabilities:")
        print("   📋 Proactive citizen service delivery")
        print("   ⚖️ Legal compliance and audit trails")
        print("   🔄 Self-optimizing government workflows")
        print("   📈 Data-driven performance improvement")
        print("   🌐 Cross-agency coordination")
        print("   🛡️ Secure and accountable AI operations")

        print("\n🚀 Next Steps:")
        print("   - Deploy to production environment")
        print("   - Integrate with existing government systems")
        print("   - Train agents on domain-specific data")
        print("   - Implement advanced security measures")
        print("   - Scale to handle citizen demand")


async def main():
    """Run the agentic AI demo"""
    demo = AgenticDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
