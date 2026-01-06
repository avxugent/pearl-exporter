# Needs to be defined before including Makefile.common to auto-generate targets
DOCKER_ARCHS ?= amd64
DOCKER_REPO             ?= kristofkeppens

include Makefile.common

DOCKER_IMAGE_NAME       ?= pearl-exporter
