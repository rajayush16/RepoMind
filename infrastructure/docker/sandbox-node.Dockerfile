# Sandbox image for executing LLM-generated Jest/Vitest-style tests. Never used
# to run anything except test code inside an isolated, network-disabled
# container -- see app/services/sandbox/docker_runner.py.
FROM node:20-slim

RUN groupadd --gid 1000 sandbox \
    && useradd --uid 1000 --gid sandbox --shell /bin/sh --create-home sandbox

RUN npm install -g jest@29

USER sandbox
WORKDIR /workspace
