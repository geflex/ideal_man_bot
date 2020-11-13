from abc import ABC, abstractmethod
from functools import cached_property
from typing import Any, Awaitable

from bottex2.chat import Keyboard
from bottex2.handler import Request, Handler
from bottex2.router import Router, Condition
from bottex2.ext.users import gen_state_cases
from bottex2.views import View, Command


def if_contains(s) -> Condition:
    s = s.lower()
    def case(r: Request):
        return s in r.text.lower()
    return case


class IdealView(View, ABC):
    message: str
    next_callback: Handler

    @property
    def router(self) -> Router:
        router = Router(default=self.default)
        for i, line in enumerate(self.commands):
            i = i + 1
            for command in line:
                router.add_route(if_contains(str(i)), command.callback)
                router.add_route(if_contains(command.text), command.callback)
        return router

    @property
    def keyboard(self) -> Keyboard:
        return Keyboard()

    def gen_message(self) -> str:
        choises = []
        for i, line in enumerate(self.commands):
            i = i + 1
            for command in line:
                choises.append(f'{i}. {command.text}')
        return '\n'.join(choises)

    @classmethod
    async def switch(cls, r: Request) -> Awaitable[Any]:
        await super().switch(r)
        self = cls(r)
        choises = self.gen_message()
        message = cls.message.format(choises)
        return r.resp(message, self.keyboard)

    def _get_commands(self):
        commands = []
        def add(s):
            commands.append([Command(s, self._get_setter(s))])
        return commands, add

    def _get_setter(self, s: str):
        async def setter(r: Request):
            return await self.next(r)
        return setter

    @abstractmethod
    async def next(self, r: Request):
        pass

    async def default(self, r: Request):
        return r.resp('Я могу понять только шаблонные ответы', self.keyboard)


class Round1(IdealView):
    message = """Итак, выбирай, чем ты хочешь заняться сегодня: 
{}"""

    async def next(self, r: Request):
        return await Round2.switch(r)

    @cached_property
    def commands(self):
        commands, add = self._get_commands()
        add('Пойти в бар')
        add('Пойти в рестик')
        add('Пойти в кино')
        add('Погулять')
        add('Посидеть дома и посмотреть фильм')
        add('Поваляться в постели')
        add('Покататься по городу')
        return commands


class Round2(IdealView):
    message = """Ок, раунд 2.

Выбирай, что хочешь посмотреть :

{}"""

    async def next(self, r: Request):
        return await Round3.switch(r)

    @cached_property
    def commands(self):
        commands, add = self._get_commands()
        add('Фильм')
        add('Сериал')
        add('Мультфильм')
        add('Документалку про убийц')
        return commands


class Round3(IdealView):
    message = """Раунд 3

Выбери сериал:
    
{}

(Если хочешь посмотреть что-то из того, что мы уже смотрели, просто напиши)"""

    async def next(self, r: Request):
        return await Round4.switch(r)

    @cached_property
    def commands(self):
        commands, add = self._get_commands()
        add('Черное зеркало')
        add('Очень странные дела')
        add('Как я встретил вашу маму')
        add('Ривердейл')
        return commands


class Round4(IdealView):
    message = """Хорошо, финал
Выбери, где мне купить еду: 
{}"""

    async def next(self, r: Request):
        return await Round1.switch(r)

    @cached_property
    def commands(self):
        commands, add = self._get_commands()
        add('Макдак')
        add('Кфс')
        add('Бургер Кинг')
        add('Карлс Джуниор')
        add('Пицца хатт')
        add('Другое')
        return commands


class Success(View):
    @cached_property
    def commands(self):
        return [[Command('Начать сначала', Round1.switch)]]

    async def default(self, r: Request) -> Awaitable[Any]:
        return await Round1.switch(r)

    @classmethod
    async def switch(cls, r: Request) -> Awaitable[Any]:
        await super().switch(r)
        return r.resp("""Понял - принял. Прибуду через 40 минут""")


main = Router(gen_state_cases([
    Round1,
    Round2,
    Round3,
    Round4,
    Success,
]), default=Round1.switch)
