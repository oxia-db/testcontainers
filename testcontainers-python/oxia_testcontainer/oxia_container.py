# Copyright 2022-2025 The Oxia Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

OXIA_PORT = 6648
INTERNAL_PORT = 6649
METRICS_PORT = 8080


class OxiaContainer(DockerContainer):
    """Testcontainer for running Oxia standalone."""

    def __init__(
        self,
        image: str = "oxia/oxia:latest",
        log_level: str = "info",
        shards: int = 1,
    ):
        if shards <= 0:
            raise ValueError("shards must be greater than zero")
        super().__init__(image)
        self.with_exposed_ports(OXIA_PORT, INTERNAL_PORT, METRICS_PORT)
        self.with_command(
            f"oxia standalone --log-level {log_level} --shards={shards}"
        )

    def start(self) -> "OxiaContainer":
        super().start()
        wait_for_logs(self, "Started Grpc server")
        return self

    def get_service_address(self) -> str:
        host = self.get_container_host_ip()
        port = self.get_exposed_port(OXIA_PORT)
        return f"{host}:{port}"

    def get_internal_address(self) -> str:
        host = self.get_container_host_ip()
        port = self.get_exposed_port(INTERNAL_PORT)
        return f"{host}:{port}"

    def get_metrics_url(self) -> str:
        host = self.get_container_host_ip()
        port = self.get_exposed_port(METRICS_PORT)
        return f"http://{host}:{port}/metrics"
