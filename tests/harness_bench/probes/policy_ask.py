"""Policy-ASK probe — does an ASK policy raise an elicitation for approval?

The third verdict on the policy axis. With an ``ask`` policy on the tool_call
phase, a provoked tool call should park for user approval, which omnigent
surfaces as an elicitation (SSE ``response.elicitation_request`` /
``pending_elicitations``) — the same signal the web UI renders an approval
prompt from. The probe drives the ask policy, observes that an elicitation was
raised (``elicitation_requested``), and the driver resolves it so the turn
settles instead of parking for the (day-long) ASK timeout.

Observability: full-server bakes the ASK policy in the agent spec and watches
the session stream for the elicitation request. The wrap-direct and native
transports have no elicitation surface wired here yet, so they return an
unmeasured result and the probe SKIPs — never a false verdict.
"""

from __future__ import annotations

from tests.harness_bench.driver import infra_failure_reason
from tests.harness_bench.probes.base import CapabilityProbe
from tests.harness_bench.profile import BenchProfile
from tests.harness_bench.transport import Driver
from tests.harness_bench.verdict import Applicability, Priority, ProbeResult, Verdict


class PolicyAskProbe(CapabilityProbe):
    name = "policy_ask"
    title = "Policy ASK"
    priority = Priority.P1
    applies_to = Applicability.BOTH

    async def run(self, driver: Driver, profile: BenchProfile) -> ProbeResult:
        result = await driver.run_policy_turn(action="ask")
        detail = {
            "elicitation_requested": result.elicitation_requested,
            "tool_calls": [tc.get("name") for tc in result.tool_calls],
            "completed": result.completed,
        }

        if result.elicitation_requested:
            return ProbeResult(
                Verdict.SUPPORTED,
                note="ASK policy raised an elicitation (approval prompt) for the tool call",
                detail=detail,
            )

        infra = infra_failure_reason(result)
        if infra is not None:
            return ProbeResult(Verdict.SKIPPED, note=infra, detail=detail)
        if result.timed_out:
            return ProbeResult(Verdict.SKIPPED, note="ask-policy turn timed out", detail=detail)
        if not result.tool_calls and not result.completed:
            # Unmeasured (no elicitation surface on this transport) or the model
            # never called the tool: the ASK path was not exercised here.
            return ProbeResult(
                Verdict.SKIPPED,
                note=(
                    "ASK policy not observable on this transport "
                    "(or the model never attempted the tool)"
                ),
                detail=detail,
            )
        # The tool call resolved without a visible elicitation — not a clean ASK
        # observation; SKIP rather than assert a false UNSUPPORTED.
        return ProbeResult(
            Verdict.SKIPPED,
            note="tool call did not raise a visible elicitation under the ASK policy",
            detail=detail,
        )
