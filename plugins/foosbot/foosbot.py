import json

from errbot import BotPlugin, botcmd, arg_botcmd, re_botcmd
from trueskill import Rating, rate


class Foosbot(BotPlugin):
    """ Foosbot """

    def finished_games(self):
        with open('./plugins/foosbot/finishedgames.json') as f:
            games = json.load(f)
            return games

    def save_game(self, result):
        with open('./plugins/foosbot/finishedgames.json', 'r+') as f:
            games = json.loads(f.read())
            games.append(result)
            f.seek(0)
            f.truncate(0)
            f.write(json.dumps(games))

    @staticmethod
    def retrieve_player_stats(stats, player):
        if player in stats:
            return stats[player]

        return {
                "gamesPlayed": 0,
                "gamesWon": 0,
                "winPercentage": 0,
                "skill": Rating(),
                "mu": 0,
                "sigma": 0,
                "rank": 2,
                "streak": 0,
                "longestWinStreak": 0,
                "longestLoseStreak": 0,
        }

    def stats(self):
        stats = {}

        for game in self.finished_games():
            t1p1 = game['team1']['player1']
            t1p2 = game['team1']['player2']
            t2p1 = game['team2']['player1']
            t2p2 = game['team2']['player2']

            t1score = game['team1']['score']
            t2score = game['team2']['score']

            all_players = [t1p1, t1p2, t2p1, t2p2]
            for player in all_players:
                stats[player] = self.retrieve_player_stats(stats, player)
                stats[player]['gamesPlayed'] += 1
                stats[player]['rank'] = 2

            winners = [t1p1, t1p2] if t1score > t2score else [t2p1, t2p2]
            losers = [t1p1, t1p2] if t1score < t2score else [t2p1, t2p2]

            for winner in winners:
                stats[winner]['gamesWon'] += 1
                stats[winner]['rank'] = 1

                stats[winner]['streak'] = 1 if stats[winner]['streak'] < 0 else stats[winner]['streak'] + 1
                if stats[winner]['streak'] > stats[winner]['longestWinStreak']:
                    stats[winner]['longestWinStreak'] = stats[winner]['streak']

            for loser in losers:
                stats[loser]['streak'] = -1 if stats[loser]['streak'] > 0 else stats[loser]['streak'] - 1
                if -stats[loser]['streak'] > stats[loser]['longestLoseStreak']:
                    stats[loser]['longestLoseStreak'] = -stats[loser]['streak']

            # TODO: trueskill adjust
            w1 = stats[winners[0]]['skill']
            w2 = stats[winners[1]]['skill']
            l1 = stats[losers[0]]['skill']
            l2 = stats[losers[1]]['skill']
            (w1, w2),(l1,l2) = rate([[w1,w2], [l1,l2]])
            stats[winners[0]]['skill'] = w1
            stats[winners[1]]['skill'] = w2
            stats[losers[0]]['skill'] = l1
            stats[losers[1]]['skill'] = l2
        for player in stats.keys():
            stats[player]['name'] = player
            stats[player]['winPercentage'] = round(stats[player]['gamesWon'] / stats[player]['gamesPlayed'] * 100, 2)
            stats[player]['trueskill'] = round(stats[player]['skill'].mu - (3 * stats[player]['skill'].sigma), 2)
            # From Wikipedia
            # Player ranks are displayed as the conservative estimate of their skill, R = μ − 3 × σ. This is conservative, because the system is 99% sure that the player's skill is actually higher than what is displayed as their rank.


            stats[player]['mu'] = round(stats[player]['skill'].mu, 2)
            stats[player]['sigma'] = round(stats[player]['skill'].sigma, 2)

        return stats

    def get_rankings(self):
        stats = self.stats()
        
        # remove retirees
        
        rankings = sorted(stats.items(), key=lambda player_stat: player_stat[1]['trueskill'], reverse=True)

        for i, player in enumerate(rankings):
            player[1]['rank'] = str(i+1)

        return rankings

    def noopFormat(self, s): return s
    def trueSkillFormat(self, s): return s
    def percentFormat(self, s): return "{}%    ".format(s)
    def gamesFormat(self, s): return "{} game{}".format(s, '' if s==1 else 's')
    def streakFormat(self, s): 
        winning = int(s) > 0
        return "{}{} {}".format("🔥" if winning else "💩", abs(int(s)), "won" if winning else "lost")

    def add_column(self, lines, stats, header, field, format_func=None, first_column=None):
        format_func = format_func or self.noopFormat
        longest_length = longest_header_length = len(header)
        
        for i, stat in enumerate(stats):
            field_value = format_func(stat[1][field]) if field != 'rank' else i
            longest_length = max(longest_length, len(str(field_value)))
            longest_header_length = max(longest_header_length, len(str(field_value)))

        longest_length += 1
        longest_header_length += 1

        # Add header and underline
        header_length = longest_header_length + 2
        lines[0] += header.ljust(header_length)
        lines[1] += '─' * header_length 
        
        # Add the column per stat
        for i, stat in enumerate(stats):
            field_value = format_func(str(stat[1][field])).ljust(longest_header_length)

            if not first_column:
                lines[2+i] += "| "

            lines[2+i] += field_value

    @botcmd
    def ranks(self, msg, args):
        rankings = self.get_rankings()

        response_list = [''] * (len(rankings)+2)
        self.add_column(response_list, rankings, "Rank", "rank", self.noopFormat, True)
        self.add_column(response_list, rankings, "Player", "name")
        self.add_column(response_list, rankings, "Trueskill", "trueskill", self.trueSkillFormat)
        self.add_column(response_list, rankings, "Mu", "mu", self.trueSkillFormat)
        self.add_column(response_list, rankings, "sigma", "sigma", self.trueSkillFormat)
        self.add_column(response_list, rankings, "Win %", "winPercentage", self.percentFormat)
        self.add_column(response_list, rankings, "Won", "gamesWon")
        self.add_column(response_list, rankings, "Played", "gamesPlayed")
        self.add_column(response_list, rankings, "Streak", "streak", self.streakFormat)
        self.add_column(response_list, rankings, "Longest Win Streak", "longestWinStreak", self.gamesFormat)
        self.add_column(response_list, rankings, "Longest Loss Streak", "longestLoseStreak", self.gamesFormat)

        output = "```"
        output += "\n\n".join(response_list)
        output += "```"

        return output

    @botcmd
    def start_game(self, msg, args):
        games = self['games']
        if not games:
            games = []

        games.append({
            "players": [msg.frm.username],
            "bets": {}
            }
        )
        self['games'] = games

        return self.games(None, None)

    def get_player(self, players, index):
        try:
            return players[index]
        except IndexError:
            return "_"

    @botcmd
    def games(self, msg, args):
        games = ""
        for i, game in enumerate(self['games']):
            games += ("Game {}:\n".format(i))
            games += ("{} and {}\n".format(self.get_player(game['players'], 0), self.get_player(game['players'], 1)))
            games += ("vs.\n")
            games += ("{} and {}\n".format(self.get_player(game['players'], 2), self.get_player(game['players'], 4)))

        if not self['games']:
            games = "No games started!"
        return games

    @botcmd
    def clear_games(self, msg, args):
        self['games'] = []
        return "All games have been cancelled!"

    @arg_botcmd('index', type=int, default=-1)
    def cancel_game(self, msg, index=None):
        games = self['games']
        if games:
            games.pop(index)
            yield "Game {} cancelled!".format(index)
            self['games'] = games

        return self.games(None, None)

    @arg_botcmd('game_index', type=int, default=0)
    def join_game(self, msg, game_index=0):
        self.add_player('', msg.frm.username, game_index)

    def get_rank(self, player, rankings):
        for stat in rankings:
            if player in stat:
                return stat[1]['rank']

    def balance(self, game):
        yield("BALANCER")
        rankings = self.get_rankings()
        players_with_ranks = [{"name": player,
                               "rank": self.get_rank(player, rankings)}
                              for player in game['players']]
        yield(players_with_ranks)
        return players_with_ranks

    @arg_botcmd('player', type=str)
    @arg_botcmd('--game', dest='game_index', type=int, default=0)
    def add(self, msg, player=None, game_index=None):
        if len(self['games'][game_index]['players']) == 4:
            return "Game full!"
        else:
            with self.mutable('games') as games:
                games[game_index]['players'].append(player)
            if len(games[game_index]['players']) == 4:
                p = self.balance(games[game_index])
                yield("FULL GAME")

            yield(len(games[game_index]['players']))
            return "{} joined game {}!".format(player, game_index)

    @arg_botcmd('player', type=str)
    @arg_botcmd('--game', dest='game_index', type=int, default=0)
    def kick(self, msg, player=None, game_index=None):
        with self.mutable('games') as games:
            games[game_index]['players'].remove(player)

        return "{} was removed from game {}".format(player, game_index)


    @arg_botcmd('score', type=str)
    def finish_game(self, msg, score):
        if not self['games']:
            return "No games started!"

        game = self['games'][0]
        gamePlayers = game['players']

        if len(gamePlayers) != 4:
            return "Next game isn't ready to go yet!"

        result = score.split('-')

        t1score = str(result[0])
        t2score = str(result[1])

        t1p1 = gamePlayers[0].lower()
        t1p2 = gamePlayers[1].lower()
        t2p1 = gamePlayers[2].lower()
        t2p2 = gamePlayers[3].lower()

        game_results = {
            'team1': {
                'player1': t1p1,
                'player2': t1p2,
                'score': t1score
            },
            'team2': {
                'player1': t2p1,
                'player2': t2p2,
                'score': t2score
            }
        }

        previous_ranks = self.get_ranks(t1p1, t1p2, t2p1, t2p2)
        yield(previous_ranks)
        self.save_game(game_results)
        new_ranks = self.get_ranks(t1p1, t1p2, t2p1, t2p2)
        yield(new_ranks)
        print( "CHANGED RANKINGS")
        yield(self.show_changed_rankings(previous_ranks, new_ranks))

        self['games'] = self['games'][1:]
        yield(self['games'])

        #payouts

#        save_accounts
#        save_finished_games
#        show_changed_rankings
#
#        remove game
#        save games
        yield "Results Saved!"

    def get_ranks(self, p1, p2, p3, p4):
        rankings = self.get_rankings()
        ranks = {
            p1: self.get_rank(p1, rankings),
            p2: self.get_rank(p2, rankings),
            p3: self.get_rank(p3, rankings),
            p4: self.get_rank(p4, rankings)
        }
        return ranks

    def show_changed_rankings(self, previous_ranks, new_ranks):
        changed_rankings = "Rank Changes: \n"
        for player, rank in new_ranks.items():
            rankDiff = int(rank) - int(previous_ranks[player])
            prefix = '' if rankDiff < 0 else '+' if rankDiff > 0 else '='
            changed_rankings += "{}{} -> {} {}\n".format(prefix, rankDiff, rank, player)

        return changed_rankings
