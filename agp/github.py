from dataclasses import dataclass
from datetime import datetime
from json import loads
from os import makedirs
from os.path import join
from typing import AsyncIterator, Sequence
from urllib.error import HTTPError

from .da import call, req


@dataclass(frozen=True)
class RepoInfo:
    name: str
    full_name: str
    default_branch: str
    private: bool


async def ls_repos(username: str) -> Sequence[RepoInfo]:
    uri = f"https://api.github.com/users/{username}/repos"
    data = await req(uri)
    repos = loads(data)
    names = tuple(
        RepoInfo(
            name=repo["name"],
            full_name=repo["full_name"],
            default_branch=repo["default_branch"],
            private=repo["private"],
        )
        for repo in repos
    )
    return names


async def check_exists(repo: RepoInfo, resource: str) -> bool:
    uri = f"https://raw.githubusercontent.com/{repo.full_name}/{repo.default_branch}/{resource}"
    try:
        await req(uri)
    except HTTPError:
        return True
    else:
        return False


async def elligible_repos(username: str) -> Sequence[RepoInfo]:
    NO_AGP = join(".github", ".noagp")
    repos = await ls_repos(username=username)

    async def cont() -> AsyncIterator:
        for repo in repos:
            exists = await check_exists(repo, resource=NO_AGP)
            if exists:
                yield repo

    return [repo async for repo in cont()]


def tokenify_repo(repo_name: str, username: str, token: str) -> str:
    tokenized = f"https://{username}:{token}@github.com/{repo_name}.git"
    return tokenized


def inc_ver(dest: str, msg: str) -> None:
    with open(dest, "w") as fd:
        fd.write(msg)


async def increment_push(
    full_name: str,
    repo_name: str,
    username: str,
    token: str,
    base_dir: str,
    bot_name: str,
    bot_email: str,
) -> None:
    git_uri = tokenify_repo(full_name, username=username, token=token)
    repo_dir = join(base_dir, repo_name)
    spec_dir = join(repo_dir, ".github")
    inc_file = join(spec_dir, ".agp")

    time = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"CI (AGP) - {time}"

    await call("git", "clone", "--depth=1", git_uri, cwd=base_dir, expect=0)

    makedirs(spec_dir, exist_ok=True)
    inc_ver(inc_file, msg=msg)

    await call("git", "config", "user.email", bot_email, cwd=repo_dir, expect=0)
    await call("git", "config", "user.name", bot_name, cwd=repo_dir, expect=0)
    await call("git", "add", "-A", cwd=repo_dir, expect=0)
    await call("git", "commit", "-m", msg, cwd=repo_dir, expect=0)
    await call("git", "push", "--force", cwd=repo_dir, expect=0)
    print(f"Done -- {repo_name}")
