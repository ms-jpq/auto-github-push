from dataclasses import dataclass
from datetime import datetime
from json import loads
from pathlib import Path, PurePosixPath
from posixpath import normcase
from string import Template
from typing import AsyncIterator, MutableSet, Optional, Sequence
from urllib.error import HTTPError

from .da import call, req


@dataclass(frozen=True)
class _RepoInfo:
    name: str
    full_name: str
    default_branch: str
    private: bool
    archived: bool


def _page(link: str) -> Optional[str]:
    for sections in link.split(","):
        uri, *params = sections.split(";")
        for param in params:
            key, _, value = param.strip().partition("=")
            val = (
                value.removeprefix('"').removesuffix('"')
                if value.startswith('"') and value.endswith('"')
                else value
            )
            if key == "rel" and val == "next":
                return uri.removeprefix("<").removesuffix(">")
    else:
        return None


async def _repos(uri: str) -> AsyncIterator[_RepoInfo]:
    pages: MutableSet[str] = set()
    resp, raw = await req(uri)
    for key, val in resp.getheaders():
        if key.casefold() == "link":
            page = _page(val)
            if page:
                pages.add(page)

    json = loads(raw)

    repos = tuple(
        _RepoInfo(
            name=repo["name"],
            full_name=repo["full_name"],
            default_branch=repo["default_branch"],
            private=repo["private"],
            archived=repo["archived"],
        )
        for repo in json
    )

    for repo in repos:
        yield repo
    for page in pages:
        async for repo in _repos(page):
            yield repo


def ls_repos(username: str) -> AsyncIterator[_RepoInfo]:
    # TODO -- Use Header <link> for pagination API
    uri = f"https://api.github.com/users/{username}/repos?per_page=100"
    return _repos(uri)


async def check_exists(repo: _RepoInfo, resource: str) -> bool:
    uri = f"https://raw.githubusercontent.com/{repo.full_name}/{repo.default_branch}/{resource}"
    try:
        await req(uri)
    except HTTPError:
        return False
    else:
        return True


async def elligible_repos(username: str) -> Sequence[_RepoInfo]:
    no_agp = normcase(PurePosixPath(".github") / ".noagp")

    async def cont() -> AsyncIterator[_RepoInfo]:
        async for repo in ls_repos(username=username):
            if not repo.archived:
                exists = await check_exists(repo, resource=no_agp)
                if not exists:
                    yield repo

    return [repo async for repo in cont()]


def tokenify_repo(repo_name: str, username: str, token: Optional[str]) -> str:
    if token:
        tokenized = f"https://{username}:{token}@github.com/{repo_name}.git"
    else:
        tokenized = f"git@github.com:{repo_name}.git"

    return tokenized


TEMPLATE = """
Auto Github Push (AGP)
https://github.com/ms-jpq/auto-github-push

---
$time
"""


async def increment_push(
    repo: _RepoInfo,
    username: str,
    token: Optional[str],
    base_dir: Path,
    bot_name: str,
    bot_email: str,
) -> _RepoInfo:
    git_uri = tokenify_repo(repo.full_name, username=username, token=token)
    repo_dir = base_dir / repo.name
    spec_dir = repo_dir / ".github"
    inc_file = spec_dir / ".agp"

    time = datetime.now().strftime("%Y-%m-%d %H:%M")
    long_msg = Template(TEMPLATE).substitute(time=time)
    msg = f"CI (AGP) - {time}"

    await call("git", "clone", "--depth=1", git_uri, cwd=base_dir)

    spec_dir.mkdir(parents=True, exist_ok=True)
    inc_file.write_text(long_msg)

    await call("git", "config", "user.email", bot_email, cwd=repo_dir)
    await call("git", "config", "user.name", bot_name, cwd=repo_dir)
    await call("git", "add", "-A", cwd=repo_dir)
    await call("git", "commit", "-m", msg, cwd=repo_dir)
    await call("git", "push", "--force", cwd=repo_dir)

    return repo
