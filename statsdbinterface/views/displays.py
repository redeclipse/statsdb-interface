from flask import current_app
from flask import Blueprint, render_template, send_from_directory, request

from ..database import models, extmodels
from ..database.core import db
from . import templateutils
from .. import rankings

# displays blueprint
bp = Blueprint(__name__, __name__)


@bp.route('/static/<path:path>')
def static(path):
    return send_from_directory('static', path)


@bp.route("/")
def display_dashboard():
    games = models.Game.query.order_by(models.Game.id.desc()).limit(
        current_app.config['DISPLAY_RESULTS_RECENT']).all()
    return render_template('displays/dashboard.html',
                           games=games,
                           rankings=rankings)


@bp.route("/games")
def display_games():
    pager = models.Game.query.order_by(models.Game.id.desc()).paginate(
            request.args.get("page", default=1, type=int),
            current_app.config['DISPLAY_RESULTS_PER_PAGE'])

    return render_template('displays/games.html', pager=pager,
                           Game=models.Game)


@bp.route("/game/<int:gameid>")
@bp.route("/games/<int:gameid>")
def display_game(gameid):
    game = models.Game.query.filter_by(id=gameid).first_or_404()
    weapons = extmodels.Weapon.all_from_game(game.id)
    return render_template('displays/game.html', game=game,
                           weapons=weapons,
                           totalwielded=(models.GameWeapon.query
                                         .with_entities(db.func.sum(
                                             models.GameWeapon.timewielded))
                                         .filter(models.GameWeapon
                                                 .game_id == game.id)
                                         .first()[0]))


@bp.route("/servers")
def display_servers():
    pager = extmodels.Server.paginate(
        request.args.get("page", default=1, type=int),
        current_app.config['DISPLAY_RESULTS_PER_PAGE'])

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
            current_app.config['DISPLAY_RESULTS_PER_PAGE'])
    return render_template('displays/server_games.html', server=server,
                           pager=pager)


@bp.route("/players")
def display_players():
    pager = extmodels.Player.paginate(
        request.args.get("page", default=1, type=int),
        current_app.config['DISPLAY_RESULTS_PER_PAGE'])

    ret = render_template('displays/players.html', pager=pager)
    return ret


@bp.route("/player/<string:handle>")
@bp.route("/players/<string:handle>")
def display_player(handle):
    player = extmodels.Player.get_or_404(handle)
    games = (models.Game.query
             .with_entities(models.Game.id)
             .filter(~db.func.re_mode(models.Game.id, 'race'))
             .filter(~db.func.re_mut(models.Game.id, 'insta'))
             .filter(~db.func.re_mut(models.Game.id, 'medieval'))
             .filter(models.Game.id.in_(player.game_ids))
             .order_by(models.Game.id.desc()).limit(50))
    weapons = extmodels.Weapon.all_from_player_games(handle, games)
    return render_template('displays/player.html',
                           player=player,
                           weapons=weapons,
                           totalwielded=(models.GameWeapon.query
                                         .with_entities(db.func.sum(
                                             models.GameWeapon.timewielded))
                                         .filter(models.GameWeapon.game_id.in_(
                                             games
                                             ))
                                         .filter(models.GameWeapon
                                                 .playerhandle == handle)
                                         .first()[0]) or 0)


@bp.route("/player:games/<string:handle>")
def display_player_games(handle):
    player = extmodels.Player.get_or_404(handle)
    pager = models.Game.query.filter(
            models.Game.id.in_(player.game_ids)).order_by(
            models.Game.id.desc()).paginate(
            request.args.get("page", default=1, type=int),
            current_app.config['DISPLAY_RESULTS_PER_PAGE'])
    return render_template('displays/player_games.html', player=player,
                           pager=pager)


@bp.route("/maps")
def display_maps():
    pager = extmodels.Map.paginate(
        request.args.get("page", default=1, type=int),
        current_app.config['DISPLAY_RESULTS_PER_PAGE'])

    ret = render_template('displays/maps.html', pager=pager)
    return ret


@bp.route("/racemaps")
def display_racemaps():
    pager = extmodels.Map.paginate(
        request.args.get("page", default=1, type=int),
        current_app.config['DISPLAY_RESULTS_PER_PAGE'],
        race=True)

    ret = render_template('displays/racemaps.html', pager=pager)
    return ret


@bp.route("/map/<string:name>")
@bp.route("/maps/<string:name>")
def display_map(name):
    map = extmodels.Map.get_or_404(name)
    return render_template('displays/map.html', map=map)


@bp.route("/map:games/<string:name>")
def display_map_games(name):
    map = extmodels.Map.get_or_404(name)
    pager = models.Game.query.filter(
            models.Game.id.in_(map.game_ids)).order_by(
            models.Game.id.desc()).paginate(
            request.args.get("page", default=1, type=int),
            current_app.config['DISPLAY_RESULTS_PER_PAGE'])
    return render_template('displays/map_games.html', map=map,
                           pager=pager)


@bp.route("/modes")
def display_modes():
    ret = render_template('displays/modes.html',
                          modes=sorted(extmodels.Mode.all(),
                                       key=lambda m: len(m.game_ids),
                                       reverse=True),
                          rankings=rankings)
    return ret


