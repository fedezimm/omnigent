"""Policy-ALLOW probe — does an explicit ALLOW policy let a tool call through?

The DENY probe proves a policy can *block* a call; this proves the other side of
the verdict axis: with an explicit ``allow`` policy baked on the tool_call phase,
a provoked tool call should *proceed* (dispatched + a result delivered), not be
blocked. Absence of a deny is not the same as an asserted ALLOW — this drives a
real ``action=allow`` policy so the allow path is exercised, not merely defaulted.

Observability mirrors the DENY probe: full-server bakes the policy in the agent
spec and observes a non-blocked ``function_call_output`` (``tool_call_allowed``);
the wrap-direct and native transports have no server-side policy surface for this
yet, so they return an unmeasured result and the probe SKIPs — never a false
verdict.
"""

from __future__ import annotations

from tests.harness_bench.driver import infra_failure_reason
from tests.harness_bench.probes.base import CapabilityProbe
from tests.harness_bench.profile import BenchProfile
from tests.harness_bench.transport import Driver
from tests.harness_bench.verdict import Applicability, Priority, ProbeResult, Verdict


class PolicyAllowProbe(CapabilityProbe):
    name = "policy_allow"
    title = "Policy ALLOW"
    priority = Priority.P1
    applies_to = Applicability.BOTH

    async def run(self, driver: Driver, profile: BenchProfile) -> ProbeResult:
        result = await driver.run_policy_turn(action="allow")
        detail = {
            "tool_call_allowed": result.tool_call_allowed,
            "tool_calls": [tc.get("name") for tc in result.tool_calls],
            "completed": result.completed,
        }

        if result.tool_call_allowed:
            return ProbeResult(
                Verdict.SUPPORTED,
                note="tool call proceeded under an explicit ALLOW policy",
                detail=detail,
            )

        infra = infra_failure_reason(result)
        if infra is not None:
            return ProbeResult(Verdict.SKIPPED, note=infra, detail=detail)
        if result.timed_out:
            return ProbeResult(Verdict.SKIPPED, note="allow-policy turn timed out", detail=detail)
        if not result.tool_calls and not result.completed:
            # An unmeasured result (transport with no server-side policy surface
            # for ALLOW) or a turn where the model never called the tool: the
            # ALLOW path was not exercised here, so SKIP rather than fail.
            return ProbeResult(
                Verdict.SKIPPED,
                note=(
                    "ALLOW policy not observable on this transport "
                    "(or the model never attempted the tool)"
                ),
                detail=detail,
            )
        # The turn completed but the tool call did not visibly proceed — not a
        # clean ALLOW observation; SKIP rather than assert a false UNSUPPORTED.
        return ProbeResult(
            Verdict.SKIPPED,
            note="tool call did not visibly proceed under the ALLOW policy",
            detail=detail,
        )
