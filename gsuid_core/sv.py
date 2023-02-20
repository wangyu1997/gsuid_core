from __future__ import annotations

from functools import wraps
from typing import Dict, List, Tuple, Union, Literal, Callable, Optional

from logger import logger
from trigger import Trigger
from config import core_config


class SVList:
    def __init__(self):
        self.lst: Dict[str, SV] = {}

    @property
    def get_lst(self):
        return self.lst


SL = SVList()
config_sv = core_config.get_config('sv')


class SV:
    is_initialized = False

    def __new__(cls, *args, **kwargs):
        # 判断sv是否已经被初始化
        if args[0] in SL.lst:
            return SL.lst[args[0]]
        else:
            _sv = super().__new__(cls)
            SL.lst[args[0]] = _sv
            return _sv

    def __init__(
        self,
        name: str = '',
        permission: int = 3,
        priority: int = 5,
        enabled: bool = True,
        area: Literal['GROUP', 'DIRECT', 'ALL'] = 'ALL',
        black_list: List = [],
    ):
        if not self.is_initialized:
            logger.info(f'【{name}】模块初始化中...')
            # sv名称，重复的sv名称将被并入一个sv里
            self.name: str = name
            # sv内包含的触发器
            self.TL: Dict[str, Trigger] = {}
            self.is_initialized = True

            # 判断sv是否已持久化
            if name in config_sv:
                self.priority = config_sv[name]['priority']
                self.enabled = config_sv[name]['enabled']
                self.permission = config_sv[name]['permission']
                self.black_list = config_sv[name]['black_list']
                self.area = config_sv[name]['area']
            else:
                # sv优先级
                self.priority = priority
                # sv是否开启
                self.enabled = enabled
                # 黑名单群
                self.black_list = black_list
                # 权限 0为master，1为superuser，2为群的群主&管理员，3为普通
                self.permission = permission
                # 作用范围
                self.area = area
                # 写入
                self.set(
                    priority=priority,
                    enabled=enabled,
                    permission=permission,
                    black_list=black_list,
                    area=area,
                )

    def set(self, **kwargs):
        for var in kwargs:
            setattr(self, var, kwargs[var])
            if self.name not in config_sv:
                config_sv[self.name] = {}
            config_sv[self.name][var] = kwargs[var]
            core_config.set_config('sv', config_sv)

    def enable(self):
        self.set(enabled=True)

    def disable(self):
        self.set(enabled=False)

    def _on(
        self,
        type: Literal['prefix', 'suffix', 'keyword', 'fullmatch'],
        keyword: Union[str, Tuple[str, ...]],
    ):
        def deco(func: Callable) -> Callable:
            keyword_list = keyword
            if isinstance(keyword, str):
                keyword_list = (keyword,)
            for _k in keyword_list:
                if _k not in self.TL:
                    logger.info(f'载入{type}触发器【{_k}】!')
                    self.TL[_k] = Trigger(type, _k, func)

            @wraps(func)
            async def wrapper(bot, msg) -> Optional[Callable]:
                return await func(bot, msg)

            return wrapper

        return deco

    def on_fullmatch(self, keyword: Union[str, Tuple[str, ...]]) -> Callable:
        return self._on('fullmatch', keyword)

    def on_prefix(self, keyword: Union[str, Tuple[str, ...]]) -> Callable:
        return self._on('prefix', keyword)

    def on_suffix(self, keyword: Union[str, Tuple[str, ...]]) -> Callable:
        return self._on('suffix', keyword)

    def on_keyword(self, keyword: Union[str, Tuple[str, ...]]) -> Callable:
        return self._on('keyword', keyword)
