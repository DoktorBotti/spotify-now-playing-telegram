from uuid import uuid4
from pony import orm
from telegram import (
    ParseMode,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.utils.helpers import escape_markdown
from datetime import datetime

from models import User
from spotify_client import spt, get_credentials
from utils import bot_description, app_url


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text(bot_description)


@orm.db_session
def start(update, context):
    """Send a message when the command /start is issued."""
    if spt.is_oauth_ready:
        user_id = str(update.message.from_user.id)
        url = spt.auth_uri(state=user_id)
        update.message.reply_text(
            "Tap the button below to log in with your Spotify account",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Login", url=url)]]
            ),
        )
    else:
        print("There's something wrong")
        update.message.reply_text("There's something wrong")


@orm.db_session
def inlinequery(update, context):
    """Handle the inline query."""
    user_id = update.inline_query.from_user.id
    users = orm.select(u for u in User if u.telegram_id == user_id)[:]
    if users:
        user = users[0]
    else:
        update.inline_query.answer(
            [],
            switch_pm_text="Login to Spotify",
            switch_pm_parameter="spotify_log_in",
            cache_time=0,
        )
        return 0

    user_creds = get_credentials(user)

    spoti = spt
    spoti.user_creds = user_creds

    current_status = spoti.currently_playing()  # ["item"]
    if current_status:
        song = spoti.currently_playing()["item"]
    else:  # no songs currently playing
        song = spoti.recently_played_tracks(limit=1)["items"][0][
            "track"
        ]  # get the last played song
    print(
        "{} | {} - {}".format(datetime.now(), song["artists"][0]["name"], song["name"])
    )
    song_title = song["name"]
    song_artist = song["artists"][0]["name"]
    song_url = song["external_urls"]["spotify"]
    thumb = song["album"]["images"][-1]
    if "localhost" in app_url:
        app_song_url = song_url
    else:
        app_song_url = app_url + "/spotify/track/" + song["id"]
    results = [
        InlineQueryResultArticle(
            id=uuid4(),
            title="{} - {}".format(song_artist, song_title),
            url=song_url,
            thumb_url=thumb["url"],
            thumb_width=thumb["width"],
            thumb_height=thumb["height"],
            input_message_content=InputTextMessageContent(
                "🎵 [{}]({}) by {}".format(
                    escape_markdown(song_title), song_url, escape_markdown(song_artist)
                ),
                parse_mode=ParseMode.MARKDOWN,
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Listen on Spotify", url=app_song_url)]
                ]
            ),
        )
    ]

    update.inline_query.answer(results, cache_time=0)


def error(update, context):
    """Log Errors caused by Updates."""
    print('Update "%s" caused error "%s"', update, context.error)
