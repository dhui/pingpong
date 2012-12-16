import collections
from django.db import models

from src.utils import cached_property, flatten, isodd
from src.utils.exceptions import PingPongException


class Player(models.Model):
    name = models.CharField(max_length=64, unique=True)
    active = models.BooleanField(default=True)

    @cached_property
    def all_teams(self):
        return self.teams.all()


class Team(models.Model):
    players = models.ManyToManyField(Player, through="TeamMember", related_name="teams")

    @classmethod
    def get_or_create(cls, players):
        teams = [set(p.all_teams) for p in players]
        unique_teams = list(reduce(set.intersection, teams))
        if len(unique_teams) == 1:
            return unique_teams[0]
        elif len(unique_teams) > 1:
            raise PingPongException("Multiple teams with same players found: %s" % [t.id for t in unique_teams])
        team = Team.objects.create()
        TeamMember.objects.bulk_create((TeamMember(team=team, player=p) for p in players))
        return team

    @cached_property
    def all_players(self):
        return self.players.all()


class TeamMember(models.Model):
    player = models.ForeignKey(Player)
    team = models.ForeignKey(Team)


# TODO: Break out TeamPerf to individual PlayerPerf
class TeamPerf(models.Model):
    # TODO: have more detailed data about scoring and errors. i.e. different error types and more info about rallies
    score = models.SmallIntegerField()
    errors = models.SmallIntegerField()
    team = models.ForeignKey(Team)


class Series(models.Model):
    @classmethod
    def create(cls, matches):
        # Validation
        # need to have an odd # of matches so someone wins the series
        if not isodd(len(matches)):
            return

        # Only 2 teams allowed
        teams = set(flatten((m.winner, m.loser) for m in matches))
        if len(teams) != 2:
            return
        # Series can't already be set
        num_existing_series = sum((1 if m.series else 0 for m in matches))
        if num_existing_series:
            return

        series = Series.objects.create()
        Match.objects.filter(id__in=[m.id for m in matches]).update(series=series)

    @cached_property
    def winner(self):
        matches = self.matches.all()
        winners = collections.Counter((m.winner for m in matches))
        return winners.most_common(1)

    @cached_property
    def loser(self):
        matches = self.matches.all()
        losers = collections.Counter((m.loser for m in matches))
        return losers.most_common(1)


class Match(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    points_per_game = models.SmallIntegerField()
    winner_perf = models.OneToOneField(TeamPerf, related_name="matches_won")
    loser_perf = models.OneToOneField(TeamPerf, related_name="matches_lost")

    series = models.ForeignKey(Series, related_name="matches", null=True)

    @property
    def deuce(self):
        # Note: Winner of the match must win by 2 points. So any match with a point difference of less than 2 is a deuce
        return (self.winner_perf.score - self.loser_perf.score) == 1

    @property
    def winner(self):
        return self.winner_perf.team

    @property
    def loser(self):
        return self.loser_perf.team

    @property
    def teams(self):
        return [self.winner, self.loser]
