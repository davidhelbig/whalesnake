import argparse
import gzip
import logging
import os
from enum import Enum
from typing import Iterable

import docker
import yaml
from pydantic import BaseModel, NewPath

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DockerCommand(str, Enum):
    start = "start"
    stop = "stop"


class PostgresSettings(BaseModel):
    container_name: str
    postgres_user: str
    output_archive: NewPath


class ContainerCommandSettings(BaseModel):
    container_name: str
    command: DockerCommand


class Recipe(BaseModel):
    recipe: list[ContainerCommandSettings | PostgresSettings]


def load_recipe_from_yaml(path: os.PathLike) -> PostgresSettings:
    with open(path, "r") as f:
        return Recipe(**yaml.safe_load(f))


def execute_container_command(
    docker_client: docker.DockerClient, settings: ContainerCommandSettings
):
    container = docker_client.containers.get(settings.container_name)

    match settings.command:
        case DockerCommand.start:
            container.start()
            logger.info(f"Started container {container.name}")
        case DockerCommand.stop:
            container.stop()
            logger.info(f"Stopped container {container.name}")


def get_output_stream_for_exec(
    docker_client: docker.DockerClient, container_name: str, cmd: list[str]
) -> Iterable[tuple[str, str]]:
    container = docker_client.containers.get(container_name)

    _, output_stream = container.exec_run(cmd=cmd, stream=True, demux=True)

    return output_stream


def backup_postgres(docker_client: docker.DockerClient, settings: PostgresSettings):
    cmd = ["pg_dumpall", "-c", "-U", settings.postgres_user]

    with gzip.GzipFile(settings.output_archive, "w") as f:
        bytes_written = 0
        for stdout_chunk, stderr_chunk in get_output_stream_for_exec(
            docker_client, settings.container_name, cmd
        ):
            bytes_written += f.write(stdout_chunk)
        logger.info(f"Wrote {bytes_written} bytes to {settings.output_archive}")


def execute_recipe(docker_client: docker.DockerClient, recipe: Recipe):
    for setting in recipe.recipe:
        match setting.__class__.__name__:
            case PostgresSettings.__name__:
                backup_postgres(docker_client, setting)
            case ContainerCommandSettings.__name__:
                execute_container_command(docker_client, setting)
            case _:
                raise RuntimeError("Invalid setting type detected!")


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("settings", help="The recipe file to load from.")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    client = docker.from_env()
    recipe = load_recipe_from_yaml(args.settings)
    execute_recipe(client, recipe)
