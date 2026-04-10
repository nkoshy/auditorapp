# Kubernetes Development Workflow

## Goal
Continue the develop -> deploy -> test -> fix cycle until all required tests pass.

## Source of truth for tests
The required end-to-end test suite is:

- tests/test_cases.md

If the file contains manual scenarios, convert them into executable tests when needed.
If executable tests already exist, use those instead of inventing new checks.

## Required commands
Use these commands as the default workflow:

1. Build and deploy to Kubernetes using the MCP server, the mcp server provides full access to namespace named automationx
2. You can use kaniko to build the docker image and push it to docker hub, my docker hub user name is nkoshy, kaniko job should use the same namespace and the completed jobs to be deleted.
2. Wait for rollout to complete
3. Ensure ingress is available at:
   https://'<appname>'.68.220.202.177.nip.io
4. You can use the annotation on the ingress resource to get letsencrypt certificate automatically. The Cluster Issuer to use is letsencrypt-prod
4. Run the required test suite, you can build an image with test suite files and execute it from the container in the same namespace
5. If any test fails:
   - inspect logs of the docker container.
   - inspect events
   - fix the application or manifests
   - redeploy
   - rerun the tests
6. Stop only when all required tests pass

## Deployment rules
- Use the Kubernetes MCP server for all cluster operations
- Never access resources outside the namespace exposed by the MCP server
- Always create or update an Ingress for hostname:
  <appname>.68.220.202.177.nip.io
- use annotations to get certificates from letencrypt - Cluster Issuer is already deployed- letsencrypt-prod
- reuse the ingress (do not delete and recreate for the same hostname unless needed as it can cause rate-limit with letsencrypt)
- use the container image registry registry.68.220.202.177.nip.io to push the code to after building the image using kaniko on k8s itself in automationx namespace - this registry does not require any credentials. Use batch/v1 Kind: Job with ttlSecondsAfterFinished: 300 for all kaniko builds. Never use Deployments for one-time build tasks.

## Test commands
Primary test command:

pytest tests/e2e -q

If a single required file is specified, prioritize tests derived from that file.

## Validation
A task is not complete until:
- deployment rollout succeeds
- ingress responds
- all required tests pass
