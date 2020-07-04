import tornado.ioloop
import tornado.web
import urlparse

## mongodb and pymongo installation assumed
import pymongo
from pymongo import Connection

class Article(tornado.web.RequestHandler):
    def initialize(self):
        self.conn = pymongo.Connection()
        self.db=self.conn['library']

    def post(self):
        article = urlparse.parse_qs(self.request.body)
        for key in article:
                article[key] = article[key][0]
        collection = self.db['articles']
        self.db.articles.insert({"id":article['id'], "author":article['author'], "genre":article['genre']})

    def get(self):
        articleid = self.get_argument("articleid", None)
        if articleid is None:
                articleList = self.db.articles.find()
                self.write(str(list(articleList)))
        else:
                article = str(self.db.articles.find_one({"id":articleid}))
                self.write(article)

    def delete(self):
        self.db.articles.drop()

application = tornado.web.Application([
    (r"/articles", Article),
],debug=True)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()