from pony import orm
import tornado.web

from models import User
from spotify_client import spt
from utils import config, bot, bot_description
from telegram import Animation


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


class SpotifyCallback(tornado.web.RequestHandler):
    @orm.db_session
    def get(self):
        if self.get_argument("code", ""):
            grant = self.get_argument("code", "")
            callback_state = self.get_argument("state", "")
            if not callback_state:
                self.write("spotify no callback state")
            spoti = spt
            try:
                user_creds = spoti.build_user_creds(grant=grant)
            except:
                self.write("spotify build user creds error")
            else:
                users = orm.select(u for u in User if u.telegram_id == callback_state)[
                    :
                ]
                if users:
                    user = users[0]
                    user.spotify_id = user_creds.id
                    user.spotify_access_token = user_creds.access_token
                    user.spotify_refresh_token = user_creds.refresh_token
                    orm.commit()
                else:
                    user = User(
                        telegram_id=callback_state,
                        spotify_id=user_creds.id,
                        spotify_access_token=user_creds.access_token,
                        spotify_refresh_token=user_creds.refresh_token,
                    )
                    orm.commit()

                bot.sendMessage(callback_state, "Logged in!")
                bot.sendAnimation(callback_state, "CgACAgQAAxkDAAIBqF4rRwTDEXJcZtA8P4IFN1ly7WwnAAL0AQACysUEUXEQkHacMB3BGAQ")
                bot.sendMessage(callback_state, bot_description)
                self.redirect("https://t.me/" + bot.username)

        else:
            self.write("spotify no code")


class SpotifyRedirectHandler(tornado.web.RequestHandler):
    def get(self, track_id):
        html = '''
        <html>
            <head>
                <meta http-equiv="refresh" content="0;url=spotify://track/{}" />
                <title></title>
            </head>
            <body></body>
        </html>
        '''
        html = html.format(track_id)

        self.write(html)


urls = [
    (r"/", MainHandler),
    (r"/spotify/callback", SpotifyCallback),
    (r"/spotify/track/(\w+)", SpotifyRedirectHandler),
    ]
