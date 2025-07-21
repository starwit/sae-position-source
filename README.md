# SAE stage template
A starter for a SAE stage implementation.\
\
This repository will help you implementing a SAE pipeline stage by putting all the necessary infrastructure in place.

# How-to start

## Create repository from template
Create your own repository using this template. It is good practice to prefix the repo name with `sae-` and use a concise name that describes what the stage does.\
**Careful:** Check the repository owner, it defaults to your main user account.

## Check prerequisites
In order to work with this repository, you need to ensure the following steps:
- Install Poetry
- Install Docker with compose plugin
- Clone main SAE repository (you will most likely need a running SAE to do anything useful): https://github.com/starwit/starwit-awareness-engine

## Replace template name
To make this repository entirely belong to your new shiny stage, you have to replace various forms of `mystage` in a few places. 
Run `set_name.sh` and enter the various forms of your new name when prompted. The script will set everything up for you and then delete itself.
If you made a mistake either reclone the repository or run `git reset --hard && git clean -fd`

## Setup
- Run `poetry install`, this should install all necessary dependencies
- Start docker compose version of the SAE (see here: https://github.com/starwit/starwit-awareness-engine/blob/main/docker-compose/README.md)
- Run `poetry run python main.py`. If you see log messages like `Received SAE message from pipeline`, everything works as intended.

## Start hacking :)

# Helpful implementation hints

## Configuration
This template employs pydantic-settings for configuration handling. On startup, the following happens:
1. Load defaults (see `config.py`)
2. Read settings `settings.yaml` if it exists
3. Search through environment variables if any match configuration parameters (converted to upper_snake_case, nested levels delimited by `__`), overwriting the corresponding setting
4. Validate settings hierarchy if all necessary values are filled, otherwise Pydantic will throw a hopefully helpful error

The `settings.template.yaml` should always reflect a correct and fully fledged settings structure to use as a starting point for users. 
