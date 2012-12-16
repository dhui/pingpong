import simplejson as json

from django.db.models import Q
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic import View

from src.pingpong.constants import POSSIBLE_POINTS_PER_GAME
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
                if team["won_deuce"]:
                    perf.score = points_per_game
                else:
                    perf.score = points_per_game - 1
            team_proxies.append(TeamProxy(players, perf))

        # Score validation
        if data["deuce"]:
            # Only one team can win deuce
            if sum([1 if t.won_deuce else 0 for t in self.teams]) > 1:
                raise Http404("Only one team may win in deuce")
        # One team must have won
        if sum([1 if t.perf.score == points_per_game else 0 for t in team_proxies]) != 1:
            raise Http404("One team must win")


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
    matches = list(Match.objects.filter(Q(winner_perf__team__players=player)|Q(loser_perf__team__players=player)).order_by("-date"))
    matches_won = [m for m in matches if player in m.winner.all_players]
    matches_lost = [m for m in matches if player in m.loser.all_players]
    num_wins = len(matches_won)
    num_losses = len(matches_lost)
    streak = ""
    if matches:
        first_match = matches[0]
        verb = "losing"
        if player in first_match.winner.all_players:
            verb = "winning"
        streak_length = 1
        for match in matches[1:]:
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
    total_score = sum((m.winner_perf.score for m in matches_won)) + sum((m.loser_perf.score for m in matches_lost))
    total_errors = sum((m.winner_perf.errors for m in matches_won)) + sum((m.loser_perf.errors for m in matches_lost))
    error_rate = float(total_errors)/total_score if total_score else 0
    return render_to_response("player_matches.html", {"player": player, "num_wins": num_wins, "num_losses": num_losses, "streak": streak, "total_score": total_score, "total_errors": total_errors, "error_rate": error_rate, "matches": matches})
