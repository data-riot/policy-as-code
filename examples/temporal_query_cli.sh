#!/bin/bash

# Decision Layer - Temporal Policy Query via CLI
# This script demonstrates how to query for policies active in April 2017 using the CLI

echo "🚀 Decision Layer - Temporal Policy Query via CLI"
echo "=================================================="

# Set the date range for April 2017
START_DATE="2017-04-01"
END_DATE="2017-04-30"

echo "📅 Querying for policies active between $START_DATE and $END_DATE"
echo ""

# 1. List all functions with their versions and status
echo "1️⃣ Listing all functions with version information..."
decision-layer list --detailed --format json > functions_list.json

echo "✅ Functions list saved to functions_list.json"
echo ""

# 2. Get detailed information for each function
echo "2️⃣ Getting detailed information for each function..."

# Create a script to process each function
cat > process_functions.py << 'EOF'
import json
import subprocess
import sys
from datetime import datetime, timezone

# Load functions list
with open('functions_list.json', 'r') as f:
    functions = json.load(f)

active_policies = []
target_start = datetime(2017, 4, 1, tzinfo=timezone.utc)
target_end = datetime(2017, 4, 30, 23, 59, 59, tzinfo=timezone.utc)

for function in functions:
    function_id = function['function_id']
    print(f"Processing {function_id}...")
    
    # Get detailed info for this function
    try:
        result = subprocess.run(
            ['decision-layer', 'info', function_id, '--format', 'json'],
            capture_output=True, text=True, check=True
        )
        function_details = json.loads(result.stdout)
        
        # Check each version
        for version_info in function_details.get('versions', []):
            version = version_info['version']
            created_at = datetime.fromisoformat(version_info['created_at'].replace('Z', '+00:00'))
            status = version_info['status']
            
            # Check if active during April 2017
            if (status == 'approved' and 
                created_at <= target_end and
                (version_info.get('deprecated_at') is None or 
                 datetime.fromisoformat(version_info['deprecated_at'].replace('Z', '+00:00')) >= target_start)):
                
                active_policies.append({
                    'function_id': function_id,
                    'version': version,
                    'title': version_info.get('title', function_id),
                    'description': version_info.get('description', ''),
                    'created_at': version_info['created_at'],
                    'author': version_info.get('author', 'unknown'),
                    'tags': version_info.get('tags', []),
                    'policy_references': version_info.get('policy_references', []),
                    'compliance_requirements': version_info.get('compliance_requirements', [])
                })
                
    except subprocess.CalledProcessError as e:
        print(f"Error processing {function_id}: {e}")

# Save active policies
with open('active_policies_april_2017.json', 'w') as f:
    json.dump(active_policies, f, indent=2)

print(f"Found {len(active_policies)} active policies in April 2017")
EOF

python3 process_functions.py

echo "✅ Active policies saved to active_policies_april_2017.json"
echo ""

# 3. Get execution traces for each active policy
echo "3️⃣ Getting execution traces for active policies..."

cat > get_traces.py << 'EOF'
import json
import subprocess
import sys
from datetime import datetime

# Load active policies
with open('active_policies_april_2017.json', 'r') as f:
    active_policies = json.load(f)

all_traces = []

for policy in active_policies:
    function_id = policy['function_id']
    version = policy['version']
    
    print(f"Getting traces for {function_id} v{version}...")
    
    try:
        # Get traces for April 2017
        result = subprocess.run([
            'decision-layer', 'traces', function_id,
            '--start-date', '2017-04-01',
            '--end-date', '2017-04-30',
            '--version', version,
            '--format', 'json'
        ], capture_output=True, text=True, check=True)
        
        traces = json.loads(result.stdout)
        traces['function_id'] = function_id
        traces['version'] = version
        all_traces.append(traces)
        
    except subprocess.CalledProcessError as e:
        print(f"Error getting traces for {function_id}: {e}")

# Save all traces
with open('april_2017_traces.json', 'w') as f:
    json.dump(all_traces, f, indent=2)

print(f"Saved traces for {len(all_traces)} policies")
EOF

python3 get_traces.py

echo "✅ Execution traces saved to april_2017_traces.json"
echo ""

# 4. Generate performance metrics
echo "4️⃣ Generating performance metrics..."

