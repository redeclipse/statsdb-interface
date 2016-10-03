import config
from flask import Blueprint, render_template, send_from_directory, request

from ..database import models, extmodels
from . import templateutils

# displays blueprint
bp = Blueprint(__name__, __name__)


@bp.route('/static/<path:path>')
def static(path):
    return send_from_directory('static', path)


@bp.route("/")
def display_dashboard():
    games = models.Game.query.order_by(models.Game.id.desc()).limit(
        config.DISPLAY_RESULTS_RECENT).all()
    return render_template('displays/dashboard.html', games=games)


@bp.route("/games")
def display_games():
    pager = models.Game.query.order_by(models.Game.id.desc()).paginate(
            request.args.get("page", default=1, type=int),
            config.DISPLAY_RESULTS_PER_PAGE)

    return render_template('displays/games.html', pager=pager)


@bp.route("/game/<int:gameid>")
@bp.route("/games/<int:gameid>")
def display_game(gameid):
    game = models.Game.query.filter_by(id=gameid).first_or_404()
    return render_template('displays/game.html', game=game)


@bp.route("/servers")
def display_servers():
    pager = extmodels.Server.paginate(
        request.args.get("page", default=1, type=int),
        config.DISPLAY_RESULTS_PER_PAGE)

    ret = render_template('displays/servers.html', pager=pager)
    return ret


@bp.route("/server/<string:handle>")
@bp.route("/servers/<string:handle>")
def display_server(handle):
    server = extmodels.Server.get_or_404(handle)
    return render_template('displays/server.html', server=server)


@bp.route("/server:games/<string:handle>")
def display_server_games(handle):
    server = extmodels.Server.get_or_404(handle)
    pager = models.Game.query.filter(
            models.Game.id.in_(server.game_ids)).order_by(
            models.Game.id.desc()).paginate(
            request.args.get("page", default=1, type=int),
            config.DISPLAY_RESULTS_PER_PAGE)
    return render_template('displays/server_games.html', server=server,
                           pager=pager)


@bp.route("/players")
def display_players():
    pager = extmodels.Player.paginate(
        request.args.get("page", default=1, type=int),
        config.DISPLAY_RESULTS_PER_PAGE)

    ret = render_template('displays/players.html', pager=pager)
    return ret


@bp.route("/player/<string:handle>")
@bp.route("/players/<string:handle>")
def display_player(handle):
    player = extmodels.Player.get_or_404(handle)
    return render_template('displays/player.html', player=player)


@bp.route("/player:games/<string:handle>")
def display_player_games(handle):
    player = extmodels.Player.get_or_404(handle)
    pager = models.Game.query.filter(
            models.Game.id.in_(player.game_ids)).order_by(
            models.Game.id.desc()).paginate(
            request.args.get("page", default=1, type=int),
            config.DISPLAY_RESULTS_PER_PAGE)
    return render_template('displays/player_games.html', player=player,
                           pager=pager)

templateutils.setup(bp)
