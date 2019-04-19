# coding=utf-8

import logging
import os
import pickle
import uuid
from gettext import translation
from typing import Dict, Optional, Tuple

from ehforwarderbot import ChatType, EFBChat, EFBMiddleware, EFBMsg, MsgType, coordinator, utils
from ehforwarderbot.exceptions import EFBException
from pkg_resources import resource_filename
from ruamel.yaml import YAML

from .__version__ import __version__ as version

yaml = YAML()


class TryshMiddleware(EFBMiddleware):
    """
    Configuration:

    .. code-block: yaml

        key: BD6B65EC00638DC9083781D5D4B65BB1A106200A
        password: test
        always_trust: true
        binary: /usr/bin/gpg
        server: pgp.mit.edu
    """
    middleware_id: str = "trysh.trysh"
    middleware_name: str = "trysh Middleware"
    __version__: str = version

    mappings: Dict[Tuple[str, str], str] = {}
    chat: EFBChat = None

    key: str = None
    password: str = None
    always_trust: bool = True
    binary: str = "gpg"
    server: str = "pgp.mit.edu"
    encrypt_all: bool = False

    Me: EFBChat = None

    translator = translation("efb_trysh_middleware",
                             resource_filename("efb_trysh_middleware", "locale"),
                             fallback=True)
    _ = translator.gettext

    def __init__(self, instance_id: str = None):
        super().__init__(instance_id)
        storage_path = utils.get_data_path(self.middleware_id)
        config_path = utils.get_config_path(self.middleware_id)
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)
        if not os.path.exists(config_path):
            raise EFBException(self._("GnuPG middleware is not configured."))
        else:
            config = yaml.load(open(config_path))
            self.key = config['key']
            self.always_trust = config.get('always_trust', self.always_trust)
            self.binary = config.get('binary', self.binary)
            self.password = config.get('password', self.password)
            self.server = config.get('server', self.server)

        self.mappings_path = os.path.join(storage_path, "keymap.pkl")
        if os.path.exists(self.mappings_path):
            self.mappings = pickle.load(open(self.mappings_path, 'rb'))

        self.chat = EFBChat()
        self.chat.channel_name = self.middleware_name
        self.chat.module_name = self.middleware_name
        self.chat.channel_id = self.middleware_id
        self.chat.module_id = self.middleware_id
        self.chat.channel_emoji = "🔐"
        self.chat.chat_uid = "__trysh.trysh__"
        self.chat.chat_name = self.middleware_name
        self.chat.chat_type = ChatType.System

        self.logger = logging.getLogger("trysh.trysh")
        self.logger.debug("trysh init ok")
        # self.logger.setLevel(99)

    def lg(self, msg):  # , *args, **kwargs):
        self.logger.log(99, msg)  # , *args, **kwargs)

    def process_message(self, message: EFBMsg) -> Optional[EFBMsg]:
        self.lg(f"Received:{message} | author:{message.author} | chat:{message.chat} | target:{message.target} | \
 chatt:{message.chat.chat_type} | cmd:{message.commands}")
        # self.lg("Received message: %s |author:%s |chat:%s |type:%s |target:%s",
        #         message, message.author, message.chat, message.type, message.target)
        # if not message.type == MsgType.Text:
        #     return message
        if message.type == MsgType.Text:
            if message.text.strip() == 'tq':
                self.lg(f"chat:{message.chat.module_name}")
                self.reply_message(message, f"rep:{message.text}")
        return message

    def reply_message(self, message: EFBMsg, text: str):
        reply = EFBMsg()
        reply.text = text
        # reply.chat = coordinator.slaves[message.chat.channel_id].get_chat(message.chat.chat_uid)
        reply.chat = coordinator.slaves[message.chat.module_id].get_chat(message.chat.chat_uid)
        reply.author = self.chat
        reply.type = MsgType.Text
        # reply.deliver_to = coordinator.master
        reply.deliver_to = coordinator.slaves[message.chat.module_id]
        # reply.target = message
        reply.uid = str(uuid.uuid4())
        r2 = reply
        coordinator.send_message(reply)
        r2.deliver_to = coordinator.master
        coordinator.send_message(r2)
