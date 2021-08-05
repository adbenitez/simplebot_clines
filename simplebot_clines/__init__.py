import os
import re

import simplebot
from deltachat import Chat, Contact, Message
from simplebot.bot import DeltaBot, Replies

from .db import DBManager
from .game import CELL, Board

__version__ = "1.0.0"
nick_re = re.compile(r"[-a-zA-Z0-9_]{1,16}$")
db: DBManager


@simplebot.hookimpl
def deltabot_init(bot: DeltaBot) -> None:
    global db
    db = _get_db(bot)


@simplebot.hookimpl
def deltabot_member_removed(bot: DeltaBot, chat: Chat, contact: Contact) -> None:
    game = db.get_game_by_gid(chat.id)
    if game:
        me = bot.self_contact
        if contact.addr in (me.addr, game["addr"]):
            db.delete_game(game["addr"])
            if contact != me:
                chat.remove_contact(me)


@simplebot.filter(name=__name__)
def filter_messages(message: Message, replies: Replies) -> None:
    """Process move coordinates in Color Lines game groups."""
    if (
        len(message.text) != 4
        or not message.text.isalnum()
        or message.text.isalpha()
        or message.text.isdigit()
    ):
        return

    game = db.get_game_by_gid(message.chat.id)
    if not game or not game["board"]:
        return

    try:
        b = Board(game["board"])
        b.move(message.text)
        if b.score > game["score"]:
            db.set_game(game["addr"], b.export(), b.score)
        else:
            db.set_board(game["addr"], b.export())
        replies.add(text=_run_turn(message.chat.id))
    except ValueError:
        replies.add(text="❌ Invalid move!")


@simplebot.command
def lines_play(bot: DeltaBot, message: Message, replies: Replies) -> None:
    """Start a new Color Lines game.

    Example: `/lines_play`
    """
    player = message.get_sender_contact()
    if not db.get_nick(player.addr):
        text = "You need to set a nick before start playing,"
        text += " send /lines_nick Your Nick"
        replies.add(text=text)
        return
    game = db.get_game_by_addr(player.addr)

    if game is None:  # create a new chat
        chat = bot.create_group("🌈 Color Lines", [player.addr])
        db.add_game(player.addr, chat.id, Board().export())
        text = "Hello {}, in this group you can play Color Lines.\n\n"
        replies.add(text=text.format(player.name) + _run_turn(chat.id), chat=chat)
    else:
        db.set_board(game["addr"], Board(old_score=game["score"]).export())
        if message.chat.id == game["gid"]:
            chat = message.chat
        else:
            chat = bot.get_chat(game["gid"])
        replies.add(text="Game started!\n\n" + _run_turn(game["gid"]), chat=chat)


@simplebot.command
def lines_next(message: Message, replies: Replies) -> None:
    """Skip to next turn.

    Example: `/lines_next`
    """
    game = db.get_game_by_gid(message.chat.id)
    if game and game["board"]:
        b = Board(game["board"])
        b.next()
        db.set_board(game["addr"], b.export())
        replies.add(text=_run_turn(message.chat.id))
    else:
        replies.add(text="No active game, send /lines_play to start playing.")


@simplebot.command
def lines_nick(payload: str, message: Message, replies: Replies) -> None:
    """Set your nick shown in Color Lines scoreboard or show your current nick if no new nick is provided.

    Example: `/lines_nick Dark Warrior`
    """
    addr = message.get_sender_contact().addr
    if payload:
        new_nick = " ".join(payload.split())
        if not nick_re.match(new_nick):
            replies.add(
                text='** Invalid nick, only letters, numbers, "-" and'
                ' "_" are allowed, and nick should be less than 16 characters'
            )
        elif db.get_addr(new_nick):
            replies.add(text="** Nick already taken, try again")
        else:
            db.set_nick(addr, new_nick)
            replies.add(text="** Nick: {}".format(new_nick))
    else:
        replies.add(text="** Nick: {}".format(db.get_nick(addr)))


@simplebot.command
def lines_repeat(bot: DeltaBot, message: Message, replies: Replies) -> None:
    """Send Color Lines game board again.

    Example: `/lines_repeat`
    """
    game = db.get_game_by_addr(message.get_sender_contact().addr)
    if game and game["board"]:
        if message.chat.id == game["gid"]:
            chat = message.chat
        else:
            chat = bot.get_chat(game["gid"])
        replies.add(text=_run_turn(game["gid"]), chat=chat)
    else:
        replies.add(text="No active game, send /lines_play to start playing.")


@simplebot.command
def lines_top(message: Message, replies: Replies) -> None:
    """Send Color Lines scoreboard.

    Example: `/lines_top`
    """
    limit = 15
    text = "🏆 Color Lines Scoreboard\n\n"
    game = db.get_game_by_addr(message.get_sender_contact().addr)
    if not game:
        games = db.get_games(limit)
    else:
        games = db.get_games()
    if not games:
        text += "(Empty list)"
    for n, g in enumerate(games[:limit], 1):
        text += "#{} {} {}\n".format(n, db.get_nick(g["addr"]), g["score"])
    if game:
        player_pos = games.index(game)
        if player_pos >= limit:
            text += "\n"
            if player_pos > limit:
                pgame = games[player_pos - 1]
                text += "#{} {} {}\n".format(
                    player_pos, db.get_nick(pgame["addr"]), pgame["score"]
                )
            text += "#{} {} {}\n".format(
                player_pos + 1, db.get_nick(game["addr"]), game["score"]
            )
            if player_pos < len(games) - 1:
                ngame = games[player_pos + 1]
                text += "#{} {} {}\n".format(
                    player_pos + 2, db.get_nick(ngame["addr"]), ngame["score"]
                )
    replies.add(text=text)


def _run_turn(gid: int) -> str:
    g = db.get_game_by_gid(gid)
    assert g is not None
    b = Board(g["board"])
    if b.result() == 1:
        if b.old_score >= b.score > b.old_score / 2:
            score = b.old_score + 1
        else:
            score = b.score
        if score > b.old_score:
            db.set_game(g["addr"], None, score)
            text = "🏆 Game over\nNew High Score: {}\n📊 /lines_top\n\n{}"
        else:
            db.set_board(g["addr"], None)
            text = "☠️ Game over\n📊 Score: {}\n\n {}"
        text = text.format(score, b)
        text += "\n▶️ Play again?  /lines_play"
        return text

    text = "📊 Score: {} / {}\n\n{}".format(b.score, g["score"], b)
    text += "\nNext:  {}  /lines_next".format(
        " ".join(CELL[e.color] for e in b.game.next_balls)
    )
    return text


def _get_db(bot: DeltaBot) -> DBManager:
    path = os.path.join(os.path.dirname(bot.account.db_path), __name__)
    if not os.path.exists(path):
        os.makedirs(path)
    return DBManager(os.path.join(path, "sqlite.db"))
