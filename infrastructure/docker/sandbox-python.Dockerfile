# Sandbox image for executing LLM-generated pytest tests. Never used to run
# anything except test code inside an isolated, network-disabled container --
# see app/services/sandbox/docker_runner.py.
FROM python:3.12-slim

RUN groupadd --gid 1000 sandbox \
    && useradd --uid 1000 --gid sandbox --shell /bin/sh --create-home sandbox

RUN pip install --no-cache-dir pytest==8.3.4

USER sandbox
WORKDIR /workspace
