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

suits = {'s':0 , 'h': 1, 'd': 2, 'c': 3}
cardRanks ={"2": 0, "3": 1, "4": 2, "5":3, "6":4, "A":5, "7":6, "8":7, "9":8, "T":9, "J":10, "Q":11, "K":12, "A": 13}
