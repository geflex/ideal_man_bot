import asyncio
import json
import sys
from random import randint
from typing import Union, Optional, AsyncIterator

import aiohttp
from aiovk import API
from aiovk.exceptions import VkAPIError
from aiovk.longpoll import BotsLongPoll
from aiovk.sessions import BaseSession, TokenSession

from bottex2.chat import AbstractChat, Keyboard
from bottex2.ext.users import UserBottexMiddleware
from bottex2.handler import Request
from bottex2.logging import logger
from bottex2.receiver import Receiver


class VkChat(AbstractChat):
    def __init__(self, session: BaseSession, peer_id: Union[int, str]):
        super().__init__()
        self._api = API(session)
        self._peer_id = peer_id

    def _prepare_kb(self, kb: Optional[Keyboard]):
        if kb is None:
            return ''
        json_buttons = []
        json_kb = {'one_time': kb.one_time,
                   'buttons': json_buttons}
        if not kb.empty():
            for line in kb:
                json_line = []
                json_buttons.append(json_line)
                for button in line:
                    json_line.append({
                        'action': {
                            'type': 'text',
                            'label': button.label
                        },
                        'color': 'secondary',
                    })
        return json.dumps(json_kb)

    async def send_message(self, text: Optional[str] = None, kb: Optional[Keyboard] = None):
        try:
            await self._api.messages.send(random_id=randint(0, sys.maxsize),
                                          user_id=self._peer_id,
                                          message=text,
                                          keyboard=self._prepare_kb(kb))
        except (asyncio.TimeoutError, aiohttp.ClientOSError, VkAPIError) as e:
            logger.error(repr(e))


class VkReceiver(Receiver):
    def __init__(self, token: str, group_id: str):
        super().__init__()
        self._session = TokenSession(access_token=token)
        self._longpoll = BotsLongPoll(self._session, mode=0, group_id=group_id)

    async def listen(self) -> AsyncIterator[Request]:
        while True:
            try:
                response = await self._longpoll.wait(need_pts=True)
            except (asyncio.TimeoutError, VkAPIError, aiohttp.ClientError) as e:
                logger.error(repr(e))
            else:
                for event in response['updates']:
                    if event['type'] == 'message_new':
                        message = event['object']['message']
                        chat = VkChat(self._session, message['peer_id'])
                        yield Request(text=message['text'],
                                      chat=chat,
                                      raw=event)


@UserBottexMiddleware.submiddleware(VkReceiver)
class VkUserHandlerMiddleware(UserBottexMiddleware):
    async def get_user(self, request: Request):
        uid = request.raw['object']['message']['from_id']
        return await self.get_or_create('vk', uid)
