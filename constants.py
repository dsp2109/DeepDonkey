
#cards
max_players = 10
num_players = 2
community_pool = 1 #might consider community cards as "dealer" along with pot
suits = 4
card_ranks = 13

#rounds
max_betting_rounds = 4 #pre-flop, flop, turn, river
max_raises = 4

#betting - won't see this in ACPC server text. Supposed to be known by program
small_blind = 50
big_blind = 100
min_raise = 100 #big blind or minimum of previous raise/bet in same round

stack_sizes = 20000 #could be a list for each player

hero = 0 #this is for one of the states, can also get the states for players up to num_players

path = '2017 ACPC logs example/'
# path = "/home/raghu/Downloads/processed_logs_2pn_2017/"

suits_1 = {'s':0 , 'h': 1, 'd': 2, 'c': 3}
cardRanks ={"2": 0, "3": 1, "4": 2, "5":3, "6":4, "A":5, "7":6, "8":7, "9":8, "T":9, "J":10, "Q":11, "K":12, "A": 13}

ante_steps = 3

#depth
betRounds = 4
max_raises = 4
dealer_action = 1 #for dealing moments
player_consolidated_layer = 1 #for giving the player the total hand and last action
ranks = 13# suit, rank

action_choices = {"fold":0, "check": 1, "bet 0.22":2, "bet 0.35": 3,
"bet 0.5": 4, "bet 0.7": 5, "raise 1": 6,"bet 1.5":7, "bet 2.5":8,
"bet all":9}
action_rounding = {"2":0.22, "3":0.35, "4":0.5, "5": 0.7,"6":1, "7":1.5, "8":2.5, "9":5}

#width
suits = 4 #2s3h 1 at [0,0] and [1,2]. Only shown in layers when first action of the round.
players = 1 #flag for which player
action_choice = 1 #including ante flag - DO NOT NEED?
size_of_action_to_stay_in_hand = 1
size_of_action_related_to_pot = 1 #this number would be size_of_action_to_stay_in_hand / size_of_pot
size_of_pot = 1
size_of_stack = 1
size_of_opponent_stack = 1
betting_round = 1
raising_round = 1
