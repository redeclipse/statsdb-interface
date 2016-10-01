import config
from flask import Blueprint, render_template, send_from_directory, request

from .. import dbmodels, extmodels
from . import templateutils

# displays blueprint
bp = Blueprint(__name__, __name__)


@bp.route('/static/<path:path>')
def static(path):
    return send_from_directory('static', path)


@bp.route("/")
def display_dashboard():
    games = dbmodels.Game.query.order_by(dbmodels.Game.id.desc()).limit(
        config.DISPLAY_RESULTS_RECENT).all()
    return render_template('displays/dashboard.html', games=games)


@bp.route("/games")
def display_games():
    pager = dbmodels.Game.query.order_by(dbmodels.Game.id.desc()).paginate(
            request.args.get("page", default=1, type=int),
            config.DISPLAY_RESULTS_PER_PAGE)

    return render_template('displays/games.html',
                           games=pager.items, pager=pager)


@bp.route("/games/<int:gameid>")
def display_game(gameid):
    game = dbmodels.Game.query.filter_by(id=gameid).first_or_404()
    return render_template('displays/game.html', game=game)


@bp.route("/servers")
def display_servers():
    pager = extmodels.Server.paginate(
        request.args.get("page", default=1, type=int),
        config.DISPLAY_RESULTS_PER_PAGE)

    ret = render_template('displays/servers.html',
                          servers=pager.items, pager=pager)
    return ret


@bp.route("/servers/<string:handle>")
def display_server(handle):
    server = extmodels.Server.get_or_404(handle)
    return render_template('displays/server.html', server=server)


@bp.route("/server_games/<string:handle>")
def display_server_games(handle):
    server = extmodels.Server.get_or_404(handle)
    pager = dbmodels.Game.query.filter(
            dbmodels.Game.id.in_(server.game_ids)).order_by(
            dbmodels.Game.id.desc()).paginate(
            request.args.get("page", default=1, type=int),
            config.DISPLAY_RESULTS_PER_PAGE)
    return render_template('displays/server_games.html',
                           server=server, games=pager.items, pager=pager)

templateutils.register(bp)
