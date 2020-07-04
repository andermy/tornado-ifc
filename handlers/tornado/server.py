"""A simple key/value store websocket API."""

from tornado import gen, ioloop, web, websocket
import time
import repackage
repackage.up()
from handler import MessageHandler


class SocketHandler(websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):
        # Inject a different message handler class by providing the class name
        # with the 'handler_class' kwarg:
        self.message_handler = kwargs.pop('handler_class', MessageHandler)()
        super().__init__(*args, **kwargs)

    def check_origin(self, origin):
        return True

    def open(self):
        self.write_message('hello')

    @gen.coroutine
    def on_message(self, msg):
        try:
            response = yield self.message_handler.handle_message(msg)
            self.write_message(response)
        except Exception as e:
            self.write_message(str(e))

def make_app():
    return web.Application([
        (r'/connect', SocketHandler),
    ])


if __name__ == '__main__':
    app = make_app()
    app.listen(8888)

    print("Websocket startet")
    ioloop.IOLoop.instance().start()
    time.sleep(120)
    ioloop.IOLoop.instance().stop()