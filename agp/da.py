from asyncio import create_subprocess_exec, to_thread
from asyncio.subprocess import DEVNULL, PIPE
from http.client import HTTPResponse
from os import environ
from pathlib import Path, PurePath
from subprocess import CompletedProcess
from typing import Any, Mapping, Tuple, Union, cast
from urllib.request import Request, build_opener

_OPENER = build_opener()


async def call(
    prog: str,
    *args: str,
    env: Mapping[str, str] = {},
    cwd: PurePath = Path.cwd(),
) -> CompletedProcess[str]:
    envi = {**environ, **env}
    proc = await create_subprocess_exec(
        prog, *args, stdin=DEVNULL, stdout=PIPE, stderr=PIPE, env=envi, cwd=cwd
    )
    stdout, stderr = await proc.communicate()
    code = cast(int, proc.returncode)
    out, err = stdout.decode(), stderr.decode()

    p = CompletedProcess(
        args=(prog, *args),
        returncode=code,
        stdout=out,
        stderr=err,
    )
    p.check_returncode()
    return p


async def req(req: Union[Request, str]) -> Tuple[HTTPResponse, Any]:
    def _req() -> Tuple[HTTPResponse, Any]:
        with _OPENER.open(req) as resp:
            resp = cast(HTTPResponse, resp)
            return resp, resp.read()

    msg = await to_thread(_req)
    return msg
