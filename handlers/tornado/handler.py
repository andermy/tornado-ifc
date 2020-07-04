"""Web socket API message handler"""

from tornado import gen
import repackage
repackage.up()
from service import StoreClient


class MessageHandler(object):

    def __init__(self, store_class=StoreClient):
        # Inject a different data storage module by providing a different class
        # name to the 'store_class' kwarg.
        self.store = store_class()

    def handle_message(self, msg):
        """Handle a received message.
        The first token (word) in the msg is the command, which determines
        how the remaining tokens are handled.
        """

        tokens = msg.split(' ')
        if hasattr(self, tokens[0]):
            return getattr(self, tokens[0])(tokens[1:])
        else:
            raise ValueError('command "{0}" not recognized'.format(tokens[0]))

    @gen.coroutine
    def get(self, tokens):
        if len(tokens) > 1:
            raise ValueError('too many words for "get" (expected "get key")')
        key = tokens[0]
        value = yield self.store.get(key)
        
        return value

    @gen.coroutine
    def set(self, tokens):
        if len(tokens) < 2:
            raise ValueError(
                'not enough words for "set" (expected "set key value")'
            )
        key = tokens[0]
        value = ' '.join(tokens[1:])
        response = yield self.store.set(key, value)

        return response