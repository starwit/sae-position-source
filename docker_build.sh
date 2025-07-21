#!/bin/bash

docker build -t starwitorg/sae-sae-position-source:$(poetry version --short) .