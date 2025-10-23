#!/usr/bin/env python3
"""
Policy as Code CLI
Command-line interface for managing decision functions
"""

import click
import json
import sys
from pathlib import Path as PathLib
from typing import Dict, Any, Optional
import importlib.util
import traceback

# Add project root to path
project_root = PathLib(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from policy_as_code.core.decision_engine import DecisionEngine
    from policy_as_code.core.registry import FunctionRegistry
except ImportError:
    # Fallback for basic functionality
    DecisionEngine = None
    FunctionRegistry = None


@click.group()
@click.version_option(version="2.0.0")
def cli():
    """Policy as Code CLI - Manage decision functions and execute decisions"""
    pass


@cli.command()
def init():
    """Initialize the Policy as Code system"""
    click.echo("🚀 Initializing Policy as Code system...")

    # Create necessary directories
    directories = ["registry", "traces", "config", "data"]
    for directory in directories:
        PathLib(directory).mkdir(exist_ok=True)
        click.echo(f"✅ Created directory: {directory}")

    # Create basic config
    config = {
        "storage_backend": "file",
        "trace_directory": "./traces",
        "registry_directory": "./registry",
        "max_input_size": 1048576,
        "rate_limit": 100,
    }

    config_file = PathLib("config/config.yaml")
    config_file.parent.mkdir(exist_ok=True)

    import yaml

    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    click.echo(f"✅ Created configuration: {config_file}")
    click.echo("🎉 Policy as Code system initialized!")


@cli.command()
@click.argument("function_id")
@click.argument("version")
@click.argument("function_file")
@click.option("--schema", help="Path to schema file (JSON)")
@click.option("--metadata", help="Path to metadata file (JSON)")
@click.option("--force", is_flag=True, help="Overwrite existing version")
def deploy(
    function_id: str,
    version: str,
    function_file: str,
    schema: Optional[str],
    metadata: Optional[str],
    force: bool,
):
    """Deploy a decision function"""
    click.echo(f"📦 Deploying {function_id} v{version}...")

    # Check if function file exists
    func_path = PathLib(function_file)
    if not func_path.exists():
        click.echo(f"❌ Function file not found: {function_file}")
        sys.exit(1)

    # Load function
    try:
        spec = importlib.util.spec_from_file_location(function_id, func_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find the main function (look for common patterns)
        main_func = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if callable(attr) and not attr_name.startswith("_"):
                # Check if it looks like a decision function
                if (
                    hasattr(attr, "__code__")
                    and "input_data" in attr.__code__.co_varnames
                ):
                    main_func = attr
                    break

        if not main_func:
            click.echo(f"❌ No decision function found in {function_file}")
            click.echo("   Expected function with 'input_data' parameter")
            sys.exit(1)

        # Create registry entry
        registry_entry = {
            "function_id": function_id,
            "version": version,
            "file_path": str(func_path.absolute()),
            "function_name": main_func.__name__,
            "deployed_at": str(PathLib().cwd()),
            "schema": schema,
            "metadata": metadata,
        }

        # Save to registry
        registry_dir = PathLib("registry")
        registry_dir.mkdir(exist_ok=True)

        registry_file = registry_dir / f"{function_id}_{version}.json"
        if registry_file.exists() and not force:
            click.echo(f"❌ Version {version} already exists. Use --force to overwrite.")
            sys.exit(1)

        with open(registry_file, "w") as f:
            json.dump(registry_entry, f, indent=2)

        click.echo(f"✅ Deployed {function_id} v{version}")
        click.echo(f"   Function: {main_func.__name__}")
        click.echo(f"   Registry: {registry_file}")

    except Exception as e:
        click.echo(f"❌ Deployment failed: {e}")
        if click.get_current_context().obj.get("debug", False):
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument("function_id")
@click.argument("input_data")
@click.option("--version", help="Function version (default: latest)")
@click.option("--output", help="Output file path")
@click.option(
    "--format",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Output format",
)
def execute(
    function_id: str,
    input_data: str,
    version: Optional[str],
    output: Optional[str],
    format: str,
):
    """Execute a decision function"""
    function_id = str(function_id)  # Ensure it's a string
    click.echo(f"⚡ Executing {function_id}...")

    # Find function in registry
    registry_dir = PathLib("registry")
    if not registry_dir.exists():
        click.echo("❌ Registry not found. Run 'policy-as-code init' first.")
        sys.exit(1)

    # Look for function files
    pattern = (
        f"{function_id}_*.json" if not version else f"{function_id}_{version}.json"
    )
    registry_files = list(registry_dir.glob(pattern))

    if not registry_files:
        click.echo(f"❌ Function {function_id} not found in registry.")
        click.echo("   Available functions:")
        for file in registry_dir.glob("*.json"):
            func_name = file.stem.split("_")[0]
            click.echo(f"   - {func_name}")
        sys.exit(1)

    # Use latest version if not specified
    if not version:
        registry_file = max(registry_files, key=lambda f: f.stat().st_mtime)
    else:
        registry_file = registry_dir / f"{function_id}_{version}.json"
        if not registry_file.exists():
            click.echo(f"❌ Version {version} not found.")
            sys.exit(1)

    # Load registry entry
    with open(registry_file, "r") as f:
        registry_entry = json.load(f)

    # Load input data
    try:
        if input_data.startswith("{") or input_data.startswith("["):
            # JSON string
            data = json.loads(input_data)
        elif PathLib(input_data).exists():
            # File path
            with open(input_data, "r") as f:
                if input_data.endswith(".json"):
                    data = json.load(f)
                elif input_data.endswith(".yaml") or input_data.endswith(".yml"):
                    import yaml

                    data = yaml.safe_load(f)
                else:
                    click.echo(f"❌ Unsupported file format: {input_data}")
                    sys.exit(1)
        else:
            click.echo(f"❌ Invalid input data: {input_data}")
            click.echo("   Provide JSON string or file path")
            sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Failed to parse input data: {e}")
        sys.exit(1)

    # Execute function
    try:
        func_path = PathLib(registry_entry["file_path"])
        spec = importlib.util.spec_from_file_location(function_id, func_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        func = getattr(module, registry_entry["function_name"])
        result = func(data)

        # Format output
        if format == "json":
            output_str = json.dumps(result, indent=2)
        else:
            import yaml

            output_str = yaml.dump(result, default_flow_style=False)

        # Output result
        if output:
            with open(output, "w") as f:
                f.write(output_str)
            click.echo(f"✅ Result saved to: {output}")
        else:
            click.echo("✅ Execution completed:")
            click.echo(output_str)

    except Exception as e:
        click.echo(f"❌ Execution failed: {e}")
        if click.get_current_context().obj.get("debug", False):
            traceback.print_exc()
        sys.exit(1)


@cli.command(name="list")
def list_functions():
    """List all deployed functions"""
    registry_dir = PathLib("registry")
    if not registry_dir.exists():
        click.echo("❌ Registry not found. Run 'policy-as-code init' first.")
        sys.exit(1)

    registry_files = list(registry_dir.glob("*.json"))
    if not registry_files:
        click.echo("📋 No functions deployed.")
        click.echo(
            "   Deploy a function with: policy-as-code deploy <name> <version> <file>"
        )
        return

    click.echo("📋 Deployed Functions:")
    click.echo("=" * 50)

    functions = {}
    for file in registry_files:
        with open(file, "r") as f:
            entry = json.load(f)

        func_id = entry["function_id"]
        if func_id not in functions:
            functions[func_id] = []
        functions[func_id].append(entry)

    for func_id, versions in functions.items():
        click.echo(f"\n🔧 {func_id}")
        for version_info in sorted(versions, key=lambda x: x["version"]):
            click.echo(f"   Version: {version_info['version']}")
            click.echo(f"   Function: {version_info['function_name']}")
            click.echo(f"   File: {version_info['file_path']}")


@cli.command()
@click.argument("function_id")
@click.option("--version", help="Function version (default: latest)")
def info(function_id: str, version: Optional[str]):
    """Get detailed information about a function"""
    registry_dir = PathLib("registry")
    if not registry_dir.exists():
        click.echo("❌ Registry not found. Run 'policy-as-code init' first.")
        sys.exit(1)

    # Find function
    pattern = (
        f"{function_id}_*.json" if not version else f"{function_id}_{version}.json"
    )
    registry_files = list(registry_dir.glob(pattern))

    if not registry_files:
        click.echo(f"❌ Function {function_id} not found.")
        sys.exit(1)

    registry_file = (
        max(registry_files, key=lambda f: f.stat().st_mtime)
        if not version
        else registry_dir / f"{function_id}_{version}.json"
    )

    with open(registry_file, "r") as f:
        entry = json.load(f)

    click.echo(f"📊 Function Information: {function_id}")
    click.echo("=" * 50)
    click.echo(f"Version: {entry['version']}")
    click.echo(f"Function Name: {entry['function_name']}")
    click.echo(f"File Path: {entry['file_path']}")
    click.echo(f"Deployed At: {entry['deployed_at']}")

    if entry.get("schema"):
        click.echo(f"Schema: {entry['schema']}")
    if entry.get("metadata"):
        click.echo(f"Metadata: {entry['metadata']}")


@cli.command()
def status():
    """Check system status"""
    click.echo("📊 Policy as Code System Status")
    click.echo("=" * 40)

    # Check directories
    directories = ["registry", "traces", "config", "data"]
    for directory in directories:
        if PathLib(directory).exists():
            click.echo(f"✅ {directory}: OK")
        else:
            click.echo(f"❌ {directory}: Missing")

    # Check registry
    registry_dir = PathLib("registry")
    if registry_dir.exists():
        registry_files = list(registry_dir.glob("*.json"))
        click.echo(f"📦 Functions: {len(registry_files)} deployed")

        if registry_files:
            click.echo("   Available functions:")
            functions = set()
            for file in registry_files:
                with open(file, "r") as f:
                    entry = json.load(f)
                functions.add(entry["function_id"])

            for func in sorted(functions):
                click.echo(f"   - {func}")
    else:
        click.echo("📦 Functions: 0 deployed")

    # Check traces
    traces_dir = PathLib("traces")
    if traces_dir.exists():
        trace_files = list(traces_dir.glob("*.json"))
        click.echo(f"📝 Traces: {len(trace_files)} files")
    else:
        click.echo("📝 Traces: 0 files")


@cli.command()
@click.option("--debug", is_flag=True, help="Enable debug mode")
def test(debug: bool):
    """Test the system with sample functions"""
    click.echo("🧪 Testing Policy as Code system...")

    # Test basic functionality
    try:
        # Test init
        click.echo("Testing initialization...")
        init()

        # Test with simple demo
        click.echo("\nTesting with simple demo...")
        demo_file = PathLib("examples/simple_demo.py")
        if demo_file.exists():
            deploy("simple_demo", "1.0", str(demo_file), force=True)

            # Test execution
            test_data = (
                '{"credit_score": 750, "income": 75000, "applicant_name": "Test User"}'
            )
            execute("simple_demo", test_data)

            click.echo("✅ System test completed successfully!")
        else:
            click.echo("❌ Demo file not found: examples/simple_demo.py")

    except Exception as e:
        click.echo(f"❌ System test failed: {e}")
        if debug:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cli()
