# Whalesnake

This is a POC for a library/CLI that supports backing up docker containers with "recipes" in YAML format.

I have not found a backup solution for Docker containers that works for me, so I want to come up with my own.

## Requirements

- Minimum Python version: 3.10
- Docker (Compose plugin recommended)

## Usage


Create a virutal environment, install dependencies:

```sh
python3 -m venv venv
source venv/bin/activa
pip install -r requirements.txt
```

Run the included example `Gitea` project:

```sh
docker compose -f recipes/gitea/docker-compose.yml up -d
```

Now run the included recipe to backup the included database into a gzipped SQL dump:

```sh
python3 backup.py recipes/gitea/gitea.yml
```

Inspect the resulting dump:

```sh
zless gitea_postgres_archive.gz
```
