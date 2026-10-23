#!/usr/bin/env bash
# Checks that pages.yml publishes only a commit on main that Validate (test.yml) passed: pull_request, a completed
# workflow_run of Validate on main and workflow_dispatch start it, and a push does not; on a workflow_run the build job
# runs only for a successful Validate run of a push or a manual run in this repository and checks out the commit
# Validate tested; the deploy job runs only when the build job reports that commit is still the tip of main. Then runs
# the step that reads the tip against a fake gh: the tested commit at the tip publishes, an older one does not, and a
# failed read fails the step.
# WORKFLOW_FILE selects the workflow under test (relative to the repository root, or absolute).
set -euo pipefail

root=$(cd "$(dirname "$0")/../.." && pwd)
workflow="${WORKFLOW_FILE:-.github/workflows/pages.yml}"
case "$workflow" in
  /*) workflow_path="$workflow" ;;
  *) workflow_path="$root/$workflow" ;;
esac
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
count=0
failures=0

# expect <name> <actual> <expected>
expect() {
  count=$((count + 1))
  if [ "$2" = "$3" ]; then
    echo "ok   $1"
  else
    failures=$((failures + 1))
    echo "FAIL $1: expected $3, got $2"
  fi
}

squeeze() { tr -s ' \n' ' ' | sed 's/^ //; s/ $//'; }
build_condition="github.event_name != 'workflow_run' || ( github.event.workflow_run.conclusion == 'success' && (github.event.workflow_run.event == 'push' || github.event.workflow_run.event == 'workflow_dispatch') && github.event.workflow_run.head_repository.full_name == github.repository)"
expect 'the triggers' "$(yq -o=json -I=0 '.on | keys' "$workflow_path")" '["pull_request","workflow_run","workflow_dispatch"]'
expect 'the workflow_run follows Validate on main' "$(yq -o=json -I=0 '.on.workflow_run' "$workflow_path")" \
  '{"workflows":["Validate"],"types":["completed"],"branches":["main"]}'
expect 'test.yml is the workflow named Validate' "$(yq -r '.name' "$root/.github/workflows/test.yml")" 'Validate'
expect 'the build job condition' "$(yq -r '.jobs.build.if' "$workflow_path" | squeeze)" "$build_condition"
expect 'the build job reports whether to publish' "$(yq -r '.jobs.build.outputs.publish' "$workflow_path")" '${{ steps.tip.outputs.publish }}'
expect 'the tip step runs on a workflow_run' "$(yq -r '.jobs.build.steps[] | select(.id == "tip") | .if' "$workflow_path")" "github.event_name == 'workflow_run'"
expect 'the tip step reads the tested commit' "$(yq -r '.jobs.build.steps[] | select(.id == "tip") | .env.TESTED' "$workflow_path")" \
  '${{ github.event.workflow_run.head_sha }}'
expect 'the build checks out the tested commit' \
  "$(yq -r '.jobs.build.steps[] | select(.uses // "" | test("^actions/checkout@")) | .with.ref' "$workflow_path")" '${{ github.event.workflow_run.head_sha }}'
expect 'the deploy job needs the build job' "$(yq -o=json -I=0 '[.jobs.deploy.needs] | flatten' "$workflow_path")" '["build"]'
expect 'the deploy job runs only to publish' "$(yq -r '.jobs.deploy.if' "$workflow_path")" "needs.build.outputs.publish == 'true'"

yq -r '.jobs.build.steps[] | select(.id == "tip") | .run' "$workflow_path" > "$work/step.sh"
mkdir "$work/bin"
cat > "$work/bin/gh" <<'EOF'
#!/usr/bin/env bash
echo "$*" >> "$STUB_LOG"
[ "${STUB_FAIL:-0}" = 1 ] && { echo 'HTTP 502' >&2; exit 1; }
echo "$STUB_TIP"
EOF
chmod +x "$work/bin/gh"

tested=0123456789abcdef0123456789abcdef01234567
newer=fedcba9876543210fedcba9876543210fedcba98

# tip <name> <tip of main> <read fails> <exit code> <publish output>
tip() {
  local name=$1 rc=0
  : > "$work/log"; : > "$work/output"
  STUB_LOG="$work/log" STUB_TIP="$2" STUB_FAIL="$3" TESTED="$tested" GITHUB_REPOSITORY=o/r GITHUB_OUTPUT="$work/output" \
    PATH="$work/bin:$PATH" bash -e "$work/step.sh" > /dev/null 2>&1 || rc=$?
  expect "$name: exit code" "$rc" "$4"
  expect "$name: output" "$(cat "$work/output")" "$5"
  expect "$name: gh call" "$(cat "$work/log")" 'api repos/o/r/commits/main --jq .sha'
}
tip 'the tested commit is the tip' "$tested" 0 0 'publish=true'
tip 'main moved past the tested commit' "$newer" 0 0 'publish=false'
tip 'the tip cannot be read' "$tested" 1 1 ''

echo "$count checks, $failures failed"
[ "$failures" = 0 ]