@bp.route("/mode/<string:name>")
@bp.route("/modes/<string:name>")
def display_mode(name):
    mode = extmodels.Mode.get_or_404(name)
    return render_template('displays/mode.html', mode=mode)


@bp.route("/mode:games/<string:name>")
def display_mode_games(name):
    mode = extmodels.Mode.get_or_404(name)
    pager = models.Game.query.filter(
            models.Game.id.in_(mode.game_ids)).order_by(
            models.Game.id.desc()).paginate(
            request.args.get("page", default=1, type=int),
            current_app.config['DISPLAY_RESULTS_PER_PAGE'])
    return render_template('displays/mode_games.html', mode=mode,
                           pager=pager)


@bp.route("/mutators")
def display_mutators():
    ret = render_template('displays/mutators.html',
                          mutators=sorted(extmodels.Mutator.all(),
                                          key=lambda m: len(m.game_ids),
                                          reverse=True),
                          rankings=rankings)
    return ret


@bp.route("/mutator/<string:name>")
@bp.route("/mutators/<string:name>")
def display_mutator(name):
    mutator = extmodels.Mutator.get_or_404(name)
    return render_template('displays/mutator.html', mutator=mutator)


@bp.route("/mutator:games/<string:name>")
def display_mutator_games(name):
    mutator = extmodels.Mutator.get_or_404(name)
    pager = models.Game.query.filter(
            models.Game.id.in_(mutator.game_ids)).order_by(
            models.Game.id.desc()).paginate(
            request.args.get("page", default=1, type=int),
            current_app.config['DISPLAY_RESULTS_PER_PAGE'])
    return render_template('displays/mutator_games.html', mutator=mutator,
                           pager=pager)


@bp.route("/weapons")
def display_weapons():
    games = (models.Game.query
             .with_entities(models.Game.id)
             .filter(db.func.re_normal_weapons(models.Game.id))
             .order_by(models.Game.id.desc()).limit(300))
    weapons = extmodels.Weapon.all_from_games(games)

    ret = render_template('displays/weapons.html',
                          weapons=weapons,
                          totalwielded=(models.GameWeapon.query
                                        .with_entities(db.func.sum(
                                            models.GameWeapon.timewielded))
                                        .filter(models.GameWeapon.game_id.in_(
                                            games
                                            ))
                                        .first()[0])
                          )
    return ret


@bp.route("/activehours")
def display_activehours():
    first_game = rankings.first_game_in_days(30)
    times = {}
    for game in (models.Game.query
                 .filter(models.Game.id >= first_game)):
        hour = int(templateutils.time_str(game.time, "%H"))
        if hour not in times:
            times[hour] = {
                "players": 0
            }
        times[hour]["players"] += 1
    barfactor = 100 / max([times[t]["players"] for t in times])
    for hour in times:
        times[hour]["hour"] = hour
        times[hour]["label"] = hour
        times[hour]["players"] = round(times[hour]["players"], 1)
        times[hour]["bar"] = "|" * round(times[hour]["players"] * barfactor)
    ret = render_template('displays/times.html',
                          days=30,
                          label="Hours",
                          times=sorted(times.values(),
                                       key=lambda k: k["hour"]))
    return ret


@bp.route("/activeweekdays")
def display_activeweekdays():
    first_game = rankings.first_game_in_days(90)
    times = {}
    for game in (models.Game.query
                 .filter(models.Game.id >= first_game)):
        dayidx = int(templateutils.time_str(game.time, "%u"))
        day = templateutils.time_str(game.time, "%a")
        if dayidx not in times:
            times[dayidx] = {
                "players": 0,
                "label": day,
            }
        times[dayidx]["players"] += 1
    barfactor = 100 / max([times[t]["players"] for t in times])
    for day in times:
        times[day]["day"] = day
        times[day]["players"] = round(times[day]["players"], 1)
        times[day]["bar"] = "|" * round(times[day]["players"] * barfactor)
    ret = render_template('displays/times.html',
                          days=90,
                          label="Weekdays",
                          times=sorted(times.values(), key=lambda k: k["day"]))
    return ret


@bp.route("/activeweekdayhours")
def display_activeweekdayhours():
    first_game = rankings.first_game_in_days(90)
    times = {}
    for game in (models.Game.query
                 .filter(models.Game.id >= first_game)):
        dayidx = int(templateutils.time_str(game.time, "%u"))
        day = templateutils.time_str(game.time, "%a")
        hour = int(templateutils.time_str(game.time, "%H"))
        idx = (dayidx, hour)
        if idx not in times:
            times[idx] = {
                "players": 0,
                "label": "%s %d" % (day, hour),
                "day": dayidx,
                "hour": hour,
            }
        times[idx]["players"] += 1
    barfactor = 100 / max([times[t]["players"] for t in times])
    for idx in times:
        times[idx]["players"] = round(times[idx]["players"], 1)
        times[idx]["bar"] = "|" * round(times[idx]["players"] * barfactor)
    ret = render_template('displays/times.html',
                          days=90,
                          label="Weekday Hours",
                          times=sorted(sorted(times.values(),
                                              key=lambda k: k["hour"]),
                                       key=lambda k: k["day"]))
    return ret


templateutils.setup(bp)
