from argparse import ArgumentParser, Namespace
from asyncio import as_completed, run
from os import environ
from pathlib import Path
from shutil import rmtree

from agp.github import elligible_repos, increment_push

_BOT_NAME = "agp-bot"
_BOT_EMAIL = "agp@github.com"
_TEMP_DIR = Path(__file__).resolve(strict=True).parent.parent / "temp"


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    if username := environ.get("GITHUB_ACTOR"):
        parser.add_argument("--username", default=username)
    else:
        parser.add_argument("--username", required=True)

    parser.add_argument("--token", default=environ.get("GITHUB_TOKEN"))
    return parser.parse_args()


async def main() -> None:
    args = _parse_args()
    username = args.username

    print(f"-- AGP for {username} --")

    rmtree(_TEMP_DIR, ignore_errors=True)
    _TEMP_DIR.mkdir(parents=True, exist_ok=True)

    repos = await elligible_repos(username=username)
    tasks = (
        increment_push(
            repo=repo,
            username=username,
            token=args.token,
            base_dir=_TEMP_DIR,
            bot_name=_BOT_NAME,
            bot_email=_BOT_EMAIL,
        )
        for repo in repos
    )

    for coro in as_completed(tuple(tasks)):
        repo = await coro
        print(f"Done -- {repo.name}")


run(main())
