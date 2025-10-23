#!/usr/bin/env python3
"""
Simple Web Interface for Policy as Code
Streamlit-based web interface for decision function execution
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
import importlib.util
import traceback
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import streamlit as st
except ImportError:
    print("❌ Streamlit not installed. Install with: pip install streamlit")
    print("   Or install production dependencies: pip install -e .[production]")
    sys.exit(1)

# Page configuration
st.set_page_config(
    page_title="Policy as Code",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        color: #1f77b4;
    }
    .function-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .result-success {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .result-error {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
    }
</style>
""",
    unsafe_allow_html=True,
)


def load_function_from_registry(
    function_id: str, version: Optional[str] = None
) -> tuple:
    """Load a function from the registry"""
    registry_dir = Path("registry")
    if not registry_dir.exists():
        raise Exception("Registry not found. Run 'policy-as-code init' first.")

    # Look for function files
    pattern = (
        f"{function_id}_*.json" if not version else f"{function_id}_{version}.json"
    )
    registry_files = list(registry_dir.glob(pattern))

    if not registry_files:
        available_functions = []
        for file in registry_dir.glob("*.json"):
            func_name = file.stem.split("_")[0]
            if func_name not in available_functions:
                available_functions.append(func_name)

        raise Exception(
            f"Function {function_id} not found. Available functions: {available_functions}"
        )

    # Use latest version if not specified
    if not version:
        registry_file = max(registry_files, key=lambda f: f.stat().st_mtime)
    else:
        registry_file = registry_dir / f"{function_id}_{version}.json"
        if not registry_file.exists():
            raise Exception(f"Version {version} not found.")

    # Load registry entry
    with open(registry_file, "r") as f:
        registry_entry = json.load(f)

    # Load function module
    func_path = Path(registry_entry["file_path"])
    spec = importlib.util.spec_from_file_location(function_id, func_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    func = getattr(module, registry_entry["function_name"])
    return func, registry_entry


def get_available_functions() -> list:
    """Get list of available functions"""
    registry_dir = Path("registry")
    if not registry_dir.exists():
        return []

    functions = []
    registry_files = list(registry_dir.glob("*.json"))

    for file in registry_files:
        with open(file, "r") as f:
            entry = json.load(f)

        func_id = entry["function_id"]
        if func_id not in [f["function_id"] for f in functions]:
            functions.append(
                {
                    "function_id": func_id,
                    "version": entry["version"],
                    "function_name": entry["function_name"],
                    "file_path": entry["file_path"],
                }
            )

    return functions


def main():
    """Main Streamlit application"""

    # Header
    st.markdown(
        '<h1 class="main-header">⚖️ Policy as Code</h1>', unsafe_allow_html=True
    )
    st.markdown("**Execute decision functions through a simple web interface**")

    # Sidebar
    st.sidebar.title("🎛️ Controls")

    # Check if registry exists
    registry_dir = Path("registry")
    if not registry_dir.exists():
        st.error("❌ Registry not found. Please run 'policy-as-code init' first.")
        st.info(
            "💡 **Quick Setup:**\n1. Open terminal\n2. Run: `policy-as-code init`\n3. Refresh this page"
        )
        return

    # Get available functions
    functions = get_available_functions()
    if not functions:
        st.warning("⚠️ No functions deployed. Deploy a function first.")
        st.info(
            "💡 **Deploy a function:**\n1. Open terminal\n2. Run: `policy-as-code deploy loan_approval 1.0 examples/simple_demo.py`\n3. Refresh this page"
        )
        return

    # Function selection
    st.sidebar.subheader("📋 Select Function")
    function_options = [f"{f['function_id']} (v{f['version']})" for f in functions]
    selected_function = st.sidebar.selectbox("Choose a function:", function_options)

    if not selected_function:
        st.stop()

    # Parse selected function
    function_id = selected_function.split(" (v")[0]
    function_info = next(f for f in functions if f["function_id"] == function_id)

    # Display function info
    st.subheader(f"🔧 Function: {function_id}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Version", function_info["version"])
    with col2:
        st.metric("Function Name", function_info["function_name"])
    with col3:
        st.metric("Status", "✅ Deployed")

    # Input data section
    st.subheader("📥 Input Data")

    # Try to load function to get input schema hints
    try:
        func, registry_entry = load_function_from_registry(function_id)

        # Create input form based on function
        st.info(f"💡 **Function:** {registry_entry['function_name']}")

        # Common input fields for loan approval
        if function_id == "loan_approval" or function_id == "simple_demo":
            col1, col2 = st.columns(2)
            with col1:
                credit_score = st.number_input(
                    "Credit Score", min_value=300, max_value=850, value=750
                )
                income = st.number_input(
                    "Income ($)", min_value=0, max_value=1000000, value=75000
                )
            with col2:
                applicant_name = st.text_input("Applicant Name", value="John Doe")
                debt_ratio = st.slider("Debt Ratio", 0.0, 1.0, 0.3, 0.01)

            input_data = {
                "credit_score": credit_score,
                "income": income,
                "applicant_name": applicant_name,
                "debt_ratio": debt_ratio,
            }

        # Common input fields for basic approval
        elif function_id == "basic_approval":
            col1, col2 = st.columns(2)
            with col1:
                age = st.number_input("Age", min_value=0, max_value=120, value=25)
                income = st.number_input(
                    "Income ($)", min_value=0, max_value=1000000, value=45000
                )
            with col2:
                name = st.text_input("Name", value="Alice")

            input_data = {"age": age, "income": income, "name": name}

        # Generic input for other functions
        else:
            st.info("💡 **Generic Input:** Enter JSON data for this function")
            input_json = st.text_area(
                "Input JSON", value='{"key": "value"}', height=100
            )

            try:
                input_data = json.loads(input_json)
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON format")
                st.stop()

        # Execute button
        if st.button("🚀 Execute Function", type="primary"):
            with st.spinner("Executing function..."):
                try:
                    start_time = datetime.now()
                    result = func(input_data)
                    execution_time = (
                        datetime.now() - start_time
                    ).total_seconds() * 1000

                    # Display result
                    st.subheader("📤 Result")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Execution Time", f"{execution_time:.2f} ms")
                    with col2:
                        st.metric("Status", "✅ Success")

                    # Format result based on content
                    if isinstance(result, dict):
                        if result.get("approved"):
                            st.markdown(
                                '<div class="result-success">', unsafe_allow_html=True
                            )
                            st.success("✅ **APPROVED**")
                            if "approved_amount" in result:
                                st.write(f"**Amount:** ${result['approved_amount']:,}")
                            if "interest_rate" in result:
                                st.write(
                                    f"**Interest Rate:** {result['interest_rate']:.1%}"
                                )
                            if "reason" in result:
                                st.write(f"**Reason:** {result['reason']}")
                            st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(
                                '<div class="result-error">', unsafe_allow_html=True
                            )
                            st.error("❌ **DENIED**")
                            if "reason" in result:
                                st.write(f"**Reason:** {result['reason']}")
                            st.markdown("</div>", unsafe_allow_html=True)

                    # Raw result
                    with st.expander("🔍 Raw Result"):
                        st.json(result)

                except Exception as e:
                    st.error(f"❌ Execution failed: {str(e)}")
                    if st.checkbox("Show debug info"):
                        st.code(traceback.format_exc())

    except Exception as e:
        st.error(f"❌ Failed to load function: {str(e)}")
        st.info(
            "💡 **Troubleshooting:**\n1. Check if function is properly deployed\n2. Run: `policy-as-code list`\n3. Redeploy if necessary"
        )

    # Footer
    st.markdown("---")
    st.markdown("**Policy as Code Foundation** - Building accountable automation")

    # Sidebar info
    st.sidebar.markdown("---")
    st.sidebar.subheader("ℹ️ Information")
    st.sidebar.info(
        """
    **Quick Commands:**
    - `policy-as-code init` - Initialize system
    - `policy-as-code list` - List functions
    - `policy-as-code deploy <name> <version> <file>` - Deploy function
    - `policy-as-code execute <name> <data>` - Execute function
    """
    )

    st.sidebar.subheader("🔗 Links")
    st.sidebar.markdown("- [Documentation](https://github.com/your-org/policy-as-code)")
    st.sidebar.markdown("- [CLI Reference](docs/reference/cli.md)")
    st.sidebar.markdown("- [API Docs](http://localhost:8000/docs)")


if __name__ == "__main__":
    main()
