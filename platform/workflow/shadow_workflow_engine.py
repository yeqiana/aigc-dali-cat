from dataclasses import dataclass


@dataclass
class NextStepDecision:
    current_step: str
    next_step: str | None
    reason: str


class ShadowWorkflowEngine:
    """
    Shadow workflow engine.

    Only calculates the expected next step.
    Does not execute tasks or change runtime state.
    """

    def decide_next_step(self, current_step: str, status: str) -> NextStepDecision:
        transitions = {
            ("IMAGE_GENERATE", "SUCCESS"): "IMAGE_REVIEW",
            ("IMAGE_REVIEW", "SUCCESS"): "RELEASE",
            ("PROMPT_COMPILE", "SUCCESS"): "IMAGE_GENERATE",
        }

        next_step = transitions.get((current_step, status))

        return NextStepDecision(
            current_step=current_step,
            next_step=next_step,
            reason="shadow transition calculation",
        )
