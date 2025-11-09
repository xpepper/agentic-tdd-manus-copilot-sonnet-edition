from rich.console import Console
from rich.theme import Theme

# Define a custom theme for better agent distinction
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
    "success": "bold green",
    "agent": "bold blue",
    "tester": "bold yellow",
    "implementer": "bold magenta",
    "refactorer": "bold cyan",
    "supervisor": "bold white on blue",
    "command": "green",
    "output": "dim white",
})

console = Console(theme=custom_theme)

def log_info(message: str):
    """Logs a general information message."""
    console.print(f"[info]INFO:[/info] {message}")

def log_success(message: str):
    """Logs a success message."""
    console.print(f"[success]SUCCESS:[/success] {message}")

def log_danger(message: str):
    """Logs a critical error or danger message."""
    console.print(f"[danger]DANGER:[/danger] {message}")

def log_agent_action(agent_name: str, action: str, details: str = ""):
    """Logs an action taken by a specific agent."""
    style = agent_name.lower()
    console.print(f"[{style}]{agent_name.upper()}:[/] {action} {details}")

def log_command(command: str, cwd: str):
    """Logs a shell command being executed."""
    console.print(f"[command]CMD:[/command] [output]{command}[/output] (in [info]{cwd}[/info])")

def log_command_output(output: str):
    """Logs the output of a shell command."""
    console.print(f"[output]{output}[/output]")
