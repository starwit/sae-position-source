# SAE Position Source
This component provides geographical location for an SAE instance. It sends either a statically configured position, or reads from an USB GPS device.

## Prerequisites
- python 3.11, you can switch between python versions with pyenv:
  - see https://github.com/pyenv/pyenv/wiki#suggested-build-environment
  - `curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash`
  - choose environment with `pyenv local 3.11.9`
- Virtual env (e.g. sudo apt install python3.11-venv)
- Install Poetry
    ```
    sudo apt install pipx
    pipx install poetry==2.1.3
    ```
- Install Docker with compose plugin
- Running instance of starwit-awareness-engine, anomaly detection and Valkey

## Setup
- Create virtual environment with `python3 -m venv .venv && source .venv/bin/activate`
- Run `poetry install`, this should install all necessary dependencies
- Run `poetry run python main.py`. If you see log messages like `Received anomaly message from pipeline`, everything works as intended.

## Configuration
This code employs pydantic-settings for configuration handling. On startup, the following happens:
1. Load defaults (see `config.py`)
2. Read settings `settings.yaml` if it exists
3. Search through environment variables if any match configuration parameters (converted to upper_snake_case, nested levels delimited by `__`), overwriting the corresponding setting
4. Validate settings hierarchy if all necessary values are filled, otherwise Pydantic will throw a hopefully helpful error

The `settings.template.yaml` should always reflect a correct and fully fledged settings structure to use as a starting point for users.

## Test GPS command reader
- Use `["bash", "-c", "while IFS= read -r line; do echo \"$line\" | cut -d';' -f2-; sleep 0.1; done < test.log"]` as a command in your `settings.yaml` to feed a log file (with timestamps; remove the cut command if your log file contains just NMEA sentences) in 100ms intervals to the position source

## Github Workflows and Versioning

The following Github Actions are available:

* [PR build](.github/workflows/pr-build.yml): Builds python project for each pull request to main branch. `poetry install` and `poetry run pytest` are executed, to compile and test python code.
* [Build and publish latest image](.github/workflows/build-publish-latest.yml): Manually executed action. Same like PR build. Additionally puts latest docker image to internal docker registry.
* [Create release](.github/workflows/create-release.yml): Manually executed action. Creates a github release with tag, docker image in internal docker registry, helm chart in chartmuseum by using and incrementing the version in pyproject.toml. Poetry is updating to next version by using "patch, minor and major" keywords. If you want to change to non-incremental version, set version in directly in pyproject.toml and execute create release afterwards.

## Dependabot Version Update

With [dependabot.yml](.github/dependabot.yml) a scheduled version update via Dependabot is configured. Dependabot creates a pull request if newer versions are available and the compilation is checked via PR build.