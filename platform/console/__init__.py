"""Story OS V3 Web Console domain contracts.

The console layer only describes product-facing views and navigation.
It does not own workflow/agent state.
"""

from .contracts import ConsoleModule, ConsolePage

__all__ = ["ConsoleModule", "ConsolePage"]
