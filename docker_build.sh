#!/bin/bash

docker build -t starwitorg/sae-position-source:$(git rev-parse --short HEAD) .