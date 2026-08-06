#!/usr/bin/env bash
# Bring the backend up in the shape a given job needs.
#
# Compose profiles decide *what* runs; this script decides *in what order*,
# which profiles cannot express: alembic has to finish before the api that
# reads the tables it creates starts, and compose returns as soon as a
# container is created rather than when it answers.
#
# With no flags it brings up the infrastructure alone — postgres, redis,
# rabbitmq and elasticsearch — which is what the integration tests need.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

WITH_APP=0
WITH_AI=0
WITH_LOGS=0
DO_MIGRATE=0
DO_SEED=0
ACTION=up
ADMIN_USER=""
TAIL_SERVICES=()

usage() {
    cat <<'USAGE'
usage: ./run.sh [flags]

what comes up (infrastructure always does)
  -a, --app            api, worker and scheduler
  -i, --ai             the ai app, its database and ollama
  -l, --logs           kibana and filebeat
  -e, --everything     all three

what runs on the way up
  -m, --migrate        alembic, before anything that reads the tables
  -s, --seed           the initial assets, sources and bubbles
  -f, --fresh          -m -s together, for an empty database

instead of bringing anything up
  -A, --admin USER     create a super admin, prompting for the password
  -b, --build [SVC]    rebuild images
  -p, --ps             what is running, and whether it is healthy
  -t, --tail [SVC]     follow logs
  -d, --down           stop everything, keep the data
  -R, --reset          stop everything and delete the volumes

  -h, --help           this

examples
  ./run.sh                     infrastructure only, for tests
  ./run.sh -a -f               a working api on an empty database
  ./run.sh -e -m               everything, migrations included
  ./run.sh -t worker           follow the worker

Ports come from backend/.env; see DOCKER.md.
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
    -a | --app) WITH_APP=1 ;;
    -i | --ai) WITH_AI=1 ;;
    -l | --logs) WITH_LOGS=1 ;;
    -e | --everything) WITH_APP=1 WITH_AI=1 WITH_LOGS=1 ;;
    -m | --migrate) DO_MIGRATE=1 ;;
    -s | --seed) DO_SEED=1 ;;
    -f | --fresh) DO_MIGRATE=1 DO_SEED=1 ;;
    -A | --admin)
        ACTION=admin
        ADMIN_USER="${2:?--admin needs a username}"
        shift
        ;;
    -b | --build)
        ACTION=build
        [[ ${2:-} && ${2:0:1} != - ]] && { TAIL_SERVICES=("$2"); shift; }
        ;;
    -p | --ps) ACTION=ps ;;
    -t | --tail)
        ACTION=tail
        [[ ${2:-} && ${2:0:1} != - ]] && { TAIL_SERVICES=("$2"); shift; }
        ;;
    -d | --down) ACTION=down ;;
    -R | --reset) ACTION=reset ;;
    -h | --help)
        usage
        exit 0
        ;;
    *)
        printf 'unknown flag: %s\n\n' "$1" >&2
        usage >&2
        exit 1
        ;;
    esac
    shift
done

# a box where the user is not in the docker group still has to work, and
# guessing wrong is a confusing permission error rather than a clear one
DC=(docker compose)
if ! docker info >/dev/null 2>&1; then
    DC=(sudo docker compose)
fi

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }
warn() { printf '\033[1;33m%s\033[0m\n' "$1" >&2; }

profile_args() {
    local args=()
    ((WITH_APP)) && args+=(--profile app)
    ((WITH_AI)) && args+=(--profile ai)
    ((WITH_LOGS)) && args+=(--profile logs)
    printf '%s\n' "${args[@]:-}"
}

mapfile -t PROFILES < <(profile_args)
PROFILES=("${PROFILES[@]:-}")
[[ -z ${PROFILES[0]} ]] && PROFILES=()

wait_healthy() {
    local deadline=$((SECONDS + ${RUN_TIMEOUT:-180}))
    local pending
    while ((SECONDS < deadline)); do
        pending=$("${DC[@]}" "${PROFILES[@]}" ps \
            --format '{{.Service}} {{.Health}}' \
            | awk '$2 != "healthy" && $2 != "" {print $1}')
        [[ -z $pending ]] && return 0
        sleep 3
    done
    warn "still not healthy after ${RUN_TIMEOUT:-180}s: ${pending//$'\n'/, }"
    return 1
}

all_profiles=(--profile app --profile ai --profile logs --profile tools)

case "$ACTION" in
admin)
    # no -p flag on the inner command: the prompt keeps the password out of
    # the shell history and out of the process list
    "${DC[@]}" run --rm scripts create-super-admin -u "$ADMIN_USER"
    ;;
build)
    "${DC[@]}" "${all_profiles[@]}" build "${TAIL_SERVICES[@]}"
    ;;
ps)
    "${DC[@]}" "${all_profiles[@]}" ps
    ;;
tail)
    "${DC[@]}" "${all_profiles[@]}" logs -f --tail 100 "${TAIL_SERVICES[@]}"
    ;;
down)
    "${DC[@]}" "${all_profiles[@]}" down
    ;;
reset)
    warn "this deletes every volume: postgres, redis, elasticsearch, media"
    read -rp "type the project name to confirm: " answer
    [[ $answer == amu-pulse ]] || {
        warn "aborted"
        exit 1
    }
    "${DC[@]}" "${all_profiles[@]}" down -v
    ;;
up)
    # infrastructure first and on its own, so a migration does not run
    # against a postgres that is still starting
    say "infrastructure"
    "${DC[@]}" up -d
    PROFILES=()
    wait_healthy

    ((DO_MIGRATE)) && {
        say "migrations"
        "${DC[@]}" run --rm migrate
        ((WITH_AI)) && "${DC[@]}" --profile ai up -d postgres-ai &&
            "${DC[@]}" run --rm ai-migrate
    }
    ((DO_SEED)) && {
        say "seed data"
        "${DC[@]}" run --rm seed
    }

    if ((WITH_APP || WITH_AI || WITH_LOGS)); then
        mapfile -t PROFILES < <(profile_args)
        say "services:${WITH_APP:+ app}${WITH_AI:+ ai}${WITH_LOGS:+ logs}"
        "${DC[@]}" "${PROFILES[@]}" up -d
        wait_healthy
    fi

    say "up"
    "${DC[@]}" "${PROFILES[@]}" ps
    ;;
esac
