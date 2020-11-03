#!/usr/bin/env python

from asyncio import gather, run
from os import environ, makedirs
from os.path import dirname, join, realpath
from shutil import rmtree

from agp.da import call
from agp.github import elligible_repos, increment_push

TEMP_DIR = join(dirname(realpath(__file__)), "temp")

bot_name = "agp-bot"
bot_email = "agp@github.com"


async def main() -> None:
    username = "ms-jpq"
    token = environ["TOKEN"]

    rmtree(TEMP_DIR, ignore_errors=True)
    makedirs(TEMP_DIR, exist_ok=True)

    repos = await elligible_repos(username=username)
    tasks = (
        increment_push(
            full_name=repo.full_name,
            repo_name=repo.name,
            username=username,
            token=token,
            base_dir=TEMP_DIR,
            bot_name=bot_name,
            bot_email=bot_email,
        )
        for repo in repos
    )
    await gather(*tasks)


run(main())
