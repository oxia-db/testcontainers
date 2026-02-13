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

import urllib.request

import oxia
import pytest

from oxia_testcontainer import OxiaContainer


def test_service_address():
    with OxiaContainer() as container:
        address = container.get_service_address()
        host, port = address.rsplit(":", 1)
        assert host
        assert port.isdigit()


def test_put_get_with_cli():
    with OxiaContainer(log_level="debug") as container:
        exit_code, output = container.exec(
            ["oxia", "client", "put", "hello", "world"]
        )
        assert exit_code == 0

        exit_code, output = container.exec(
            ["oxia", "client", "get", "hello"]
        )
        assert exit_code == 0
        assert b"world" in output


def test_metrics_endpoint():
    with OxiaContainer() as container:
        url = container.get_metrics_url()
        with urllib.request.urlopen(url) as response:
            assert response.status == 200
            body = response.read().decode()
            assert "oxia" in body


def test_custom_shards():
    with OxiaContainer(shards=2) as container:
        address = container.get_service_address()
        host, port = address.rsplit(":", 1)
        assert host
        assert port.isdigit()


def test_invalid_shards_raises():
    with pytest.raises(ValueError, match="shards must be greater than zero"):
        OxiaContainer(shards=0)


def test_client_put_and_get():
    with OxiaContainer() as container:
        client = oxia.Client(container.get_service_address())
        try:
            key, version = client.put("/test/key1", "value1")
            assert key == "/test/key1"
            assert version.version_id() >= 0

            key, value, version = client.get("/test/key1")
            assert key == "/test/key1"
            assert value == b"value1"
        finally:
            client.close()


def test_client_put_conditional():
    with OxiaContainer() as container:
        client = oxia.Client(container.get_service_address())
        try:
            _, version1 = client.put(
                "/test/conditional",
                "v1",
                expected_version_id=oxia.EXPECTED_RECORD_DOES_NOT_EXIST,
            )

            _, version2 = client.put(
                "/test/conditional",
                "v2",
                expected_version_id=version1.version_id(),
            )
            assert version2.version_id() != version1.version_id()

            _, value, _ = client.get("/test/conditional")
            assert value == b"v2"
        finally:
            client.close()


def test_client_list():
    with OxiaContainer() as container:
        client = oxia.Client(container.get_service_address())
        try:
            client.put("/list/a", "1")
            client.put("/list/b", "2")
            client.put("/list/c", "3")
            client.put("/other/x", "4")

            keys = client.list("/list/", "/list/~")
            assert sorted(keys) == ["/list/a", "/list/b", "/list/c"]
        finally:
            client.close()


def test_client_delete():
    with OxiaContainer() as container:
        client = oxia.Client(container.get_service_address())
        try:
            client.put("/test/delete-me", "gone")
            deleted = client.delete("/test/delete-me")
            assert deleted is True

            with pytest.raises(oxia.ex.KeyNotFound):
                client.get("/test/delete-me")
        finally:
            client.close()


def test_client_delete_range():
    with OxiaContainer() as container:
        client = oxia.Client(container.get_service_address())
        try:
            client.put("/range/a", "1")
            client.put("/range/b", "2")
            client.put("/range/c", "3")

            client.delete_range("/range/a", "/range/c")

            keys = client.list("/range/", "/range/~")
            assert keys == ["/range/c"]
        finally:
            client.close()


def test_client_range_scan():
    with OxiaContainer() as container:
        client = oxia.Client(container.get_service_address())
        try:
            client.put("/scan/a", "alpha")
            client.put("/scan/b", "beta")
            client.put("/scan/c", "gamma")

            results = list(client.range_scan("/scan/", "/scan/~"))
            assert len(results) == 3

            keys = [r[0] for r in results]
            values = [r[1] for r in results]
            assert sorted(keys) == ["/scan/a", "/scan/b", "/scan/c"]
            assert b"alpha" in values
            assert b"beta" in values
            assert b"gamma" in values
        finally:
            client.close()


def test_client_get_nonexistent_key():
    with OxiaContainer() as container:
        client = oxia.Client(container.get_service_address())
        try:
            with pytest.raises(oxia.ex.KeyNotFound):
                client.get("/does/not/exist")
        finally:
            client.close()


def test_client_version_metadata():
    with OxiaContainer() as container:
        client = oxia.Client(container.get_service_address())
        try:
            _, version = client.put("/test/version-meta", "data")
            assert version.version_id() >= 0
            assert version.modifications_count() == 0
            assert version.created_timestamp() is not None
            assert version.modified_timestamp() is not None

            _, version2 = client.put("/test/version-meta", "data2")
            assert version2.modifications_count() == 1
        finally:
            client.close()
