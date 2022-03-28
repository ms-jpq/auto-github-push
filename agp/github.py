from dataclasses import dataclass
from datetime import datetime
from json import loads
from pathlib import Path, PurePosixPath
from posixpath import normcase
from string import Template
from typing import AsyncIterator, Optional, Sequence
from urllib.error import HTTPError

from .da import call, req


@dataclass(frozen=True)
class RepoInfo:
    name: str
    full_name: str
    default_branch: str
    private: bool


async def ls_repos(username: str) -> Sequence[RepoInfo]:
    # TODO -- Use Header <link> for pagination API
    uri = f"https://api.github.com/users/{username}/repos?per_page=100"
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
        return False
    else:
        return True


async def elligible_repos(username: str) -> Sequence[RepoInfo]:
    no_agp = normcase(PurePosixPath(".github") / ".noagp")
    repos = await ls_repos(username=username)

    async def cont() -> AsyncIterator[RepoInfo]:
        for repo in repos:
            exists = await check_exists(repo, resource=no_agp)
            if not exists:
                yield repo

    return [repo async for repo in cont()]


def tokenify_repo(repo_name: str, username: str, token: Optional[str]) -> str:
    tok = f":{token}" if token else ""
    tokenized = f"https://{username}{tok}@github.com/{repo_name}.git"
    return tokenized


TEMPLATE = """
Auto Github Push (AGP)
https://github.com/ms-jpq/auto-github-push

---
$time
"""


async def increment_push(
    repo: RepoInfo,
    username: str,
    token: Optional[str],
    base_dir: Path,
    bot_name: str,
    bot_email: str,
) -> RepoInfo:
    git_uri = tokenify_repo(repo.full_name, username=username, token=token)
    repo_dir = base_dir / repo.name
    spec_dir = repo_dir / ".github"
    inc_file = spec_dir / ".agp"

    time = datetime.now().strftime("%Y-%m-%d %H:%M")
    long_msg = Template(TEMPLATE).substitute(time=time)
    msg = f"CI (AGP) - {time}"

    await call("git", "clone", "--depth=1", git_uri, cwd=base_dir, expect=0)

    spec_dir.mkdir(parents=True, exist_ok=True)
    inc_file.write_text(long_msg)

    await call("git", "config", "user.email", bot_email, cwd=repo_dir, expect=0)
    await call("git", "config", "user.name", bot_name, cwd=repo_dir, expect=0)
    await call("git", "add", "-A", cwd=repo_dir, expect=0)
    await call("git", "commit", "-m", msg, cwd=repo_dir, expect=0)
    await call("git", "push", "--force", cwd=repo_dir, expect=0)

    return repo
