#!/bin/bash
cd /home/kavia/workspace/code-generation/weatherwise-event-planner-27795-27892/events_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

