# Sourced by evaluate-checks.sh. The unit/lint/type-check checks gate every PR.
# The e2e + e2e-ui suites also gate PRs. `E2E Tests` and the mock-LLM
# `E2E UI Tests` use no secrets and run on fork PRs directly (like CI). The
# secret-bearing legs -- `E2E UI Native` and `Integration` -- cannot read the
# LLM_API_KEY / GATEWAY_BASE_URL secrets on a fork pull_request, so they skip
# there (empty matrix) and run via the fork-e2e/** mirror push after approval.
# Every e2e/e2e-ui/integration shard name is therefore in BOTH REQUIRED (a
# same-repo PR must pass it) and ALLOW_SKIP (a draft- or fork-skipped check
# still satisfies the gate; the fork-approval block lives in compute-gate.sh).
# Generated file -- do not hand-edit; it is replaced wholesale on every sync.
# NOTE: when changing the e2e-ui shard counts or adding the `E2E UI Native`
# leg, update the generator's source of truth too (the names below mirror the
# job `name:` templates in .github/workflows/e2e-ui.yml).

REQUIRED=(
  "Pre-commit checks"
  "Pytest (runtime-harnesses)"
  "Pytest (runtime-policies)"
  "Pytest (runtime-core)"
  "Pytest (inner-terminal)"
  "Pytest (inner-env)"
  "Pytest (inner-tracing)"
  "Pytest (inner-rest)"
  "Pytest (tools)"
  "Pytest (repl-sdk)"
  "Pytest (server-responses)"
  "Pytest (server-rest)"
  "Pytest (spec-llms)"
  "Pytest (misc)"
  "E2E Tests (shard 0/4)"
  "E2E Tests (shard 1/4)"
  "E2E Tests (shard 2/4)"
  "E2E Tests (shard 3/4)"
  "E2E UI Tests (shard 0/3)"
  "E2E UI Tests (shard 1/3)"
  "E2E UI Tests (shard 2/3)"
  "E2E UI Native (shard 0/2)"
  "E2E UI Native (shard 1/2)"
  "Integration (claude-sdk)"
  "Integration (openai-agents)"
  "Integration (codex)"
)

ALLOW_SKIP=(
  "Pytest (runtime-harnesses)"
  "Pytest (runtime-policies)"
  "Pytest (runtime-core)"
  "Pytest (inner-terminal)"
  "Pytest (inner-env)"
  "Pytest (inner-tracing)"
  "Pytest (inner-rest)"
  "Pytest (tools)"
  "Pytest (repl-sdk)"
  "Pytest (server-responses)"
  "Pytest (server-rest)"
  "Pytest (spec-llms)"
  "Pytest (misc)"
  "E2E Tests (shard 0/4)"
  "E2E Tests (shard 1/4)"
  "E2E Tests (shard 2/4)"
  "E2E Tests (shard 3/4)"
  "E2E UI Tests (shard 0/3)"
  "E2E UI Tests (shard 1/3)"
  "E2E UI Tests (shard 2/3)"
  "E2E UI Native (shard 0/2)"
  "E2E UI Native (shard 1/2)"
  "Integration (claude-sdk)"
  "Integration (openai-agents)"
  "Integration (codex)"
)

is_allow_skip() { printf '%s\n' "${ALLOW_SKIP[@]}" | grep -qxF "$1"; }

# Maps an ALLOW_SKIP check to the workflow that produces it, so
# evaluate-checks.sh can tell a genuine skip (a CI Pytest shard path-skip, or
# the fork guard skipping an e2e job) from a check that is merely absent
# because its workflow is still queued or re-running.
workflow_for() {
  case "$1" in
    "Pytest ("*)              echo "CI" ;;
    "E2E Tests (shard "*)     echo "E2E Tests" ;;
    # Both e2e-ui jobs (mock + native) live in the one "E2E UI Tests" workflow.
    "E2E UI Tests (shard "*)  echo "E2E UI Tests" ;;
    "E2E UI Native (shard "*) echo "E2E UI Tests" ;;
    "Integration ("*)         echo "Integration Tests" ;;
    *)                        echo "" ;;
  esac
}
