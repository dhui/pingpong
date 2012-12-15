import simplejson as json

from django.db.models import Q
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic import View

from src.pingpong.constants import POSSIBLE_POINTS_PER_GAME
from src.pingpong.models import Player, MatchTeamPerf, MatchTeam, TeamMember, Match
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
            perf = MatchTeamPerf(score=int(team["score"]), errors=int(team["errors"]))
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
            match_team_perf = team_proxy.perf
            match_team_perf.save()
            match_team = MatchTeam(perf=match_team_perf)
            match_team.save()
            team_members = (TeamMember(match_team=match_team, player=p) for p in team_proxy.players)
            TeamMember.objects.bulk_create(team_members)
            if match_team_perf.score == points_per_game:
                match.winner = match_team
            else:
                match.loser = match_team
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
    matches = Match.objects.filter(Q(winner__players=player)|Q(loser__players=player))
    return render_to_response("matches.html", {"matches": matches})
