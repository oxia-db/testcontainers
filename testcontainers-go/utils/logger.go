package utils

import (
	"fmt"
	"log/slog"

	"github.com/testcontainers/testcontainers-go/log"
)

var _ log.Logger = &logger{}

type logger struct {
}

func NewDefaultLogger() log.Logger {
	return &logger{}
}

func (l *logger) Printf(format string, v ...any) {
	slog.Info(fmt.Sprintf(format, v))
}
