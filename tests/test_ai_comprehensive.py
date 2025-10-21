"""
Comprehensive test suite for AI and workflow components
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from policy_as_code.ai.llm import LLMIntegration, LLMConfig
from policy_as_code.ai.workflow import WorkflowOrchestrator, WorkflowStep
from policy_as_code.ai.monitoring import PerformanceMonitor, DriftDetector
from policy_as_code.ai.conversational import ConversationalInterface


class TestLLMIntegration:
    """Test LLM integration functionality"""

    @pytest.fixture
    def llm_config(self):
        """Create test LLM configuration"""
        return LLMConfig(
            provider="mock", api_key="test_key", model="test_model", temperature=0.7
        )

    @pytest.fixture
    def llm_integration(self, llm_config):
        """Create test LLM integration"""
        return LLMIntegration(llm_config)

    @pytest.mark.asyncio
    async def test_generate_decision_function(self, llm_integration):
        """Test generating decision function from natural language"""
        policy_description = "Approve loans for users with credit score > 700"

        with patch.object(
            llm_integration,
            "_call_llm",
            return_value="async def loan_approval(input_data, context): return {'decision': 'approved'}",
        ):
            result = await llm_integration.generate_decision_function(
                policy_description
            )

            assert result is not None
            assert "async def" in result

    @pytest.mark.asyncio
    async def test_explain_decision(self, llm_integration):
        """Test explaining a decision"""
        decision_result = {
            "decision": "approved",
            "confidence": 0.95,
            "reasoning": "High credit score",
        }

        with patch.object(
            llm_integration,
            "_call_llm",
            return_value="The loan was approved because the applicant has a high credit score of 750, which exceeds the minimum requirement of 700.",
        ):
            result = await llm_integration.explain_decision(decision_result)

            assert result is not None
            assert "approved" in result.lower()

    @pytest.mark.asyncio
    async def test_process_natural_language_query(self, llm_integration):
        """Test processing natural language queries"""
        query = "What are the requirements for loan approval?"

        with patch.object(
            llm_integration,
            "_call_llm",
            return_value="Loan approval requires a credit score of at least 700 and income verification.",
        ):
            result = await llm_integration.process_query(query)

            assert result is not None
            assert "credit score" in result.lower()


class TestWorkflowOrchestrator:
    """Test workflow orchestrator functionality"""

    @pytest.fixture
    def workflow_orchestrator(self):
        """Create test workflow orchestrator"""
        return WorkflowOrchestrator()

    @pytest.fixture
    def sample_workflow_steps(self):
        """Create sample workflow steps"""
        return [
            WorkflowStep(
                step_id="validate_input",
                function_id="input_validator",
                dependencies=[],
                timeout=30,
            ),
            WorkflowStep(
                step_id="check_eligibility",
                function_id="eligibility_checker",
                dependencies=["validate_input"],
                timeout=60,
            ),
            WorkflowStep(
                step_id="make_decision",
                function_id="decision_maker",
                dependencies=["check_eligibility"],
                timeout=30,
            ),
        ]

    @pytest.mark.asyncio
    async def test_execute_workflow(self, workflow_orchestrator, sample_workflow_steps):
        """Test executing a workflow"""
        workflow_id = "loan_approval_workflow"
        input_data = {"amount": 5000, "credit_score": 750}

        # Mock step execution
        with patch.object(
            workflow_orchestrator,
            "_execute_step",
            return_value={"status": "completed", "result": "success"},
        ):
            result = await workflow_orchestrator.execute_workflow(
                workflow_id=workflow_id,
                steps=sample_workflow_steps,
                input_data=input_data,
            )

            assert result is not None
            assert result["workflow_id"] == workflow_id
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_workflow_with_failure(
        self, workflow_orchestrator, sample_workflow_steps
    ):
        """Test workflow execution with step failure"""
        workflow_id = "failing_workflow"
        input_data = {"amount": 5000, "credit_score": 650}

        # Mock step failure
        with patch.object(
            workflow_orchestrator, "_execute_step", side_effect=Exception("Step failed")
        ):
            result = await workflow_orchestrator.execute_workflow(
                workflow_id=workflow_id,
                steps=sample_workflow_steps,
                input_data=input_data,
            )

            assert result["status"] == "failed"
            assert "error" in result

    @pytest.mark.asyncio
    async def test_parallel_step_execution(self, workflow_orchestrator):
        """Test parallel step execution"""
        parallel_steps = [
            WorkflowStep(
                step_id="step1", function_id="function1", dependencies=[], timeout=30
            ),
            WorkflowStep(
                step_id="step2", function_id="function2", dependencies=[], timeout=30
            ),
        ]

        with patch.object(
            workflow_orchestrator, "_execute_step", return_value={"status": "completed"}
        ):
            result = await workflow_orchestrator.execute_workflow(
                workflow_id="parallel_workflow", steps=parallel_steps, input_data={}
            )

            assert result["status"] == "completed"


class TestPerformanceMonitor:
    """Test performance monitoring functionality"""

    @pytest.fixture
    def performance_monitor(self):
        """Create test performance monitor"""
        return PerformanceMonitor()

    @pytest.mark.asyncio
    async def test_record_execution_metrics(self, performance_monitor):
        """Test recording execution metrics"""
        function_id = "test_function"
        execution_time = 0.5
        success = True

        await performance_monitor.record_execution(
            function_id=function_id, execution_time=execution_time, success=success
        )

        metrics = await performance_monitor.get_metrics(function_id)
        assert metrics["total_executions"] == 1
        assert metrics["success_rate"] == 1.0
        assert metrics["avg_execution_time"] == execution_time

    @pytest.mark.asyncio
    async def test_detect_performance_degradation(self, performance_monitor):
        """Test detecting performance degradation"""
        function_id = "test_function"

        # Record normal performance
        for _ in range(10):
            await performance_monitor.record_execution(
                function_id=function_id, execution_time=0.1, success=True
            )

        # Record degraded performance
        for _ in range(5):
            await performance_monitor.record_execution(
                function_id=function_id, execution_time=2.0, success=True  # Much slower
            )

        degradation = await performance_monitor.detect_degradation(function_id)
        assert degradation["detected"] is True
        assert degradation["severity"] == "high"


class TestDriftDetector:
    """Test drift detection functionality"""

    @pytest.fixture
    def drift_detector(self):
        """Create test drift detector"""
        return DriftDetector()

    @pytest.mark.asyncio
    async def test_detect_output_drift(self, drift_detector):
        """Test detecting output drift"""
        function_id = "test_function"

        # Baseline data
        baseline_outputs = ["approved", "approved", "rejected", "approved"]

        # New data with drift
        new_outputs = ["rejected", "rejected", "rejected", "rejected"]

        drift_result = await drift_detector.detect_output_drift(
            function_id=function_id,
            baseline_outputs=baseline_outputs,
            new_outputs=new_outputs,
        )

        assert drift_result["drift_detected"] is True
        assert drift_result["drift_score"] > 0.5

    @pytest.mark.asyncio
    async def test_detect_input_drift(self, drift_detector):
        """Test detecting input drift"""
        function_id = "test_function"

        # Baseline inputs
        baseline_inputs = [
            {"credit_score": 750, "amount": 5000},
            {"credit_score": 800, "amount": 3000},
            {"credit_score": 700, "amount": 7000},
        ]

        # New inputs with drift
        new_inputs = [
            {"credit_score": 600, "amount": 10000},
            {"credit_score": 650, "amount": 15000},
            {"credit_score": 550, "amount": 20000},
        ]

        drift_result = await drift_detector.detect_input_drift(
            function_id=function_id,
            baseline_inputs=baseline_inputs,
            new_inputs=new_inputs,
        )

        assert drift_result["drift_detected"] is True


class TestConversationalInterface:
    """Test conversational interface functionality"""

    @pytest.fixture
    def conversational_interface(self):
        """Create test conversational interface"""
        return ConversationalInterface()

    @pytest.mark.asyncio
    async def test_process_citizen_query(self, conversational_interface):
        """Test processing citizen queries"""
        query = "Why was my loan application rejected?"
        context = {"user_id": "123", "application_id": "app_456"}

        with patch.object(
            conversational_interface,
            "_generate_response",
            return_value="Your loan application was rejected because your credit score of 650 is below the minimum requirement of 700.",
        ):
            result = await conversational_interface.process_query(query, context)

            assert result is not None
            assert "rejected" in result.lower()

    @pytest.mark.asyncio
    async def test_handle_complex_query(self, conversational_interface):
        """Test handling complex queries"""
        query = "I want to understand the loan approval process and what I can do to improve my chances"
        context = {"user_id": "123"}

        with patch.object(
            conversational_interface,
            "_generate_response",
            return_value="The loan approval process considers your credit score, income, and debt-to-income ratio. To improve your chances, you can work on improving your credit score and reducing your existing debt.",
        ):
            result = await conversational_interface.process_query(query, context)

            assert result is not None
            assert len(result) > 50  # Should be a substantial response


class TestAIIntegration:
    """Test AI integration scenarios"""

    @pytest.fixture
    def llm_integration(self):
        """Create LLM integration for integration tests"""
        config = LLMConfig(provider="mock", api_key="test_key", model="test_model")
        return LLMIntegration(config)

    @pytest.fixture
    def workflow_orchestrator(self):
        """Create workflow orchestrator for integration tests"""
        return WorkflowOrchestrator()

    @pytest.mark.asyncio
    async def test_ai_powered_decision_workflow(
        self, llm_integration, workflow_orchestrator
    ):
        """Test AI-powered decision workflow"""
        # Generate decision function using LLM
        policy_description = (
            "Approve loans for users with credit score > 700 and income > 50000"
        )

        with patch.object(
            llm_integration,
            "_call_llm",
            return_value="async def loan_approval(input_data, context): return {'decision': 'approved' if input_data.get('credit_score', 0) > 700 and input_data.get('income', 0) > 50000 else 'rejected'}",
        ):
            decision_function = await llm_integration.generate_decision_function(
                policy_description
            )

            assert decision_function is not None

        # Execute workflow with AI-generated function
        workflow_steps = [
            WorkflowStep(
                step_id="ai_decision",
                function_id="ai_generated_function",
                dependencies=[],
                timeout=30,
            )
        ]

        with patch.object(
            workflow_orchestrator,
            "_execute_step",
            return_value={"status": "completed", "result": {"decision": "approved"}},
        ):
            result = await workflow_orchestrator.execute_workflow(
                workflow_id="ai_workflow",
                steps=workflow_steps,
                input_data={"credit_score": 750, "income": 60000},
            )

            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_explainable_ai_decision(self, llm_integration):
        """Test explainable AI decision making"""
        decision_result = {
            "decision": "approved",
            "confidence": 0.95,
            "reasoning": "High credit score and sufficient income",
            "metadata": {"credit_score": 750, "income": 60000},
        }

        with patch.object(
            llm_integration,
            "_call_llm",
            return_value="Your loan application was approved because you have an excellent credit score of 750, which is well above our minimum requirement of 700, and your annual income of $60,000 provides sufficient financial stability to support the loan payments.",
        ):
            explanation = await llm_integration.explain_decision(decision_result)

            assert explanation is not None
            assert "approved" in explanation.lower()
            assert "credit score" in explanation.lower()
            assert "income" in explanation.lower()
