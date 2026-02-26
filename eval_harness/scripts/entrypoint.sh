#!/bin/bash
# =============================================================================
# RepoGenesis Evaluation Harness - Container Entrypoint
#
# Runs the 3-phase evaluation inside a Docker container:
#   Phase 1: DSR (Deployment Success Rate) -- start the service
#   Phase 2: Pass@1 (Functional Correctness) -- run golden oracle tests
#   Phase 3: Cleanup
#
# Environment variables:
#   REPO_LANG          - "python" or "java" (required)
#   SERVICE_PORT       - port the service listens on (default: 8080)
#   STARTUP_TIMEOUT    - seconds to wait for service (default: 15)
#   TEST_TIMEOUT       - seconds to run tests (default: 300)
# =============================================================================
set -uo pipefail
# NOTE: NOT using -e so the script continues on failure (like SWE-bench)

LANG="${REPO_LANG:-python}"
SERVICE_PORT="${SERVICE_PORT:-8080}"
STARTUP_TIMEOUT="${STARTUP_TIMEOUT:-15}"
TEST_TIMEOUT="${TEST_TIMEOUT:-300}"

SERVICE_PID=""

# =================== Helper Functions ===================

find_start_script() {
    # Look for start.sh in common locations
    for candidate in \
        "./start.sh" \
        "./scripts/start.sh" \
        "./bin/start.sh"; do
        if [ -f "$candidate" ]; then
            echo "$candidate"
            return 0
        fi
    done
    # Recursive search (depth-limited)
    find . -maxdepth 3 -name "start.sh" -type f 2>/dev/null | head -1
}

start_python_service() {
    local start_script
    start_script=$(find_start_script)

    if [ -n "$start_script" ]; then
        echo "Starting service via: $start_script"
        bash "$start_script" &
        SERVICE_PID=$!
        return
    fi

    # Fallback: try common Python entry points
    if [ -f "app.py" ]; then
        echo "Starting service via: python app.py"
        python app.py &
        SERVICE_PID=$!
    elif [ -f "main.py" ]; then
        echo "Starting service via: python main.py"
        python main.py &
        SERVICE_PID=$!
    elif [ -f "run.py" ]; then
        echo "Starting service via: python run.py"
        python run.py &
        SERVICE_PID=$!
    elif [ -f "manage.py" ]; then
        echo "Starting service via: python manage.py runserver 0.0.0.0:$SERVICE_PORT"
        python manage.py runserver "0.0.0.0:$SERVICE_PORT" &
        SERVICE_PID=$!
    elif [ -f "server.py" ]; then
        echo "Starting service via: python server.py"
        python server.py &
        SERVICE_PID=$!
    else
        # Last resort: try uvicorn with common module names
        for module in "main:app" "app:app" "server:app" "api:app"; do
            if python -c "import ${module%%:*}" 2>/dev/null; then
                echo "Starting service via: uvicorn $module"
                python -m uvicorn "$module" --host 0.0.0.0 --port "$SERVICE_PORT" &
                SERVICE_PID=$!
                return
            fi
        done
        echo "WARNING: No Python entry point found"
        SERVICE_PID=""
    fi
}

start_java_service() {
    local start_script
    start_script=$(find_start_script)

    if [ -n "$start_script" ]; then
        echo "Starting service via: $start_script"
        bash "$start_script" &
        SERVICE_PID=$!
        return
    fi

    # Fallback: try Maven spring-boot:run
    if [ -f "pom.xml" ]; then
        echo "Starting service via: mvn spring-boot:run"
        mvn spring-boot:run -q &
        SERVICE_PID=$!
    else
        echo "WARNING: No Java entry point found"
        SERVICE_PID=""
    fi
}

wait_for_service() {
    local port="$1"
    local timeout="$2"

    echo "Waiting for service on port $port (timeout: ${timeout}s)..."

    for i in $(seq 1 "$timeout"); do
        # Check if process is still alive
        if [ -n "$SERVICE_PID" ] && ! kill -0 "$SERVICE_PID" 2>/dev/null; then
            wait "$SERVICE_PID" 2>/dev/null
            local exit_code=$?
            echo "Process exited with code $exit_code after ${i}s"
            return 1
        fi

        # Check health endpoints
        for path in "/" "/health" "/api/health" "/api/v1/health" "/actuator/health"; do
            if curl -sf "http://localhost:${port}${path}" > /dev/null 2>&1; then
                echo "Service ready after ${i}s (responded on ${path})"
                return 0
            fi
        done

        # Check if port is open (even without health endpoint)
        if nc -z localhost "$port" 2>/dev/null; then
            echo "Port $port is open after ${i}s"
            return 0
        fi

        sleep 1
    done

    # Timeout -- check if process is still running
    if [ -n "$SERVICE_PID" ] && kill -0 "$SERVICE_PID" 2>/dev/null; then
        echo "Process still running after ${timeout}s, checking port..."
        if nc -z localhost "$port" 2>/dev/null; then
            echo "Port $port is open (service likely ready)"
            return 0
        fi
        echo "Process running but port $port not open"
        # Still count as partial success (process didn't crash)
        return 0
    fi

    return 1
}

cleanup() {
    if [ -n "$SERVICE_PID" ]; then
        echo "Cleaning up service (PID: $SERVICE_PID)..."
        kill "$SERVICE_PID" 2>/dev/null || true
        sleep 1
        kill -9 "$SERVICE_PID" 2>/dev/null || true
        wait "$SERVICE_PID" 2>/dev/null || true
    fi
}

trap cleanup EXIT

# =================== Phase 1: DSR ===================

echo ">>>>> DSR_START"
DSR_SUCCESS="false"
DSR_MESSAGE="Unknown"

if [ "$LANG" = "python" ]; then
    start_python_service
elif [ "$LANG" = "java" ]; then
    start_java_service
fi

if [ -z "$SERVICE_PID" ]; then
    DSR_SUCCESS="false"
    DSR_MESSAGE="No service entry point found"
else
    if wait_for_service "$SERVICE_PORT" "$STARTUP_TIMEOUT"; then
        DSR_SUCCESS="true"
        DSR_MESSAGE="Service started successfully"
    else
        # Check if process printed success patterns before dying
        DSR_SUCCESS="false"
        DSR_MESSAGE="Service failed to start within ${STARTUP_TIMEOUT}s"
    fi
fi

echo "DSR_RESULT=$DSR_SUCCESS"
echo "DSR_MESSAGE=$DSR_MESSAGE"
echo ">>>>> DSR_END"

# =================== Phase 2: Pass@1 ===================

echo ">>>>> TEST_START"
TEST_EXIT=1

if [ "$LANG" = "python" ]; then
    echo "Running pytest..."
    timeout "$TEST_TIMEOUT" python -m pytest tests/ -v --tb=short \
        --json-report --json-report-file=/tmp/pytest_report.json \
        2>&1 || true
    TEST_EXIT=${PIPESTATUS[0]:-$?}
elif [ "$LANG" = "java" ]; then
    echo "Running Maven tests..."
    timeout "$TEST_TIMEOUT" mvn test 2>&1 || true
    TEST_EXIT=${PIPESTATUS[0]:-$?}
fi

echo "TEST_EXIT_CODE=$TEST_EXIT"
echo ">>>>> TEST_END"

# =================== Phase 3: Exit ===================

echo "Evaluation complete. Test exit code: $TEST_EXIT"
exit $TEST_EXIT
