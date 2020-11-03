from asyncio import create_subprocess_exec, get_running_loop
from asyncio.subprocess import DEVNULL, PIPE
from dataclasses import dataclass
from functools import partial
from http.client import HTTPResponse
from os import environ, getcwd
from typing import Any, Callable, Dict, Optional, TypeVar, Union, cast
from urllib.request import HTTPRedirectHandler, Request, build_opener

T = TypeVar("T")


async def run_in_executor(f: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    loop = get_running_loop()
    cont = partial(f, *args, **kwargs)
    return await loop.run_in_executor(None, cont)


@dataclass(frozen=True)
class ProcReturn:
    code: int
    out: str
    err: str


async def call(
    prog: str,
    *args: str,
    env: Dict[str, str] = {},
    cwd: str = getcwd(),
    expect: Optional[int] = None
) -> ProcReturn:
    envi = {**environ, **env}
    proc = await create_subprocess_exec(
        prog, *args, stdin=DEVNULL, stdout=PIPE, stderr=PIPE, env=envi, cwd=cwd
    )
    stdout, stderr = await proc.communicate()
    code = cast(int, proc.returncode)
    out, err = stdout.decode(), stderr.decode()

    if expect is not None and code != expect:
        raise RuntimeError(err)
    else:
        return ProcReturn(code=code, out=out, err=err)


async def req(req: Union[Request, str]) -> Any:
    def _req() -> Any:
        opener = build_opener()
        with opener.open(req) as resp:
            resp = cast(HTTPResponse, resp)
            return resp.read()

    msg = await run_in_executor(_req)
    return msg
