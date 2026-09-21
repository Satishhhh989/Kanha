import asyncio
import typer
import uuid
from rich.console import Console
from rich.panel import Panel

from core.config import settings
from core.agent import agent_runtime
from infrastructure.logging import setup_logging
from sysplatform import adapter

app = typer.Typer(help="KAHNA CLI - Local AI Computer Agent")
console = Console()

@app.command()
def start(services: str = typer.Option("api,telegram", help="Comma-separated list of services to start (e.g., api,telegram,voice)")):
    """Starts the KAHNA API server and specified services."""
    import os
    os.environ["KAHNA_SERVICES"] = services
    
    from apps.api import run_server
    console.print(f"[green]Starting KAHNA API server on {settings.host}:{settings.port}[/green]")
    console.print(f"[green]Enabled services: {services}[/green]")
    run_server()

@app.command()
def desktop():
    """Starts the KAHNA desktop GUI, Voice, and Telegram services simultaneously."""
    import os
    import subprocess
    import sys
    
    # Enable all primary services for the desktop experience
    services = "api,telegram,voice"
    os.environ["KAHNA_SERVICES"] = services
    
    console.print(f"[green]Starting KAHNA backend (Services: {services})...[/green]")
    
    # Start the backend server as a subprocess
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "apps.cli.main", "start", "--services", services],
        env=os.environ.copy()
    )
    
    console.print("[green]Starting KAHNA Desktop GUI...[/green]")
    
    # Start the Tauri dev server (assuming dev environment)
    desktop_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "desktop")
    
    try:
        # Run npm run tauri dev
        frontend_process = subprocess.Popen(
            ["npm", "run", "tauri", "dev"],
            cwd=desktop_dir
        )
        frontend_process.wait()
    except KeyboardInterrupt:
        console.print("[yellow]Shutting down...[/yellow]")
    finally:
        if 'frontend_process' in locals():
            frontend_process.terminate()
        if 'backend_process' in locals():
            backend_process.terminate()


@app.command()
def chat(session_id: str = typer.Option(None, help="Session ID to resume")):
    """Starts an interactive chat session in the terminal."""
    # Ensure logs don't clutter the interactive terminal
    setup_logging(level="WARNING")
    
    sid = session_id or str(uuid.uuid4())
    console.print(Panel(f"Session started: [bold cyan]{sid}[/bold cyan]\nType 'exit' or 'quit' to end.", title="KAHNA", border_style="cyan"))
    
    async def chat_loop():
        while True:
            try:
                user_input = console.input("[bold blue]You:[/bold blue] ")
                if user_input.lower() in ("exit", "quit"):
                    break
                if not user_input.strip():
                    continue
                    
                response = await agent_runtime.chat(sid, user_input)
                console.print(f"[bold magenta]KAHNA:[/bold magenta] {response}")
            except (KeyboardInterrupt, EOFError):
                break
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {str(e)}")

    asyncio.run(chat_loop())
    console.print("[yellow]Session ended.[/yellow]")

@app.command()
def voice():
    """Starts a continuous voice interaction session in the terminal."""
    setup_logging(level="WARNING")
    console.print(Panel("Voice Session Started!\nSpeak into your microphone.\nPress Ctrl+C to exit.", title="KAHNA Voice", border_style="cyan"))
    
    async def voice_loop():
        from core.voice.factory import voice_manager
        
        # Start voice manager. Since we bypassed Wake Word, it will trigger LISTENING on first speech.
        await voice_manager.start()
        try:
            # Keep the event loop running
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            voice_manager.stop()

    try:
        asyncio.run(voice_loop())
    except (KeyboardInterrupt, EOFError):
        console.print("[yellow]Voice session ended.[/yellow]")

@app.command()
def doctor():
    """Runs a diagnostic check of the environment and platform."""
    console.print("[bold cyan]KAHNA Diagnostic Check[/bold cyan]")
    
    # 1. Config Check
    console.print("\n[bold]1. Configuration[/bold]")
    console.print(f"Environment: {settings.environment}")
    console.print(f"Log Level: {settings.log_level}")
    console.print(f"OpenRouter Configured: {'Yes' if settings.openrouter_api_key != 'your_openrouter_api_key_here' else 'No (Default)'}")
    
    # 2. Platform Check
    console.print("\n[bold]2. Platform Abstraction[/bold]")
    try:
        info = adapter.get_system_info()
        console.print(f"OS: {info.os_name} {info.os_version}")
        console.print(f"Arch: {info.architecture}")
        console.print(f"Python: {info.python_version}")
        console.print(f"Memory: {info.memory_total_gb} GB")
        console.print("[green]Platform adapter loaded successfully.[/green]")
    except Exception as e:
        console.print(f"[red]Platform check failed: {str(e)}[/red]")
        
    console.print("\n[green]Diagnostics complete.[/green]")

if __name__ == "__main__":
    app()
