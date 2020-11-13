import logging

from sqlalchemy import create_engine

from bottex2 import sqlalchemy as sqldb
from bottex2.bottex import Bottex
from bottex2.ext import users, responses
from bottex2.platforms.tg import TgReceiver
from bottex2.platforms.vk import VkReceiver
from ideal_man import logic, configs


def get_bottex():
    bottex = Bottex(
        TgReceiver(configs.tg.token),
        VkReceiver(configs.vk.token, configs.vk.group_id),
    )
    bottex.set_handler(logic.main)
    return bottex


def setup_db():
    db = create_engine(configs.db_url)
    sqldb.create_tables(db)
    sqldb.set_engine(db)
    users.set_user_model(users.UserModel)


def set_middlewares(bottex):
    bottex.add_middleware(responses.ResponseBottexMiddleware)
    bottex.add_middleware(users.UserBottexMiddleware)


def main():
    setup_db()
    bottex = get_bottex()
    set_middlewares(bottex)
    bottex.serve_forever()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
