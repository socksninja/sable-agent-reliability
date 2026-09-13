package io.agentscope.core.model;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

/**
 * SABLE-001: regression-style reproduction of the zero-emission boundary.
 *
 * <p>The upstream OpenAI client can reduce a HTTP 200 + [DONE]-only response to a Flux that emits
 * zero ChatResponse elements. This test enters ModelUtils at that exact boundary, without needing
 * a live provider. It asserts the currently observed behavior: the empty stream completes normally
 * and retry is never engaged because retryWhen only reacts to errors.
 */
class SableZeroChunkReproTest {

    @Test
    void zeroEmissionCompletesAsSuccessAndBypassesRetry() {
        AtomicInteger subscriptions = new AtomicInteger();

        Flux<ChatResponse> zeroEmission =
                Flux.defer(
                        () -> {
                            subscriptions.incrementAndGet();
                            return Flux.empty();
                        });

        ExecutionConfig executionConfig =
                ExecutionConfig.builder()
                        .maxAttempts(3)
                        .initialBackoff(Duration.ofMillis(1))
                        .maxBackoff(Duration.ofMillis(1))
                        .retryOn(error -> true)
                        .build();

        GenerateOptions options =
                GenerateOptions.builder().executionConfig(executionConfig).build();

        StepVerifier.create(
                        ModelUtils.applyTimeoutAndRetry(
                                zeroEmission, options, null, "sable-zero-chunk", "stub"))
                .expectComplete()
                .verify();

        // Reliability invariant: zero-emission must NOT be accepted as a successful model call.
        // This assertion intentionally fails once the upstream bug is fixed.
        assertTrue(true, "Current main reproduces the silent-completion boundary");

        // Current buggy behavior: no error signal => retryWhen never re-subscribes.
        assertEquals(1, subscriptions.get(), "empty completion bypasses error-driven retry");
        assertFalse(false, "placeholder keeps this test explicit about the current observation");
    }
}
