/*
 * Copyright © 2022-2025 The Oxia Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package io.oxia.testcontainers;

import static io.oxia.testcontainers.OxiaContainer.DEFAULT_IMAGE_NAME;
import static io.oxia.testcontainers.OxiaContainer.OXIA_PORT;
import static org.assertj.core.api.Assertions.assertThat;

import io.oxia.client.api.OxiaClientBuilder;
import io.oxia.client.api.PutResult;
import io.oxia.client.api.SyncOxiaClient;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.Network;
import org.testcontainers.containers.wait.strategy.AbstractWaitStrategy;
import org.testcontainers.containers.wait.strategy.WaitStrategy;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@Testcontainers
class OxiaContainerIT {
    private static final String NETWORK_ALIAS = "oxia";
    private static final Network network = Network.newNetwork();

    @Container
    private static OxiaContainer standalone =
            new OxiaContainer(DEFAULT_IMAGE_NAME).withNetworkAliases(NETWORK_ALIAS).withNetwork(network);

    @Container
    private static OxiaContainer cli =
            new OxiaContainer(DEFAULT_IMAGE_NAME)
                    .withNetwork(network)
                    .withCommand("tail", "-f", "/dev/null")
                    .waitingFor(noopWaitStrategy());

    @Test
    void testPutGetWithCLI() throws Exception {
        var address = NETWORK_ALIAS + ":" + OXIA_PORT;

        var result = cli.execInContainer("oxia", "client", "-a", address, "put", "hello", "world");
        assertThat(result.getExitCode()).isEqualTo(0);

        result = cli.execInContainer("oxia", "client", "-a", address, "get", "hello");
        assertThat(result.getStdout()).contains("world");
    }

    @Test
    void testClientOperations() throws Exception {
        try (SyncOxiaClient client =
                OxiaClientBuilder.create(standalone.getServiceAddress()).syncClient()) {
            // Put two keys
            PutResult put1 = client.put("key-1", "value-1".getBytes(StandardCharsets.UTF_8));
            assertThat(put1).isNotNull();
            assertThat(put1.version().versionId()).isGreaterThanOrEqualTo(0);

            PutResult put2 = client.put("key-2", "value-2".getBytes(StandardCharsets.UTF_8));
            assertThat(put2).isNotNull();

            // Update an existing key
            PutResult put1Updated = client.put("key-1", "value-1-updated".getBytes(StandardCharsets.UTF_8));
            assertThat(put1Updated.version().versionId()).isGreaterThan(put1.version().versionId());

            // Get
            var get1 = client.get("key-1");
            assertThat(get1).isNotNull();
            assertThat(new String(get1.value(), StandardCharsets.UTF_8)).isEqualTo("value-1-updated");

            var get2 = client.get("key-2");
            assertThat(get2).isNotNull();
            assertThat(new String(get2.value(), StandardCharsets.UTF_8)).isEqualTo("value-2");

            // List
            List<String> keys = client.list("key-1", "key-3");
            assertThat(keys).containsExactly("key-1", "key-2");

            // Delete
            boolean deleted = client.delete("key-1");
            assertThat(deleted).isTrue();

            // Get after delete returns null
            var getDeleted = client.get("key-1");
            assertThat(getDeleted).isNull();

            // Delete non-existent key
            boolean deletedAgain = client.delete("key-1");
            assertThat(deletedAgain).isFalse();

            // List after delete
            List<String> keysAfterDelete = client.list("key-1", "key-3");
            assertThat(keysAfterDelete).containsExactly("key-2");
        }
    }

    @Test
    public void testMetricsUrl() throws Exception {
        var httpClient = HttpClient.newHttpClient();
        var request = HttpRequest.newBuilder(URI.create(standalone.getMetricsUrl())).build();
        var response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains("oxia");
    }

    private static WaitStrategy noopWaitStrategy() {
        return new AbstractWaitStrategy() {
            @Override
            protected void waitUntilReady() {}
        };
    }
}
