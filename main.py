#!/usr/bin/env python

from asyncio import as_completed, run
from os import environ, makedirs
from os.path import dirname, join, realpath
from shutil import rmtree
from sys import stderr

from agp.da import call
from agp.github import elligible_repos, increment_push

TEMP_DIR = join(dirname(realpath(__file__)), "temp")

bot_name = "agp-bot"
bot_email = "agp@github.com"


async def main() -> None:
    username = environ["GITHUB_ACTOR"]
    token = environ["GITHUB_TOKEN"]
    print(f"-- AGP for {username} --")

    rmtree(TEMP_DIR, ignore_errors=True)
    makedirs(TEMP_DIR, exist_ok=True)

    repos = await elligible_repos(username=username)
    tasks = (
        increment_push(
            repo=repo,
            username=username,
            token=token,
            base_dir=TEMP_DIR,
            bot_name=bot_name,
            bot_email=bot_email,
        )
        for repo in repos
    )

    for coro in as_completed(tuple(tasks)):
        repo = await coro
        print(f"Done -- {repo.name}")


run(main())
