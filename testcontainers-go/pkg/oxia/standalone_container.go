package oxia

import (
	"context"
	"fmt"

	"github.com/oxia-db/testcontainers/testcontainers-go/utils"
	"github.com/pkg/errors"
	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/wait"
)

const (
	externalPort = "6648/tcp"
	internalPort = "6649/tcp"
)

type standaloneOptions struct {
	image    string
	logLevel string
}

func (s *standaloneOptions) WithDefault() {
	s.image = "oxia/oxia:latest"
	s.logLevel = "info"
}

type StandaloneOption func(*standaloneOptions) error

var _ testcontainers.ContainerCustomizer = (StandaloneOption)(nil)

func (s StandaloneOption) Customize(*testcontainers.GenericContainerRequest) error { return nil }

func WithImage(image string) StandaloneOption {
	return func(options *standaloneOptions) error {
		options.image = image
		return nil
	}
}

func WithLogLevel(logLevel string) StandaloneOption {
	return func(options *standaloneOptions) error {
		options.logLevel = logLevel
		return nil
	}
}

type StandaloneContainer struct {
	testcontainers.Container
}

func (s *StandaloneContainer) PublicAddress() string {
	host, err := s.Host(context.Background())
	if err != nil {
		panic(err)
	}
	port, err := s.MappedPort(context.Background(), "6648")
	if err != nil {
		panic(err)
	}
	return fmt.Sprintf(`%s:%s`, host, port)
}

func Run(ctx context.Context, opts ...testcontainers.ContainerCustomizer) (*StandaloneContainer, error) {
	// apply options
	var options standaloneOptions
	options.WithDefault()

	for _, opt := range opts {
		if opt, ok := opt.(StandaloneOption); ok {
			if err := opt(&options); err != nil {
				return nil, err
			}
		}
	}

	containerReq := testcontainers.GenericContainerRequest{
		ContainerRequest: testcontainers.ContainerRequest{
			Image:        options.image,
			ExposedPorts: []string{externalPort, internalPort},
			Cmd:          []string{"bin/oxia", "standalone", "--log-level", options.logLevel},
			WaitingFor:   wait.ForLog("Started Grpc server"),
		},
		Started: true,
		Logger:  utils.NewDefaultLogger(),
	}

	for _, opt := range opts {
		if err := opt.Customize(&containerReq); err != nil {
			return nil, err
		}
	}

	container, err := testcontainers.GenericContainer(ctx, containerReq)
	if err != nil {
		return nil, errors.Wrap(err, "failed to generic container")
	}

	return &StandaloneContainer{
		Container: container,
	}, nil
}