cat > generate_metrics.py << 'EOF'
import json
from datetime import datetime

# Load traces
with open('april_2017_traces.json', 'r') as f:
    all_traces = json.load(f)

# Load active policies
with open('active_policies_april_2017.json', 'r') as f:
    active_policies = json.load(f)

performance_metrics = []

for traces_data in all_traces:
    function_id = traces_data['function_id']
    version = traces_data['version']
    traces = traces_data.get('traces', [])
    
    # Calculate metrics
    total_executions = len(traces)
    successful_executions = len([t for t in traces if t.get('status') == 'success'])
    error_executions = len([t for t in traces if t.get('status') == 'error'])
    
    success_rate = successful_executions / total_executions if total_executions > 0 else 0
    
    # Calculate average execution time
    execution_times = [t.get('execution_time_ms', 0) for t in traces if t.get('execution_time_ms')]
    avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
    
    metrics = {
        'function_id': function_id,
        'version': version,
        'total_executions': total_executions,
        'successful_executions': successful_executions,
        'error_executions': error_executions,
        'success_rate': success_rate,
        'average_execution_time_ms': avg_execution_time
    }
    
    performance_metrics.append(metrics)

# Save metrics
with open('april_2017_performance_metrics.json', 'w') as f:
    json.dump(performance_metrics, f, indent=2)

print(f"Generated metrics for {len(performance_metrics)} policies")
EOF

python3 generate_metrics.py

echo "✅ Performance metrics saved to april_2017_performance_metrics.json"
echo ""

# 5. Generate comprehensive report
echo "5️⃣ Generating comprehensive report..."

cat > generate_report.py << 'EOF'
import json
from datetime import datetime, timezone

# Load all data
with open('active_policies_april_2017.json', 'r') as f:
    active_policies = json.load(f)

with open('april_2017_performance_metrics.json', 'r') as f:
    performance_metrics = json.load(f)

# Create comprehensive report
report = {
    'report_period': 'April 2017',
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'summary': {
        'total_active_policies': len(active_policies),
        'total_executions': sum(m['total_executions'] for m in performance_metrics),
        'total_successful_executions': sum(m['successful_executions'] for m in performance_metrics),
        'total_error_executions': sum(m['error_executions'] for m in performance_metrics),
        'overall_success_rate': sum(m['successful_executions'] for m in performance_metrics) / 
                               sum(m['total_executions'] for m in performance_metrics) if sum(m['total_executions'] for m in performance_metrics) > 0 else 0
    },
    'policies': []
}

# Combine policy and performance data
for policy in active_policies:
    metrics = next((m for m in performance_metrics 
                   if m['function_id'] == policy['function_id'] and m['version'] == policy['version']), None)
    
    policy_report = {
        'function_id': policy['function_id'],
        'version': policy['version'],
        'title': policy['title'],
        'description': policy['description'],
        'author': policy['author'],
        'tags': policy['tags'],
        'policy_references': policy['policy_references'],
        'compliance_requirements': policy['compliance_requirements'],
        'performance': metrics or {}
    }
    
    report['policies'].append(policy_report)

# Save report
with open('april_2017_comprehensive_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print("Comprehensive report generated:")
print(f"  • Total active policies: {report['summary']['total_active_policies']}")
print(f"  • Total executions: {report['summary']['total_executions']}")
print(f"  • Overall success rate: {report['summary']['overall_success_rate']:.1%}")
print(f"  • Report saved to: april_2017_comprehensive_report.json")
EOF

python3 generate_report.py

echo ""
echo "🎉 Temporal Policy Query Complete!"
echo "=================================="
echo ""
echo "Generated files:"
echo "  • functions_list.json - All functions"
echo "  • active_policies_april_2017.json - Active policies in April 2017"
echo "  • april_2017_traces.json - Execution traces"
echo "  • april_2017_performance_metrics.json - Performance metrics"
echo "  • april_2017_comprehensive_report.json - Comprehensive report"
echo ""
echo "To view the results:"
echo "  cat april_2017_comprehensive_report.json | jq '.summary'"
echo "  cat april_2017_comprehensive_report.json | jq '.policies[] | {function_id, version, title, performance}'" 