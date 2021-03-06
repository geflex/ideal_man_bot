from typing import Optional, Any, Awaitable

from bottex2.bottex import BottexMiddleware
from bottex2.chat import Keyboard, ChatMiddleware
from bottex2.logging import logger


class BottexLoggingMiddleware(BottexMiddleware):
    __unified__ = True

    async def __call__(self, request) -> Awaitable[Any]:
        logger.info(f'in : {request.text!r}')
        request.chat = BottexLoggingChatMiddleware(request.chat)
        return await self.handler(request)


class BottexLoggingChatMiddleware(ChatMiddleware):
    async def send_message(self, text: Optional[str] = None, kb: Optional[Keyboard] = None):
        logger.info(f'out: {text!r}')
        await self.chat.send_message(text, kb)
