from asyncio import create_subprocess_exec, to_thread
from asyncio.subprocess import DEVNULL, PIPE
from dataclasses import dataclass
from http.client import HTTPResponse
from os import environ
from pathlib import Path, PurePath
from typing import Any, Dict, Optional, Union, cast
from urllib.request import Request, build_opener


@dataclass(frozen=True)
class ProcReturn:
    code: int
    out: str
    err: str


async def call(
    prog: str,
    *args: str,
    env: Dict[str, str] = {},
    cwd: PurePath = Path.cwd(),
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

    msg = await to_thread(_req)
    return msg
