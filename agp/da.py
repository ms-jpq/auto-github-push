from asyncio import create_subprocess_exec
from asyncio.subprocess import DEVNULL, PIPE
from dataclasses import dataclass
from os import environ, getcwd
from typing import Dict, cast


@dataclass(frozen=True)
class ProcReturn:
    code: int
    out: str
    err: str


async def call(
    prog: str, *args: str, env: Dict[str, str] = {}, cwd: str = getcwd()
) -> ProcReturn:
    envi = {**environ, **env}
    proc = await create_subprocess_exec(
        prog, *args, stdin=DEVNULL, stdout=PIPE, stderr=PIPE, env=envi, cwd=cwd
    )
    stdout, stderr = await proc.communicate()
    code = cast(int, proc.returncode)
    return ProcReturn(code=code, out=stdout.decode(), err=stderr.decode())
