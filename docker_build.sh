#!/bin/bash

docker build -t starwitorg/sae-sae-position-source:$(git rev-parse --short HEAD) .