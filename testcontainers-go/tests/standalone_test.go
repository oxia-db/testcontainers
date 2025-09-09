package tests

import (
	"io"
	"testing"

	"github.com/oxia-io/testcontainers/pkg/oxia"
	"github.com/stretchr/testify/assert"
)

func TestStandalone(t *testing.T) {
	container, err := oxia.Run(t.Context(), oxia.WithImage("oxia/oxia:latest"), oxia.WithLogLevel("debug"))
	assert.NoError(t, err)
	exitCode, reader, err := container.Exec(t.Context(), []string{"bin/oxia", "client", "put", "key", "value-data"})
	assert.Equal(t, exitCode, 0)
	assert.NoError(t, err)
	output, err := io.ReadAll(reader)
	assert.NoError(t, err)
	assert.Contains(t, string(output), "created_timestamp")
	exitCode, reader, err = container.Exec(t.Context(), []string{"bin/oxia", "client", "get", "key"})
	assert.NoError(t, err)
	assert.Equal(t, exitCode, 0)
	output, err = io.ReadAll(reader)
	assert.NoError(t, err)
	assert.Contains(t, string(output), "value-data")
}
