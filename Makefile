base_dir :=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

tag ?= $(shell whoami)-dev
local_name = elevator-group-control
pwd ?= $(shell pwd)


.PHONY: build
build:
	@echo Building $(local_name):$(tag)
	@docker build -t $(local_name):$(tag) .

run:
	@docker run --rm -it \
		--mount type=bind,source=$(pwd),target=/elevator-group-control \
			$(local_name):$(tag) python main.py
