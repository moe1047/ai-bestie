from .state import VeeState


def mode_decider_edge(state: VeeState) -> str:
    """Determines the next node based on the 'mode' in the state."""
    print("\n--- (edge) MODE DECIDER ---")
    mode = state.get("mode")
    print(f"Routing to: {mode}")
    return mode


