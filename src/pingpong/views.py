import simplejson as json

from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic import View

from src.pingpong.constants import POSSIBLE_POINTS_PER_GAME
from src.pingpong.leader_board import LeaderBoard
from src.pingpong.models import Player, Team, TeamPerf, Match
from src.utils import render_to_json

def index(request):
    players = Player.objects.filter(active=True)
    return render_to_response("index.html", {"players": players, "POSSIBLE_POINTS_PER_GAME": POSSIBLE_POINTS_PER_GAME})

class Matches(View):
    def get(self, request, *args, **kwargs):
        matches = Match.objects.all().order_by("-date")
        return render_to_response("matches.html", {"matches": matches})

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        points_per_game = int(data["pointsPerGame"])

        # Basic validation
        if points_per_game not in POSSIBLE_POINTS_PER_GAME:
            raise Http404("Invalid points per game: %s" % points_per_game)
        if len(data["teams"]) != 2:
            raise Http404("Invalid # of teams: %s" % len(data["teams"]))

        class TeamProxy(object):
            """
            Proxy object for holding data used to create a team that participated in a match.
            """
            def __init__(self, players, perf):
                self.players = players
                self.perf = perf

        team_proxies = []

        for team in data["teams"]:
            players = Player.objects.filter(id__in=team["players"])
            if not players:
                raise Http404("No players found: %s" % team["players"])
            perf = TeamPerf(score=int(team["score"]), errors=int(team["errors"]))
            # Update the score for the deuce case
            if data["deuce"]:
                if team["wonDeuce"]:
                    perf.score = points_per_game
                else:
                    perf.score = points_per_game - 1
            team_proxies.append(TeamProxy(players, perf))

        # Score validation - one team must have won
        if sum((1 if t.perf.score == points_per_game else 0 for t in team_proxies)) != 1:
            raise Http404("One team must win")
        # Can't have more errors than another team's points
        for team in team_proxies:
            for other_team in team_proxies:
                if other_team == team:
                    continue
                if other_team.perf.score < team.perf.errors:
                    raise Http404("Errors must be less than opposing team's score")

        match = Match(points_per_game=points_per_game)
        for team_proxy in team_proxies:
            team = Team.get_or_create(team_proxy.players)
            team_perf = team_proxy.perf
            team_perf.team = team
            team_perf.save()
            if team_perf.score == points_per_game:
                match.winner_perf = team_perf
            else:
                match.loser_perf = team_perf
        match.save()

        return render_to_json({})


class Players(View):
    def get(self, request, *args, **kwargs):
        players = Player.objects.filter(active=True)
        return render_to_response("players.html", {"players": players})

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        name = data["name"]
        try:
            player = Player.objects.get(name=name)
            player.active = True
            player.save()
        except Player.DoesNotExist:
            player = Player.objects.create(name=name)
        return render_to_json({"id": player.id})

    def delete(self, request, *args, **kwargs):
        data = json.loads(request.body)
        player = Player.objects.get(id=data["id"])
        player.active = False
        player.save()
        return render_to_json({})

def player_matches(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    all_matches = list(Match.objects.all().order_by("-date"))
    player_matches = [m for m in all_matches if player in m.winner.all_players or player in m.loser.all_players]
    leader_board = LeaderBoard(all_matches)
    streak = ""
    if player_matches:
        first_match = player_matches[0]
        verb = "losing"
        if player in first_match.winner.all_players:
            verb = "winning"
        streak_length = 1
        for match in player_matches[1:]:
            if verb == "winning":
                if player in match.winner.all_players:
                    streak_length += 1
                else:
                    break
            else:
                if player in match.loser.all_players:
                    streak_length += 1
                else:
                    break

        streak = "You are on a %s game %s streak" % (streak_length, verb)
    return render_to_response("player_matches.html", {"player": player, "player_stats": leader_board.get_stats_for_player(player), "streak": streak, "matches": player_matches})


def leader_board(request):
    matches = Match.objects.all()
    leader_board = LeaderBoard(matches)
    return render_to_response("leader_board.html", {"leader_board": leader_board})
