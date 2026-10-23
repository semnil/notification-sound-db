#!/usr/bin/env bash
# Checks that pages.yml publishes only a commit on main that Validate (test.yml) passed: pull_request, a completed
# workflow_run of Validate on main and workflow_dispatch start it, and a push does not. A workflow_run publishes only for
# a successful Validate run of a push or a manual run in this repository whose tested commit is the last commit on the
# default branch the event names (github.sha); the build checks out that commit and no step reads a ref from the
# workflow_run payload. Only those runs share the concurrency group pages; every other run gets a group of its own, so
# it cannot cancel a pending publish. The publish condition is the same text in the group and in the build job.
# WORKFLOW_FILE selects the workflow under test (relative to the repository root, or absolute).
set -euo pipefail

root=$(cd "$(dirname "$0")/../.." && pwd)
workflow="${WORKFLOW_FILE:-.github/workflows/pages.yml}"
case "$workflow" in
  /*) workflow_path="$workflow" ;;
  *) workflow_path="$root/$workflow" ;;
esac
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
publish="github.event.workflow_run.conclusion == 'success' && (github.event.workflow_run.event == 'push' || github.event.workflow_run.event == 'workflow_dispatch') && github.event.workflow_run.head_repository.full_name == github.repository && github.sha == github.event.workflow_run.head_sha"
group="\${{ github.event_name == 'pull_request' && format('pages-pr-{0}', github.ref) || ( github.event_name == 'workflow_run' && $publish) && 'pages' || format('pages-run-{0}', github.run_id) }}"

expect 'the triggers' "$(yq -o=json -I=0 '.on | keys' "$workflow_path")" '["pull_request","workflow_run","workflow_dispatch"]'
expect 'the workflow_run follows Validate on main' "$(yq -o=json -I=0 '.on.workflow_run' "$workflow_path")" \
  '{"workflows":["Validate"],"types":["completed"],"branches":["main"]}'
expect 'test.yml is the workflow named Validate' "$(yq -r '.name' "$root/.github/workflows/test.yml")" 'Validate'
expect 'only publishing runs share the group pages' "$(yq -r '.concurrency.group' "$workflow_path" | squeeze)" "$group"
expect 'a running publish is not cancelled' "$(yq -r '.concurrency.cancel-in-progress' "$workflow_path")" 'false'
expect 'the build job runs a workflow_run only to publish' "$(yq -r '.jobs.build.if' "$workflow_path" | squeeze)" \
  "github.event_name != 'workflow_run' || ( $publish)"
expect 'the build checks out the commit the event names' \
  "$(yq -r '.jobs.build.steps[] | select(.uses // "" | test("^actions/checkout@")) | .with.ref' "$workflow_path")" 'null'
expect 'no step reads the workflow_run payload' \
  "$(yq -o=json -I=0 '[.jobs[].steps[]] | tostring | test("workflow_run")' "$workflow_path")" 'false'
expect 'the deploy job needs the build job' "$(yq -o=json -I=0 '[.jobs.deploy.needs] | flatten' "$workflow_path")" '["build"]'
expect 'the deploy job runs only for a workflow_run' "$(yq -r '.jobs.deploy.if' "$workflow_path")" "github.event_name == 'workflow_run'"

echo "$count checks, $failures failed"
[ "$failures" = 0 ]
