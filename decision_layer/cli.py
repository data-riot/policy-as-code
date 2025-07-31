import asyncio
import json
from pathlib import Path
from typing import Any, Dict

import click
import yaml

from .core import DecisionEngine
from .errors import DecisionLayerError, create_error_response


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    if not Path(config_path).exists():
        return {}

    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}


@click.group()
@click.option("--config", "-c", default="config.yaml", help="Configuration file")
@click.pass_context
def cli(ctx, config):
    """Decision Layer - Elegant decision management"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config)
    ctx.obj["engine"] = DecisionEngine(storage_backend="file", config=ctx.obj["config"])


@cli.command()
@click.argument("function_id")
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--version", "-v", help="Function version (defaults to latest)")
@click.option("--output", "-o", help="Output file (defaults to stdout)")
@click.pass_context
def execute(ctx, function_id, input_file, version, output):
    """Execute a decision function"""
    engine = ctx.obj["engine"]

    # Load input
    with open(input_file) as f:
        input_data = json.load(f)

    # Execute
    async def run():
        try:
            result = await engine.execute(function_id, input_data, version)

            # Output
            if output:
                with open(output, "w") as f:
                    json.dump(result, f, indent=2)
                click.echo(f"Result written to {output}")
            else:
                click.echo(json.dumps(result, indent=2))

        except DecisionLayerError as e:
            error_response = create_error_response(e)
            click.echo(f"Error: {error_response['error']['message']}", err=True)
            if error_response["error"]["details"]:
                click.echo(f"Details: {error_response['error']['details']}", err=True)
            raise click.Abort()
        except Exception as e:
            click.echo(f"Unexpected error: {e}", err=True)
            raise click.Abort()

    asyncio.run(run())


@cli.command()
@click.argument("function_id")
@click.argument("function_file", type=click.Path(exists=True))
@click.option("--version", "-v", required=True, help="Function version")
@click.pass_context
def deploy(ctx, function_id, function_file, version):
    """Deploy a decision function"""
    engine = ctx.obj["engine"]

    # Load function code
    with open(function_file) as f:
        function_code = f.read()

    # Deploy
    async def run():
        try:
            await engine.deploy_function(function_id, version, function_code)
            click.echo(f"✅ Deployed {function_id} version {version}")
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

    asyncio.run(run())


@cli.command()
@click.argument("function_id")
@click.option("--version", "-v", help="Function version (defaults to latest)")
@click.option("--test-data", "-t", help="Test data file (JSON)")
@click.pass_context
def test(ctx, function_id, version, test_data):
    """Test a decision function"""
    engine = ctx.obj["engine"]

    # Generate or load test data
    if test_data and Path(test_data).exists():
        with open(test_data) as f:
            input_data = json.load(f)
    else:
        # Default test data
        input_data = {
            "issue": "late",
            "customer": {"tier": "gold", "id": "test-123"},
            "order_amount": 1000,
        }

    # Execute test
    async def run():
        try:
            result = await engine.execute(function_id, input_data, version)
            click.echo("✅ Test successful")
            click.echo(f"Input: {json.dumps(input_data, indent=2)}")
            click.echo(f"Output: {json.dumps(result, indent=2)}")
        except Exception as e:
            click.echo(f"❌ Test failed: {e}", err=True)
            raise click.Abort()

    asyncio.run(run())


@cli.command()
@click.pass_context
def list(ctx):
    """List all available functions"""
    engine = ctx.obj["engine"]

    async def run():
        try:
            functions = await engine.list_functions()

            if not functions:
                click.echo("No functions found")
                return

            click.echo("Available Functions:")
            click.echo("===================")

            for function_id in sorted(functions):
                versions = await engine.list_versions(function_id)
                latest_version = versions[-1] if versions else "none"
                click.echo(f"📦 {function_id} (latest: {latest_version})")
                if len(versions) > 1:
                    click.echo(f"   Versions: {', '.join(versions)}")
                click.echo()

        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

    asyncio.run(run())


@cli.command()
@click.argument("function_id")
@click.option("--date", "-d", help="Date in YYYYMMDD format (defaults to today)")
@click.pass_context
def traces(ctx, function_id, date):
    """View traces for a function"""
    from datetime import datetime

    if date is None:
        date = datetime.now().strftime("%Y%m%d")

    trace_file = Path(f"./traces/{function_id}_{date}.jsonl")

    if not trace_file.exists():
        click.echo(f"No traces found for {function_id} on {date}")
        return

    click.echo(f"Traces for {function_id} on {date}:")
    click.echo("=" * 50)

    with open(trace_file) as f:
        for line_num, line in enumerate(f, 1):
            try:
                trace = json.loads(line.strip())
                click.echo(f"Trace {line_num}:")
                click.echo(f"  ID: {trace.get('trace_id', 'N/A')}")
                click.echo(f"  Status: {trace.get('status', 'N/A')}")
                click.echo(f"  Timestamp: {trace.get('timestamp', 'N/A')}")
                if trace.get("status") == "success":
                    click.echo(
                        f"  Output: {json.dumps(trace.get('output', {}), indent=4)}"
                    )
                else:
                    click.echo(
                        f"  Error: {trace.get('output', {}).get('error', 'N/A')}"
                    )
                click.echo()
            except json.JSONDecodeError:
                click.echo(f"  Invalid JSON on line {line_num}")


@cli.command()
@click.argument("function_id")
@click.option("--version", "-v", help="Function version")
@click.pass_context
def info(ctx, function_id, version):
    """Show information about a function"""
    engine = ctx.obj["engine"]

    async def run():
        try:
            versions = await engine.list_versions(function_id)

            if not versions:
                click.echo(f"Function '{function_id}' not found")
                return

            click.echo(f"Function: {function_id}")
            click.echo(f"Versions: {', '.join(versions)}")
            click.echo(f"Latest: {versions[-1]}")

            if version:
                if version not in versions:
                    click.echo(f"Version '{version}' not found")
                    return

                # Try to load function to show basic info
                try:
                    function = await engine.storage.load_function(function_id, version)
                    click.echo("Function loaded successfully")
                    click.echo(f"Type: {type(function).__name__}")
                except Exception as e:
                    click.echo(f"Error loading function: {e}")

        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

    asyncio.run(run())


@cli.command()
@click.option("--function-id", help="Function ID to clear")
@click.option("--all", "clear_all", is_flag=True, help="Clear all traces")
@click.pass_context
def clear(ctx, function_id, clear_all):
    """Clear traces"""
    trace_dir = Path("./traces")

    if not trace_dir.exists():
        click.echo("No traces directory found")
        return

    if clear_all:
        # Clear all traces
        for trace_file in trace_dir.glob("*.jsonl"):
            trace_file.unlink()
        click.echo("✅ Cleared all traces")
    elif function_id:
        # Clear traces for specific function
        count = 0
        for trace_file in trace_dir.glob(f"{function_id}_*.jsonl"):
            trace_file.unlink()
            count += 1
        click.echo(f"✅ Cleared {count} trace files for {function_id}")
    else:
        click.echo("Please specify --function-id or --all")


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize the decision layer (create directories)"""
    # Create necessary directories
    directories = ["./data/functions", "./traces", "./config"]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        click.echo(f"✅ Created {directory}")

    # Create default config if it doesn't exist
    config_file = Path("config.yaml")
    if not config_file.exists():
        default_config = {
            "storage": {"backend": "file", "path": "./data"},
            "plugins": {
                "validation": {"enabled": True, "strict": False},
                "tracing": {"enabled": True, "path": "./traces"},
                "caching": {"enabled": True, "ttl": 300},
            },
            "api": {"host": "0.0.0.0", "port": 8000, "cors": True},
        }

        with open(config_file, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False)

        click.echo(f"✅ Created {config_file}")

    click.echo("🎉 Decision Layer initialized successfully!")


if __name__ == "__main__":
    cli()
