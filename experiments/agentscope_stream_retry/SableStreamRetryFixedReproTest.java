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
 * SABLE-002 upstream-fix check: once a streaming response has been emitted,
 * a retryable transport error must not replay the already-delivered chunks.
 *
 * This test is intentionally separate from the historical reproducer so the
 * expected post-fix behavior is explicit rather than inferred from a failing
 * regression test.
 */
class SableStreamRetryFixedReproTest {

  @Test
  void postEmissionFailureDoesNotReplayDeliveredChunks() {
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

    ModelUtils.applyTimeoutAndRetry(upstream, options, options, "sable-fix-test", "sable")
        .map(this::textOf)
        .onErrorResume(e -> Flux.empty())
        .doOnNext(delivered::add)
        .collectList()
        .block();

    assertEquals(1, subscriptions.get(), "post-emission failure must not resubscribe");
    assertIterableEquals(List.of("Hello", " world"), delivered);
  }

  private static ChatResponse chunk(String text) {
    return ChatResponse.builder().content(List.of(TextBlock.builder().text(text).build())).build();
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
