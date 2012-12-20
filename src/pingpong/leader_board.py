import collections
from src.utils import cached_property


class PlayerStats(object):
    def __init__(self, wins=0, losses=0):

        self.wins = wins
        self.losses = losses

    @property
    def win_ratio(self):
        if not self.wins:
            return 0.0
        return float(self.wins) / (self.wins + self.losses)


class Leader(object):
    def __init__(self, player, player_stats):
        self.player = player
        self.player_stats = player_stats


class LeaderBoard(object):

    def __init__(self, matches):
        self.player_stats = collections.defaultdict(PlayerStats)

        for match in matches:
            for winner in match.winner.all_players:
                self.player_stats[winner].wins += 1
            for loser in match.loser.all_players:
                self.player_stats[loser].losses += 1

        print "init: %s" % self.player_stats

    @cached_property
    def players_to_leaders(self):
        return [Leader(ps[0], ps[1]) for ps in self.player_stats.iteritems()]

    @property
    def leaders_by_wins(self):
        return sorted(self.players_to_leaders, key=lambda l: l.player_stats.wins, reverse=True)

    @property
    def leaders_by_win_ratio(self):
        return sorted(self.players_to_leaders, key=lambda l: l.player_stats.win_ratio, reverse=True)
