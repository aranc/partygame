import os
import sys
import json
import random
import readline
from copy import deepcopy
from termcolor import colored
from icecream import ic

from RoomedAgent import RoomedAgent as Agent
from RoomedAgent import AutoRooms as Rooms
from SourceTracker import expose_to_agent

votes = {}
rooms = None
valid_vote_options = []
valid_voters = []
protected = None
queued_announce = None

grace = 1
def press_any_key_to_continue():
    global grace
    if grace > 0:
        grace -= 1
        return
    if True:
        input("Press Enter to continue...")

def queue_local_announcement(room, message, voice=None):
    global queued_announce
    assert queued_announce is None
    queued_announce = ('local', room, message, voice)

def queue_global_announcement(message):
    global queued_announce
    assert queued_announce is None
    queued_announce = ('global', message)

def clear_queued_announcement():
    global queued_announce
    if queued_announce is None:
        return
    if queued_announce[0] == 'local':
        room, message, voice = queued_announce[1:]
        if voice is None:
            print(colored(rooms.localAnnouncer(room, message), attrs=['reverse']))
        else:
            print(colored(rooms.localAnnouncer(room, message, voice=voice), attrs=['reverse']))
    else:
        assert queued_announce[0] == 'global'
        print(colored(rooms.globalAnnouncer(queued_announce[1]), attrs=['reverse']))
    queued_announce = None

class Player(Agent):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

    @expose_to_agent
    def vote(self, player):
        global votes, rooms, valid_vote_options, valid_voters

        if player not in valid_vote_options:
            return "invalid vote. available options are: " + ", ".join(valid_vote_options)

        previous_vote = votes.get(self.name, None)
        votes[self.name] = player

        room = rooms.where_is(self.name)
        if previous_vote is None:
            queue_local_announcement(room, f'{self.name} voted for {player}')
        else:
            queue_local_announcement(room, f'{self.name} changed vote from {previous_vote} to {player}')

        return "vote registered"

def shuffle(L):
    L = deepcopy(L)
    random.shuffle(L)
    return L

