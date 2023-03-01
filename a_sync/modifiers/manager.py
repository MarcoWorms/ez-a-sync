
import functools
from typing import Any, Awaitable, Callable

from a_sync import cache, rate_limiting, semaphores
from a_sync._typing import *

valid_modifiers = [key for key in ModifierKwargs.__annotations__ if not key.startswith('_') and not key.endswith('_')]


def get_modifiers_from(thing: Union[dict, type, object]) -> ModifierKwargs:
    if isinstance(thing, dict):
        return ModifierKwargs({modifier: thing[modifier] for modifier in valid_modifiers if modifier in thing})
    return ModifierKwargs({modifier: getattr(thing, modifier) for modifier in valid_modifiers if hasattr(thing, modifier)})

class ModifierManager:
    def __init__(self, modifiers: ModifierKwargs = None) -> None:
        if modifiers:
            for key in modifiers.keys():
                if key not in valid_modifiers:
                    raise ValueError(f"'{key}' is not a supported modifier.")
            self._modifiers = modifiers
        else:
            self._modifiers = ModifierKwargs()
    def __repr__(self) -> str:
        return str(self._modifiers)
    def __getitem__(self, modifier_key: str):
        return self._modifiers[modifier_key]
    def __getattribute__(self, modifier_key: str) -> Any:
        if modifier_key == '__dict__' or modifier_key not in valid_modifiers:
            return super().__getattribute__(modifier_key)
        try:
            return self[modifier_key]
        except:
            from a_sync import config
            return config.default_modifiers[modifier_key]
    
    @property
    def use_limiter(self) -> bool:
        from a_sync.config import null_modifiers
        return self.runs_per_minute != null_modifiers.runs_per_minute
    @property
    def use_semaphore(self) -> bool:
        from a_sync.config import null_modifiers
        return self.semaphore != null_modifiers.semaphore
    @property
    def use_cache(self) -> bool:
        from a_sync.config import null_modifiers
        return any([
            self.cache_type != null_modifiers.cache_type,
            self.ram_cache_maxsize != null_modifiers.ram_cache_maxsize,
            self.ram_cache_ttl != null_modifiers.ram_cache_ttl,
            self.cache_typed != null_modifiers.cache_typed,
        ])
    
    def apply_async_modifiers(self, coro_fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        # NOTE: THESE STACK IN REVERSE ORDER
        if self.use_limiter is not None:
            coro_fn = rate_limiting.apply_rate_limit(coro_fn, self.runs_per_minute)
        if self.use_semaphore:
            coro_fn = semaphores.apply_semaphore(coro_fn, self.semaphore)
        if self.use_cache:
            coro_fn = cache.apply_async_cache(
                coro_fn,
                cache_type=self.cache_type or 'memory',
                cache_typed=self.cache_typed,
                ram_cache_maxsize=self.ram_cache_maxsize,
                ram_cache_ttl=self.ram_cache_ttl
            )
        return coro_fn
    
    def apply_sync_modifiers(self, function: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(function)
        def sync_modifier_wrap(*args: P.args, **kwargs: P.kwargs) -> T:
            return function(*args, **kwargs)
        # NOTE There are no sync modifiers at this time but they will be added here for my convenience.
        return sync_modifier_wrap



