package io.agentscope.core.model;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertIterableEquals;

import io.agentscope.core.message.TextBlock;
import java.io.IOException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Flux;

/**
 * SABLE-002: dynamic reproduction of mid-stream retry replaying already-emitted chunks.
 *
 * Upstream emits two chunks, then a retryable IOException. ModelUtils.retryWhen re-subscribes
 * the whole Flux, so already delivered chunks are repeated.
 */
class SableStreamRetryReproTest {

    @Test
    void midStreamRetryDuplicatesAlreadyEmittedChunks() {
        AtomicInteger subscriptions = new AtomicInteger();
        List<String> delivered = new ArrayList<>();

        Flux<ChatResponse> upstream =
                Flux.defer(
                        () -> {
                            subscriptions.incrementAndGet();
                            return Flux.concat(
                                    Flux.just(chunk("Hello"), chunk(" world")),
                                    Flux.error(new IOException("connection reset by peer")));
                        });

        GenerateOptions options =
                GenerateOptions.builder()
                        .executionConfig(
                                ExecutionConfig.builder()
                                        .maxAttempts(3)
                                        .initialBackoff(Duration.ZERO)
                                        .maxBackoff(Duration.ZERO)
                                        .retryOn(ExecutionConfig.RETRYABLE_ERRORS)
                                        .build())
                        .build();

        ModelUtils.applyTimeoutAndRetry(upstream, options, options, "sable-test", "sable")
                .map(this::textOf)
                .onErrorResume(e -> Flux.empty())
                .doOnNext(delivered::add)
                .collectList()
                .block();

        assertEquals(3, subscriptions.get(), "maxAttempts=3 should resubscribe twice");
        assertIterableEquals(
                List.of("Hello", " world", "Hello", " world", "Hello", " world"), delivered);
    }

    private static ChatResponse chunk(String text) {
        return ChatResponse.builder()
                .content(List.of(TextBlock.builder().text(text).build()))
                .build();
    }

    private String textOf(ChatResponse response) {
        return response.getContent().stream()
                .filter(TextBlock.class::isInstance)
                .map(TextBlock.class::cast)
                .map(TextBlock::getText)
                .findFirst()
                .orElse("");
    }
}
