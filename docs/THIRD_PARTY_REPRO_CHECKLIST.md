# Third-party reproduction: 5-minute path

This is the smallest useful path for an independent runtime/eval engineer evaluating SABLE-002.

## Claim

Against AgentScope-Java revision `39cd304a7dc400eb3fb2a7daca750162e79bec05`, a stream emits:

```text
Hello
 world
IOException
```

with `maxAttempts=3`. The retry boundary re-subscribes to the upstream stream, so already-delivered chunks are replayed.

## Run

```bash
git clone https://github.com/agentscope-ai/agentscope-java.git
cd agentscope-java
git checkout 39cd304a7dc400eb3fb2a7daca750162e79bec05

curl -L -o /tmp/SableStreamRetryReproTest.java \
  https://raw.githubusercontent.com/socksninja/sable-agent-reliability/main/experiments/agentscope_stream_retry/SableStreamRetryReproTest.java

# Copy the test into the matching test source tree, then run only this test.
# See the source file for the package/import contract used by the pinned revision.
```

Expected observed sequence:

```text
Hello, world, Hello, world, Hello, world
```

## Report one result

Reply on SABLE issue #48 with exactly one of:

- **Reproduced** — include your commit/run URL and observed sequence.
- **Not reproduced** — include the exact revision and observed sequence.
- **Taxonomy correction** — state the better reliability classification.

Do not generalize from this single pinned implementation to other providers or runtimes.

## Existing machine evidence

- SABLE reproduction test: `experiments/agentscope_stream_retry/SableStreamRetryReproTest.java`
- SABLE workflow: `.github/workflows/sable-002-agentscope-stream-retry.yml`
- Independent challenge: https://github.com/socksninja/sable-agent-reliability/issues/48
- Copy-paste issue: https://github.com/socksninja/sable-agent-reliability/issues/49
- Confirmed SABLE run: https://github.com/socksninja/sable-agent-reliability/actions/runs/34762494234
- Upstream issue: https://github.com/agentscope-ai/agentscope-java/issues/2478

The SABLE result is owner-produced evidence. Only an execution by another party changes the evidence state to independent reproduction.
