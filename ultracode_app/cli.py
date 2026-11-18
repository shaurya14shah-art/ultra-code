"""
ULTRA CODE — CLI Entry Point
The main executable entry for the terminal app.
"""

import sys
import asyncio
import click

from .core.config import UltraCodeConfig
from .ui.terminal import UltraCodeApp

@click.command()
@click.option("--model", help="Override the default LLM model (e.g., gemini-2.5-pro)")
@click.option("--verbose", is_flag=True, help="Enable verbose error logging")
@click.option("--dir", "working_dir", default=".", help="Set the working directory (defaults to current)")
@click.option("--no-stream", is_flag=True, help="Disable streaming output")
def main(model: str, verbose: bool, working_dir: str, no_stream: bool):
    """
    ULTRA CODE — Terminal-Based Multi-Agent AI Coding System.
    
    Launch the interactive REPL to collaborate with the 12-agent fleet.
    """
    
    # Load config and apply CLI overrides
    config = UltraCodeConfig.load(working_dir)
    
    if model:
        config.model = model
    if verbose:
        config.verbose = True
    if no_stream:
        config.stream_output = False
        
    # Start the UI
    try:
        ui = UltraCodeApp(config)
        asyncio.run(ui.run_app())
    except KeyboardInterrupt:
        print("\n\n👋 ULTRA CODE signing off.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        if config.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
