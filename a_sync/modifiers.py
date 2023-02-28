
import asyncio
from concurrent.futures._base import Executor
from typing import TypedDict, Union

class Modifiers(TypedDict, total=False):
    runs_per_minute: int
    executor: Executor
    semaphore: Union[int, asyncio.Semaphore]

valid_modifiers = [key for key in Modifiers.__annotations__ if not key.startswith('_') and not key.endswith('_')]

def read_modifiers(cls: Union[type, object]) -> Modifiers:
    return Modifiers({modifier: getattr(cls, modifier) for modifier in valid_modifiers if hasattr(cls, modifier)})