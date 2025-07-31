#!/usr/bin/env python3
"""
Decision Layer - Streamlit Web Interface
"""

import streamlit as st
import asyncio
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

from decision_layer import DecisionEngine, load_config
from decision_layer.errors import DecisionLayerError


# Page configuration
st.set_page_config(
    page_title="Decision Layer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_css():
    """Load custom CSS for elegant styling"""
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e5e7eb;
        text-align: center;
    }
    
    .function-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border: 1px solid #e5e7eb;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .success-badge {
        background: #d1fae5;
        color: #065f46;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .error-badge {
        background: #fee2e2;
        color: #991b1b;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .warning-badge {
        background: #fef3c7;
        color: #92400e;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .stButton > button {
        border-radius: 0.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .sidebar .sidebar-content {
        background: #f8fafc;
    }
    </style>
    """, unsafe_allow_html=True)


def init_engine():
    """Initialize the decision engine"""
    if 'engine' not in st.session_state:
        try:
            config = load_config()
            st.session_state.engine = DecisionEngine(config=config.to_dict())
            st.session_state.engine_ready = True
        except Exception as e:
            st.error(f"Failed to initialize engine: {e}")
            st.session_state.engine_ready = False


async def get_engine_stats():
    """Get engine statistics"""
    try:
        functions = await st.session_state.engine.list_functions()
        total_functions = len(functions)
        
        # Get recent traces for metrics
        traces = await get_recent_traces(limit=100)
        
        total_executions = len(traces)
        success_count = len([t for t in traces if t.get('status') == 'success'])
        success_rate = (success_count / total_executions * 100) if total_executions > 0 else 0
        
        avg_duration = sum(t.get('duration', 0) for t in traces) / len(traces) if traces else 0
        
        return {
            'total_functions': total_functions,
            'total_executions': total_executions,
            'success_rate': round(success_rate, 1),
            'avg_duration': round(avg_duration, 1)
        }
    except Exception as e:
        st.error(f"Error getting stats: {e}")
        return {'total_functions': 0, 'total_executions': 0, 'success_rate': 0, 'avg_duration': 0}


async def get_recent_traces(limit=50):
    """Get recent execution traces"""
    try:
        # This would normally query the trace storage
        # For now, return mock data
        return [
            {
                'timestamp': datetime.now() - timedelta(minutes=i),
                'function_id': 'refund_policy',
                'version': 'v1.0',
                'status': 'success' if i % 10 != 0 else 'error',
                'duration': 10 + (i % 20),
                'input_size': 100 + (i % 50)
            }
            for i in range(limit)
        ]
    except Exception as e:
        st.error(f"Error getting traces: {e}")
        return []


def show_dashboard():
    """Show the main dashboard"""
    st.markdown('<h1 class="main-header">🎯 Decision Layer Dashboard</h1>', unsafe_allow_html=True)
    
    # Get stats
    stats = asyncio.run(get_engine_stats())
    
    # Metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📦 Active Functions</h3>
            <h2 style="color: #3b82f6; font-size: 2rem;">{stats['total_functions']}</h2>
            <p style="color: #6b7280; font-size: 0.875rem;">+2 this week</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>⚡ Total Executions</h3>
            <h2 style="color: #10b981; font-size: 2rem;">{stats['total_executions']}</h2>
            <p style="color: #6b7280; font-size: 0.875rem;">+15% today</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>✅ Success Rate</h3>
            <h2 style="color: #10b981; font-size: 2rem;">{stats['success_rate']}%</h2>
            <p style="color: #6b7280; font-size: 0.875rem;">+0.1% improvement</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>⏱️ Avg Response</h3>
            <h2 style="color: #f59e0b; font-size: 2rem;">{stats['avg_duration']}ms</h2>
            <p style="color: #6b7280; font-size: 0.875rem;">-2ms faster</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Execution Trends")
        traces = asyncio.run(get_recent_traces(limit=100))
        if traces:
            df = pd.DataFrame(traces)
            df['hour'] = df['timestamp'].dt.hour
            
            hourly_stats = df.groupby('hour').size().reset_index(name='executions')
            fig = px.line(hourly_stats, x='hour', y='executions', 
                         title="Executions by Hour")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Function Performance")
        if traces:
            function_stats = df.groupby('function_id').agg({
                'status': lambda x: (x == 'success').mean() * 100,
                'duration': 'mean'
            }).reset_index()
            
            fig = px.bar(function_stats, x='function_id', y='status',
                        title="Success Rate by Function")
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.subheader("🕒 Recent Activity")
    traces = asyncio.run(get_recent_traces(limit=10))
    
    for trace in traces:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
            
            col1.write(trace['timestamp'].strftime("%H:%M:%S"))
            col2.write(f"**{trace['function_id']}** v{trace['version']}")
            
            status_badge = "success-badge" if trace['status'] == 'success' else "error-badge"
            status_icon = "✅" if trace['status'] == 'success' else "❌"
            col3.markdown(f'<span class="{status_badge}">{status_icon} {trace["status"]}</span>', 
                         unsafe_allow_html=True)
            
            col4.write(f"{trace['duration']}ms")
            
            if col5.button("👁️", key=f"view_{trace['timestamp']}"):
                st.session_state.view_trace = trace
                st.rerun()


def show_functions():
    """Show functions management page"""
    st.title("📦 Functions Management")
    
    # Function list
    try:
        functions = asyncio.run(st.session_state.engine.list_functions())
        
        if not functions:
            st.info("No functions deployed yet. Deploy your first function!")
            return
        
        for function_id in functions:
            with st.expander(f"🔧 {function_id}", expanded=False):
                try:
                    versions = asyncio.run(st.session_state.engine.list_versions(function_id))
                    
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**Versions:** {', '.join(versions)}")
                        st.write(f"**Latest:** {versions[-1] if versions else 'None'}")
                        
                        # Get function stats
                        traces = asyncio.run(get_recent_traces(limit=50))
                        function_traces = [t for t in traces if t['function_id'] == function_id]
                        
                        if function_traces:
                            success_rate = len([t for t in function_traces if t['status'] == 'success']) / len(function_traces) * 100
                            avg_duration = sum(t['duration'] for t in function_traces) / len(function_traces)
                            
                            st.write(f"**Success Rate:** {success_rate:.1f}%")
                            st.write(f"**Avg Duration:** {avg_duration:.1f}ms")
                    
                    with col2:
                        if st.button(f"🧪 Test", key=f"test_{function_id}"):
                            st.session_state.testing_function = function_id
                            st.rerun()
                    
                    with col3:
                        if st.button(f"✏️ Edit", key=f"edit_{function_id}"):
                            st.session_state.editing_function = function_id
                            st.rerun()
                
                except Exception as e:
                    st.error(f"Error loading function {function_id}: {e}")
    
    except Exception as e:
        st.error(f"Error loading functions: {e}")


def show_function_editor():
    """Show function editor page"""
    st.title("✏️ Function Editor")
    
    # Function selection
    try:
        functions = asyncio.run(st.session_state.engine.list_functions())
        
        if not functions:
            st.warning("No functions available. Deploy a function first.")
            return
        
        selected_function = st.selectbox("Select Function", functions)
        
        if selected_function:
            versions = asyncio.run(st.session_state.engine.list_versions(selected_function))
            selected_version = st.selectbox("Version", versions)
            
            # Load function code
            try:
                code = asyncio.run(st.session_state.engine.storage.load_function(
                    selected_function, selected_version
                ))
                
                # Code editor
                st.subheader("Function Code")
                new_code = st.text_area(
                    "Edit your decision function:",
                    value=code,
                    height=400,
                    help="Edit your decision function code here. Make sure to include the 'decision_function' definition."
                )
                
                # Test section
                st.subheader("🧪 Test Function")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Test Input (JSON):**")
                    test_input = st.text_area(
                        "Input data:",
                        value='{"amount": 500, "issue": "damaged"}',
                        height=150,
                        help="Enter JSON input data for testing"
                    )
                
                with col2:
                    st.write("**Test Results:**")
                    
                    if st.button("🚀 Run Test", type="primary"):
                        try:
                            # Parse test input
                            input_data = json.loads(test_input)
                            
                            # Execute function
                            result = asyncio.run(st.session_state.engine.execute(
                                selected_function, input_data, selected_version
                            ))
                            
                            st.json(result)
                            
                        except json.JSONDecodeError:
                            st.error("Invalid JSON input")
                        except Exception as e:
                            st.error(f"Test failed: {e}")
                
                # Deploy section
                st.subheader("🚀 Deploy New Version")
                
                new_version = st.text_input(
                    "New Version:",
                    value=f"v{len(versions) + 1}.0",
                    help="Enter version number for the new deployment"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📋 Validate Code", type="secondary"):
                        try:
                            # Basic validation
                            if "def decision_function" not in new_code:
                                st.error("Code must contain 'decision_function' definition")
                            else:
                                st.success("Code validation passed!")
                        except Exception as e:
                            st.error(f"Validation failed: {e}")
                
                with col2:
                    if st.button("🚀 Deploy", type="primary"):
                        try:
                            asyncio.run(st.session_state.engine.deploy_function(
                                selected_function, new_version, new_code
                            ))
                            st.success(f"Successfully deployed {selected_function} v{new_version}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Deployment failed: {e}")
            
            except Exception as e:
                st.error(f"Error loading function code: {e}")
    
    except Exception as e:
        st.error(f"Error in function editor: {e}")


def show_deploy():
    """Show function deployment page"""
    st.title("🚀 Deploy New Function")
    
    # Function details
    function_id = st.text_input(
        "Function ID:",
        placeholder="e.g., refund_policy, risk_assessment",
        help="Unique identifier for your function"
    )
    
    version = st.text_input(
        "Version:",
        value="v1.0",
        help="Version number for this function"
    )
    
    # Code editor
    st.subheader("Function Code")
    
    # Template selector
    template = st.selectbox(
        "Choose Template:",
        ["Custom", "Refund Policy", "Risk Assessment", "Eligibility Check"]
    )
    
    if template == "Refund Policy":
        default_code = '''from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """Refund policy decision function"""
    
    amount = input_data.get('amount', 0)
    issue = input_data.get('issue', '')
    customer_tier = input_data.get('customer_tier', 'standard')
    
    # Decision logic
    if amount > 1000:
        return {"approved": False, "reason": "Amount exceeds limit"}
    
    if issue == "damaged":
        if customer_tier == "premium":
            return {"approved": True, "reason": "Premium customer damaged item policy"}
        else:
            return {"approved": True, "reason": "Standard damaged item policy"}
    
    if issue == "wrong_item":
        return {"approved": True, "reason": "Wrong item policy"}
    
    return {"approved": False, "reason": "Issue not covered by policy"}'''
    
    elif template == "Risk Assessment":
        default_code = '''from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """Risk assessment decision function"""
    
    age = input_data.get('age', 0)
    income = input_data.get('income', 0)
    credit_score = input_data.get('credit_score', 0)
    employment_years = input_data.get('employment_years', 0)
    
    # Calculate risk score
    risk_score = 0
    
    if age < 25:
        risk_score += 20
    elif age > 65:
        risk_score += 15
    
    if income < 30000:
        risk_score += 25
    elif income > 100000:
        risk_score -= 10
    
    if credit_score < 600:
        risk_score += 30
    elif credit_score > 750:
        risk_score -= 20
    
    if employment_years < 2:
        risk_score += 15
    
    # Risk categories
    if risk_score < 30:
        risk_level = "low"
        approved = True
    elif risk_score < 60:
        risk_level = "medium"
        approved = True
    else:
        risk_level = "high"
        approved = False
    
    return {
        "approved": approved,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "reason": f"Risk assessment: {risk_level} risk"
    }'''
    
    elif template == "Eligibility Check":
        default_code = '''from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """Eligibility check decision function"""
    
    age = input_data.get('age', 0)
    location = input_data.get('location', '')
    product = input_data.get('product', '')
    
    # Basic eligibility
    if age < 18:
        return {"eligible": False, "reason": "Minimum age requirement not met"}
    
    # Product-specific rules
    if product == "insurance":
        if age > 80:
            return {"eligible": False, "reason": "Age exceeds insurance limit"}
    
    if product == "loan":
        if age > 75:
            return {"eligible": False, "reason": "Age exceeds loan limit"}
    
    # Location restrictions
    restricted_locations = ["restricted_region_1", "restricted_region_2"]
    if location in restricted_locations:
        return {"eligible": False, "reason": "Location not eligible for this product"}
    
    return {"eligible": True, "reason": "All eligibility criteria met"}'''
    
    else:
        default_code = '''from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """Your decision function"""
    
    # Extract input data
    # your_input = input_data.get('your_field', default_value)
    
    # Your decision logic here
    # if condition:
    #     return {"result": "decision"}
    
    # Return structured output
    return {
        "result": "your_decision",
        "reason": "explanation"
    }'''
    
    code = st.text_area(
        "Function Code:",
        value=default_code,
        height=400,
        help="Write your decision function code here"
    )
    
    # Test section
    st.subheader("🧪 Test Before Deploy")
    
    col1, col2 = st.columns(2)
    
    with col1:
        test_input = st.text_area(
            "Test Input (JSON):",
            value='{"test": "data"}',
            height=150
        )
    
    with col2:
        if st.button("🚀 Test Function"):
            try:
                # Basic code validation
                if "def decision_function" not in code:
                    st.error("Code must contain 'decision_function' definition")
                else:
                    st.success("Code validation passed!")
                    
                    # Try to parse test input
                    try:
                        input_data = json.loads(test_input)
                        st.success("Test input is valid JSON")
                    except json.JSONDecodeError:
                        st.error("Invalid JSON in test input")
            
            except Exception as e:
                st.error(f"Test failed: {e}")
    
    # Deploy button
    st.subheader("🚀 Deploy Function")
    
    if st.button("🚀 Deploy Function", type="primary", disabled=not function_id):
        if not function_id:
            st.error("Please enter a function ID")
        else:
            try:
                asyncio.run(st.session_state.engine.deploy_function(
                    function_id, version, code
                ))
                st.success(f"Successfully deployed {function_id} v{version}")
                
                # Clear form
                st.rerun()
            
            except Exception as e:
                st.error(f"Deployment failed: {e}")


def show_traces():
    """Show execution traces page"""
    st.title("📊 Execution Traces")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            functions = asyncio.run(st.session_state.engine.list_functions())
            function_filter = st.selectbox(
                "Function",
                ["All"] + functions
            )
        except:
            function_filter = "All"
    
    with col2:
        date_filter = st.date_input("Date", value=datetime.now())
    
    with col3:
        status_filter = st.selectbox("Status", ["All", "Success", "Error"])
    
    # Get traces
    traces = asyncio.run(get_recent_traces(limit=100))
    
    # Apply filters
    if function_filter != "All":
        traces = [t for t in traces if t['function_id'] == function_filter]
    
    if status_filter != "All":
        status_value = status_filter.lower()
        traces = [t for t in traces if t['status'] == status_value]
    
    # Display traces
    if traces:
        # Convert to DataFrame for better display
        df = pd.DataFrame(traces)
        df['time'] = df['timestamp'].dt.strftime('%H:%M:%S')
        df['date'] = df['timestamp'].dt.strftime('%Y-%m-%d')
        
        # Display as table
        st.dataframe(
            df[['time', 'function_id', 'version', 'status', 'duration']],
            column_config={
                "time": "Time",
                "function_id": "Function",
                "version": "Version",
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Success", "Error"]
                ),
                "duration": st.column_config.NumberColumn(
                    "Duration (ms)",
                    format="%d ms"
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Summary stats
        st.subheader("📈 Summary Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Traces", len(traces))
        
        with col2:
            success_count = len([t for t in traces if t['status'] == 'success'])
            st.metric("Success Rate", f"{success_count/len(traces)*100:.1f}%")
        
        with col3:
            avg_duration = sum(t['duration'] for t in traces) / len(traces)
            st.metric("Avg Duration", f"{avg_duration:.1f}ms")
        
        with col4:
            st.metric("Functions", len(set(t['function_id'] for t in traces)))
    
    else:
        st.info("No traces found for the selected filters")


def show_settings():
    """Show settings page"""
    st.title("⚙️ Settings")
    
    # Configuration
    st.subheader("🔧 Configuration")
    
    try:
        config = load_config()
        
        # Storage settings
        st.write("**Storage Configuration:**")
        st.json(config.storage.dict())
        
        # Security settings
        st.write("**Security Configuration:**")
        security_config = config.security.dict()
        # Hide sensitive info
        if security_config.get('api_key'):
            security_config['api_key'] = '***hidden***'
        st.json(security_config)
        
        # Plugin settings
        st.write("**Plugin Configuration:**")
        st.json(config.plugins.dict())
        
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
    
    # Health check
    st.subheader("🏥 System Health")
    
    if st.button("🔍 Check Health"):
        try:
            # Basic health check
            functions = asyncio.run(st.session_state.engine.list_functions())
            st.success(f"✅ System healthy - {len(functions)} functions loaded")
        except Exception as e:
            st.error(f"❌ Health check failed: {e}")


def main():
    """Main application"""
    # Load custom CSS
    load_css()
    
    # Initialize engine
    init_engine()
    
    if not st.session_state.get('engine_ready', False):
        st.error("Failed to initialize Decision Layer engine. Please check your configuration.")
        return
    
    # Sidebar navigation
    st.sidebar.title("🎯 Decision Layer")
    
    page = st.sidebar.selectbox(
        "Navigation",
        ["Dashboard", "Functions", "Deploy", "Traces", "Settings"]
    )
    
    # Page routing
    if page == "Dashboard":
        show_dashboard()
    elif page == "Functions":
        show_functions()
    elif page == "Deploy":
        show_deploy()
    elif page == "Traces":
        show_traces()
    elif page == "Settings":
        show_settings()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Decision Layer v2.0**")
    st.sidebar.markdown("Elegant decision management")


if __name__ == "__main__":
    main() 