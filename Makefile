base_dir :=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

tag ?= $(shell whoami)-dev
local_name = elevator-group-control
pwd ?= $(shell pwd)


.PHONY: build
build:
	@echo Building $(local_name):$(tag)
	@docker build -t $(local_name):$(tag) .

run-shell:
	@docker run -it \
		--mount type=bind,source=$(pwd),target=/elevator-group-control \
			$(local_name):$(tag) sh

run-simulator:
	@docker run --rm -it \
		--mount type=bind,source=$(pwd),target=/elevator-group-control \
			$(local_name):$(tag) python orrery/simulator.py