def main():
    # when transcribing, ignore system messages and whisper voices

    global rooms, votes, valid_vote_options, valid_voters

    colors = ["magenta", "cyan", "blue", "green", "red", "yellow"] + ["light_green", "light_blue", "light_magenta", "light_cyan"] + ["light_red", "light_yellow"]
    players = ["Alloy", "Echo", "Fable", "Onyx", "Nova", "Shimmer"] + ["Aqua", "Azure", "Cerulean", "Cobalt"] + ["Mint", "Sage"]

    citizens = ["Alloy", "Echo", "Fable"] + ["Aqua", "Azure", "Cerulean", "Cobalt"]
    doctor = ["Onyx"]
    mafia = ["Shimmer", "Nova"] + ["Mint", "Sage"]

    innocent = citizens + doctor
    agents = {player: Player(name=player) for player in players}
    rooms = Rooms(agents.values())
    rooms.set_save_file("mafia.json")
    colors_map = {player: color for player, color in zip(players, colors)}
    print(colors_map)
    
    print(colored(rooms.system(f"Welcome to AI game night! Today we're playing Mafia. The game is simple: there are {len(players)} players, {len(mafia)} of which {'are' if len(mafia) > 1 else 'is'} mafia and {len(doctor)} of which {'are' if len(doctor) > 1 else 'is'} the doctor. The mafia know each other, but the innocents don't know who the mafia are. The game is played in rounds. During each round, the doctor will choose a player to protect, the mafia will choose a player to eliminate. Only unprotected players will be eliminated by the mafia's vote. Then, all players will vote on who they think the mafia are. The player with the most votes will be eliminated. The game ends when either all the mafia are eliminated, or all the innocents are eliminated. If only one mafia and one innocent citizen are left, then the mafia wins. But if only one mafia and one doctor are left, then the citizens win. Good luck!"), attrs=['reverse']))
    print("==================================================")

    for player in players:
        rooms.dm(player, f"You are {player}. Remember that! you are a player, you will see other players in the chat inside user messages, and they will see you in the same format (you dont need to append you name to each message, it is appeneded automatically). dont speak for other players, dont speak for the announcer, only speak for yourself", voice="whisper")
        rooms.move(player, "day")

    print(colored(rooms.globalAnnouncer("Hello Players! before we begin assiging roles to each of you and starting the game, lets do a quick round of introductions for the audience. Please state your name and a single short fact about your name"), attrs=['reverse']))
    for player in players:
        message, func_call = rooms.chat(player)
        if message is not None:
            print(f"{player}: " + colored(message, colors_map[player]))
        if func_call is not None:
            print(colored(f"{player} called {func_call[0]} with arguments {func_call[1]}: ", "grey"), end="")
            res = rooms.call()
            print(colored(res, "grey"))
            clear_queued_announcement()

    print(colored(rooms.globalAnnouncer("Excellent, we will now continue to secretly reveal to each of you your secret role"), attrs=['reverse']))

    for player in citizens:
        rooms.dm(player, f"{player} you are a citizen. Your goal is to eliminate the mafia. You have no special abilities.", voice="whisper")

    assert len(doctor) == 1
    for player in doctor:
        rooms.dm(player, f"{player} you are the doctor. Each night, you may choose one player to protect. If the mafia choose to eliminate that player, they will be saved.", voice="whisper")

    for player in mafia:
        other_mafia_members = ", ".join([m for m in mafia if m != player])
        rooms.dm(player, f"MUHAHAHA! {player} you are mafia. Your goal is to eliminate the citizens. Each night, you may choose one player to eliminate. The other mafia members are: {other_mafia_members}", voice="whisper")

    def is_game_over():
        mafia_alive = [m for m in mafia if rooms.where_is(m) != "graveyard"]
        if len(mafia_alive) == 0:
            return "citizens_won"

        innocent_alive = [i for i in innocent if rooms.where_is(i) != "graveyard"]
        if len(innocent_alive) == 0:
            return "mafia_won"

        if len(mafia_alive) == 1 and len(innocent_alive) == 1:
            if innocent_alive[0] == doctor[0]:
                return "citizens_won"
            else:
                return "mafia_won"

        return False

    def is_vote_complete():
        global votes, valid_vote_options, valid_voters
        # if everybody has voted and there is no tie OR if there is a majority vote for a player, return (True, max_vote)
        # otherwise return (False, reason)

        # Create a mapping of who voted to kill which player
        vote_mapping = {player: [] for player in valid_vote_options}
        
        for voter, voted_for in votes.items():
            assert voted_for in vote_mapping
            vote_mapping[voted_for].append(voter)

        # Determine the maximal player(s)
        max_votes = 0
        max_voted_players = []

        for player, voters in vote_mapping.items():
            num_votes = len(voters)
            if num_votes > max_votes:
                max_votes = num_votes
                max_voted_players = [player]
            elif num_votes == max_votes:
                max_voted_players.append(player)

        # Check if there is a tie between the maximals
        if len(max_voted_players) > 1:
            # If everybody has voted, and there is a tie, return False
            if len([_ for _ in valid_voters if _ not in votes]) == 0:
                return (False, "there is a tie between the top-voted players and all players have voted, need to change some votes")

        # Get the maximal player
        maximal_player = max_voted_players[0]

        # Check if the maximal player has more than half of the votes
        total_voters = len(valid_voters)
        required_majority = (total_voters // 2) + 1

        if len(vote_mapping[maximal_player]) >= required_majority:
            assert len(max_voted_players) == 1
            return (True, maximal_player)

        # alternatively, if everybody has voted, since there is a clear majority, return the maximal player
        if len([_ for _ in valid_voters if _ not in votes]) == 0:
            return (True, maximal_player)

        return (False, "no clear majority, need more votes")

    def day(days_counter, allow_no_elimination=False):
        global votes, valid_vote_options, valid_voters

        rooms.log(f"Day {days_counter}")
        for player in players:
            if rooms.where_is(player) != "graveyard":
                rooms.move(player, "day")
        active = [p for p in players if rooms.where_is(p) == "day"]
        valid_vote_options = deepcopy(active)
        valid_voters = deepcopy(active)
        votes = {}

        print(colored(rooms.globalAnnouncer(f"Good morning! It's a new day! (day number {days_counter}). Still alive with us today are: {', '.join(active)}"), attrs=['reverse']))
        if allow_no_elimination:
            print(colored(rooms.localAnnouncer("day", "You have the option to choose to not eliminate anyone today. If you wish to do so, please vote 'no_elimination'"), attrs=['reverse']))
            valid_vote_options.append("no_elimination")

        counter = 10
        while is_vote_complete()[0] is False:
            counter -= 1
            for player in shuffle(active):
                if counter > 0:
                    message, func_call = rooms.chat(player)
                else:
                    message, func_call = rooms.chat(player, force_tools_usage=True)
                if message is not None:
                    print(f"{player}: " + colored(message, colors_map[player]))
                if func_call is not None:
                    print(colored(f"{player} called {func_call[0]} with arguments {func_call[1]}: ", "grey"), end="")
                    res = rooms.call()
                    print(colored(res, "grey"))
                    clear_queued_announcement()
                    print(votes)

                if is_vote_complete()[0]:
                    break

            _is_vote_complete, reason = is_vote_complete()
            if not _is_vote_complete:
                print(colored(rooms.localAnnouncer("day", "Reminder, The vote is not complete yet. Reason: " + reason, voice="whisper"), attrs=['reverse']))

        max_vote = is_vote_complete()[1]
        if max_vote == "no_elimination":
            assert allow_no_elimination
            print(colored(rooms.globalAnnouncer("The citizens have chosen to not eliminate anyone today"), attrs=['reverse']))
            return

        role = None
        if max_vote in mafia:
            role = "mafia"
        elif max_vote in doctor:
            role = "the doctor"
        else:
            role = "an innocent citizen"

        print(colored(rooms.globalAnnouncer(f"Player {max_vote} ({role}) has been voted out by the citizens"), attrs=['reverse']))
        rooms.move(max_vote, "graveyard")

    def night_doctor():
        global protected, rooms, votes, valid_vote_options, valid_voters
        protected = None

        assert len(doctor) == 1
        doc = doctor[0]

        if rooms.where_is(doc) == "graveyard":
            return

        rooms.log("Night - Doctor's turn")

        valid_voters = [doc]
        valid_vote_options = [p for p in players if rooms.where_is(p) != "graveyard"]
        votes = {}
        rooms.move(doc, "night")
        counter = 10
        while is_vote_complete()[0] is False:
            counter -= 1
            print(colored(rooms.localAnnouncer("night", f"{doc}, please choose a player to protect (vote for protection)"), attrs=['reverse']))
            if counter > 0:
                message, func_call = rooms.chat(doc)
            else:
                message, func_call = rooms.chat(doc, force_tools_usage=True)
            if message is not None:
                print(f"{doc}: " + colored(message, colors_map[doc]))
            if func_call is not None:
                print(colored(f"{doc} called {func_call[0]} with arguments {func_call[1]}: ", "grey"), end="")
                res = rooms.call()
                print(colored(res, "grey"))
                clear_queued_announcement()
                print(votes)

        protected = is_vote_complete()[1]
        print(colored(rooms.localAnnouncer("night", f"{doc} has chosen to protect {protected}"), attrs=['reverse']))
        rooms.move(doc, "day")

    def night_mafia():
        global votes, valid_vote_options, valid_voters, protected

        votes = {}

        # Find active mafia members
        active_mafia = [m for m in mafia if rooms.where_is(m) != "graveyard"]

        if not active_mafia:
            return  # No mafia left to vote

        rooms.log("Night - Mafia's turn")
        valid_voters = deepcopy(active_mafia)
        #valid_vote_options = [p for p in players if rooms.where_is(p) != "graveyard" and p not in mafia]
        valid_vote_options = [p for p in players if rooms.where_is(p) != "graveyard"]

        for mafia_member in active_mafia:
            rooms.move(mafia_member, "night")

        print(colored(rooms.localAnnouncer("night", f"Good evening mafia members! It's time to choose a player to eliminate. Current mafia members are: {', '.join(active_mafia)} and current valid vote options are: {', '.join(valid_vote_options)}"), attrs=['reverse']))

        counter = 10
        while is_vote_complete()[0] is False:
            counter -= 1
            for mafia_member in shuffle(active_mafia):
                if counter > 0:
                    message, func_call = rooms.chat(mafia_member)
                else:
                    message, func_call = rooms.chat(mafia_member, force_tools_usage=True)
                if message is not None:
                    print(f"{mafia_member}: " + colored(message, colors_map[mafia_member]))
                if func_call is not None:
                    print(colored(f"{mafia_member} called {func_call[0]} with arguments {func_call[1]}: ", "grey"), end="")
                    res = rooms.call()
                    print(colored(res, "grey"))
                    clear_queued_announcement()
                    print(votes)

                if is_vote_complete()[0]:
                    break

            _is_vote_complete, reason = is_vote_complete()
            if not _is_vote_complete:
                print(colored(rooms.localAnnouncer("night", "Reminder, The vote is not complete yet. Reason: " + reason, voice="whisper"), attrs=['reverse']))

        chosen_to_eliminate = is_vote_complete()[1]

        if chosen_to_eliminate == protected:
            print(colored(rooms.localAnnouncer("night", f"{chosen_to_eliminate} was protected and has survived the night!"), attrs=['reverse']))
            print(colored(rooms.dm(chosen_to_eliminate, f"{chosen_to_eliminate} you were protected by the doctor and have survived the night!"), attrs=['reverse']))
            print(colored(rooms.dm(doctor[0], f"{chosen_to_eliminate} was protected by you and has survived the night!"), attrs=['reverse']))

        else:
            print(colored(rooms.globalAnnouncer(f"{chosen_to_eliminate} has been eliminated by the mafia"), attrs=['reverse']))
            rooms.move(chosen_to_eliminate, "graveyard")

        for member in list(rooms.who("night")):
            rooms.move(member, "day")

    is_day = True
    days_counter = 1
    while not is_game_over():
        press_any_key_to_continue()
        if is_day:
            day(days_counter)
            days_counter += 1
        else:
            night_doctor()
            night_mafia()
        is_day = not is_day

    assert is_game_over() in ("citizens_won", "mafia_won")
    if is_game_over() == "citizens_won":
        print(colored(rooms.globalAnnouncer("The citizens have won! The mafia have been eliminated."), attrs=['reverse']))
        rooms.log("citizens_won")
    else:
        print(colored(rooms.globalAnnouncer("The mafia have won! The citizens have been eliminated."), attrs=['reverse']))
        rooms.log("mafia_won")

    print(colored(rooms.globalAnnouncer(f"Game Cast reveal. The doctor was {doctor[0]}. The mafia were: {', '.join(mafia)}"), attrs=['reverse']))
    print(colored(rooms.globalAnnouncer("Good game everyone! Any last words?"), attrs=['reverse']))
    for player in players:
        message, func_call = rooms.chat(player)
        if message is not None:
            print(f"{player}: " + colored(message, colors_map[player]))
        if func_call is not None:
            print(colored(f"{player} called {func_call[0]} with arguments {func_call[1]}: ", "grey"), end="")
            res = rooms.call()
            print(colored(res, "grey"))
            clear_queued_announcement()
    print(colored(rooms.globalAnnouncer("That is all than, see you next time, in AI game night, Mafia edition!"), attrs=['reverse']))

if __name__ == '__main__':
    main()
