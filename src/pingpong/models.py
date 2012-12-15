from django.db import models


class Player(models.Model):
    name = models.CharField(max_length=64, unique=True)
    active = models.BooleanField(default=True)


# TODO: Break out TeamPerf to individual PlayerPerf
class MatchTeamPerf(models.Model):
    # TODO: have more detailed data about scoring and errors. i.e. different error types and more info about rallies
    score = models.SmallIntegerField()
    errors = models.SmallIntegerField()


class MatchTeam(models.Model):
    perf = models.ForeignKey(MatchTeamPerf)
    players = models.ManyToManyField(Player, through="TeamMember", related_name="teams")


class TeamMember(models.Model):
    player = models.ForeignKey(Player)
    match_team = models.ForeignKey(MatchTeam)

    class Meta:
        unique_together = (("player", "match_team"),)


class Match(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    points_per_game = models.SmallIntegerField()
    winner = models.ForeignKey(MatchTeam, related_name="matches_won")
    loser = models.ForeignKey(MatchTeam, related_name="matches_lost")

    @property
    def deuce(self):
        # Note: Winner of the match must win by 2 points. So any match with a point difference of less than 2 is a deuce
        return (self.winner.perf.score - self.loser.perf.score) == 1

    @property
    def teams(self):
        return [self.winner, self.loser]
