from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram import filters

from .EchoClient import EchoBot
from ..plugins.poster import _poster_cmd
from ..plugins.broadcast import _broadcast
from ..plugins.cmds import _strt, _ping
from ..plugins.service import (
    _authorize, _unauthorize, _log_cmd, _log_cb, _restart, _restart_cb
)
from ..plugins.imdb import _imdb_search, _imdb_callback
from ..plugins.anilist import _anime, _anime_cb
from ..plugins.bypass import _bypass_cmd
from ..plugins.tmdb import _p
from ..plugins.overlap import _olap_cmd, _olap_cb
from ..helper.utils.bot_cmds import BotCommands
from ..helper.utils.filters import CustomFilters


def add_plugs():
    EchoBot.bot.add_handler(
        MessageHandler(
            _strt,
            filters.command(BotCommands.StartCommand, case_sensitive=True)
            & CustomFilters.authorized,
        )
    )

    EchoBot.bot.add_handler(
        MessageHandler(
            _authorize,
            filters.command(BotCommands.AuthorizeCommand, case_sensitive=True)
            & CustomFilters.sudo,
        )
    )

    EchoBot.bot.add_handler(
        MessageHandler(
            _unauthorize,
            filters.command(BotCommands.UnAuthorizeCommand, case_sensitive=True)
            & CustomFilters.sudo,
        )
    )

    EchoBot.bot.add_handler(
        MessageHandler(
            _log_cmd,
            filters.command(BotCommands.LogCommand, case_sensitive=True)
            & CustomFilters.sudo,
        )
    )

    EchoBot.bot.add_handler(
        CallbackQueryHandler(
            _log_cb,
            filters.regex(r"^log ") & CustomFilters.sudo,
        )
    )

    EchoBot.bot.add_handler(
        MessageHandler(
            _ping,
            filters.command(BotCommands.PingCommand, case_sensitive=True)
            & CustomFilters.authorized,
        )
    )

    EchoBot.bot.add_handler(
        MessageHandler(
            _restart,
            filters.command(BotCommands.RestartCommand, case_sensitive=True)
            & CustomFilters.sudo,
        )
    )

    EchoBot.bot.add_handler(
        CallbackQueryHandler(
            _restart_cb,
            filters.regex(r"^restart ") & CustomFilters.sudo,
        )
    )

    EchoBot.bot.add_handler(
        MessageHandler(
            _broadcast,
            filters.command(BotCommands.BroadcastCommand, case_sensitive=True)
            & CustomFilters.sudo,
        )
    )

    EchoBot.bot.add_handler(
        MessageHandler(
            _imdb_search,
            filters.command(BotCommands.ImdbCommand, case_sensitive=True)
            & CustomFilters.authorized,
        )
    )

    EchoBot.bot.add_handler(
        CallbackQueryHandler(
            _imdb_callback,
            filters.regex(r"^imdb ") & CustomFilters.authorized,
        )
    )

    EchoBot.bot.add_handler(
        MessageHandler(
            _poster_cmd,
            filters.command(BotCommands.PosterCommand, case_sensitive=True)
            & CustomFilters.authorized,
        )
    )

    EchoBot.bot.add_handler(
        MessageHandler(
            _bypass_cmd,
            filters.command(BotCommands.BypassCommand, case_sensitive=True)
            & CustomFilters.authorized,
        )
    )

    EchoBot.bot.add_handler(
        MessageHandler(
            _p,
            filters.command(BotCommands.PosterSearchCommand, case_sensitive=True)
            & CustomFilters.authorized,
        )
    )

    EchoBot.bot.add_handler(
        MessageHandler(
            _anime,
            filters.command(BotCommands.AnimeCommand, case_sensitive=True)
            & CustomFilters.authorized,
        )
    )

    EchoBot.bot.add_handler(
        CallbackQueryHandler(
            _anime_cb,
            filters.regex(r"^anime ") & CustomFilters.authorized,
        )
    )

    EchoBot.bot.add_handler(
        MessageHandler(
            _olap_cmd,
            filters.command(BotCommands.OverlapCommand, case_sensitive=True)
            & CustomFilters.authorized,
        )
    )

    EchoBot.bot.add_handler(
        CallbackQueryHandler(
            _olap_cb,
            filters.regex(r"^ov ") & CustomFilters.authorized,
        )
    )
