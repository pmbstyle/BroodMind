from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from octopal.runtime.workers.contracts import WorkerResult
from octopal.utils import should_suppress_user_delivery


class DeliveryMode(StrEnum):
    SILENT = "silent"
    DEFERRED = "deferred"
    IMMEDIATE = "immediate"


@dataclass(frozen=True)
class DeliveryDecision:
    mode: DeliveryMode
    text: str
    reason: str
    followup_required: bool = False

    @property
    def user_visible(self) -> bool:
        return self.mode in {DeliveryMode.DEFERRED, DeliveryMode.IMMEDIATE}


def resolve_user_delivery(
    text: str,
    *,
    followup_required: bool = False,
) -> DeliveryDecision:
    value = str(text or "")
    if should_suppress_user_delivery(value):
        return DeliveryDecision(
            mode=DeliveryMode.SILENT,
            text=value,
            reason="control_or_empty",
            followup_required=False,
        )
    return DeliveryDecision(
        mode=DeliveryMode.IMMEDIATE,
        text=value,
        reason="user_visible",
        followup_required=followup_required,
    )


def resolve_worker_followup_delivery(
    text: str,
    *,
    result: WorkerResult,
    pending_closure: bool,
    suppress_followup: bool,
    should_force: bool,
    forced_text_factory,
) -> DeliveryDecision:
    decision = resolve_user_delivery(text)
    if not decision.user_visible and (should_force or pending_closure):
        forced_text = forced_text_factory(result)
        forced_decision = resolve_user_delivery(forced_text)
        if forced_decision.user_visible:
            return DeliveryDecision(
                mode=DeliveryMode.DEFERRED if suppress_followup else DeliveryMode.IMMEDIATE,
                text=forced_decision.text,
                reason="forced_substantive_followup",
            )

    if not decision.user_visible:
        return DeliveryDecision(
            mode=DeliveryMode.SILENT,
            text=decision.text,
            reason="no_user_response",
        )

    if suppress_followup:
        return DeliveryDecision(
            mode=DeliveryMode.DEFERRED,
            text=decision.text,
            reason="suppressed_turn_followup",
        )

    return DeliveryDecision(
        mode=DeliveryMode.IMMEDIATE,
        text=decision.text,
        reason="user_visible_followup",
    )
