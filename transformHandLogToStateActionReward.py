import numpy as np
import pandas as pd
import constants
#import pymongo
import pprint
act_array = np.array(constants.act_array)

# from pymongo import MongoClient
# client = MongoClient('localhost', 27017)

# db = client.poker
# dfs = db.dataframes

# for df in dfs.find():
# 	# call the loop of the main function here
# 	pprint.pprint(df)
# 	hand_log = df

hand_log = pd.read_pickle("../fiveLogs.pickle")
final_state_layer = 1 # last state.
depth = constants.betRounds*(constants.max_raises)+ constants.player_consolidated_layer
depth_names = {"consol_layer":0, "first_act": 1, "first_flop_act":8, "first_turn_act":16,"first_river_act":24, "end_state":32}
height = constants.ranks
height_names = constants.cardRanks
width = (constants.num_suits + constants.players + constants.action_choice + \
	constants.size_of_action_to_stay_in_hand + constants.size_of_action_related_to_pot + \
	constants.size_of_pot +\
constants.size_of_stack + constants.size_of_opponent_stack+ constants.betting_round+ constants.raising_round)

suits = list(constants.suits.keys())
width_names = {"betting_round":0, "raise_round":1, "player":2, "suit0":3, \
"suit1":4, "suit2":5, "suit3":6,"action_choice":7,\
"size_of_action_to_stay_in_hand":8, "size_of_action_related_to_pot":9,\
"size_of_pot":10, "size_of_p0stack":11, "size_of_p1stack":12}

#repeat from constants.py
ante_steps = 3

#depth
betRounds = 4
max_raises = 4
dealer_action = 1 #for dealing moments
player_consolidated_layer = 1 #for giving the player the total hand and last action


#height
ranks = 13# suit, rank

action_choices = {"fold":0, "check": 1, "bet 0.22":2, "bet 0.35": 3,
"bet 0.5": 4, "bet 0.7": 5, "raise 1": 6,"bet 1.5":7, "bet 2.5":8,
"bet all":9}
action_rounding = {"2":0.22, "3":0.35, "4":0.5, "5": 0.7,"6":1, "7":1.5, "8":2.5, "9":5}

#width
num_suits = 4 #2s3h 1 at [0,0] and [1,2]. Only shown in layers when first action of the round.
players = 1 #flag for which player
action_choice = 1 #including ante flag - DO NOT NEED?
size_of_action_to_stay_in_hand = 1
size_of_action_related_to_pot = 1 #this number would be size_of_action_to_stay_in_hand / size_of_pot
size_of_pot = 1
size_of_stack = 1
size_of_opponent_stack = 1
betting_round = 1
raising_round = 1

blank_state = np.zeros((height, width, depth)) #cards , (max_raises, cost/action)
blank_layer = np.zeros((height,width))

chip_divider = 5

def binarize_num(num, width = 13):
	bin_str = np.binary_repr(num, width = width)
	return [int(c) for c in bin_str]

def bin_array_to_base10(bin_array):
	return np.sum(2**np.arange(len(bin_array))*bin_array) 

def depth_in_input_matrix(player_pos, bet_round, raise_round):
	return constants.player_consolidated_layer + bet_round*constants.max_raises + raise_round*2 + player_pos

def create_player_state_layer(betting_round, raising_round, player, cards, action_to, action_to_pot_size, pot_size, p0_stack, p1_stack, action):
	#create numpy array for one layer of the inputs, based on the state
	layer = np.copy(blank_layer)
	layer[betting_round, width_names["betting_round"]] = 1
	layer[raising_round, width_names["raise_round"]] = 1
	layer[player, width_names["player"]] = 1
	for card in cards:
		layer[card[0],card[1]+3] = 1
	
	if action:
		#set the action in this layer
		layer[action, width_names["action_choice"]] = 1
	layer[:,width_names["size_of_action_to_stay_in_hand"]] = binarize_num(int(action_to/chip_divider))
	layer[:,width_names["size_of_action_related_to_pot"]] = binarize_num(int(action_to_pot_size))
	layer[:,width_names["size_of_pot"]] = binarize_num(int(pot_size/chip_divider))
	layer[:,width_names["size_of_p0stack"]] = binarize_num(int(p0_stack/chip_divider))
	layer[:,width_names["size_of_p1stack"]] = binarize_num(int(p1_stack/chip_divider)) 
	#these could cause rounding problems during check.

	return layer

def create_entire_state(stepList, cardList):
	#step columns = ["bet round", "player_position", "raising round", "action", "size_to", "ante-flag"]
	#card columns=["bet round", "player_position", "rank", "suit"]
	#stepList, cardList = hand_log["Steps"][0], hand_log["Cards"][0]
	total_player_steps = len(stepList)
	entire_state = [] #the state when the hand is over

	player_stacks = np.zeros(2)
	player_commits = np.zeros(2)

	#first build entire_state which contains all action, then build player 0 episode and player 1 episode
	for step in range(3,total_player_steps):
		#get all these things to build one layer: betting_round, raising_round, player, cards, action_to,
		# action_to_pot_size, pot_size, stack, opp_stack, action
		betting_round = stepList[step][0]
		raising_round = stepList[step][2] 
		if betting_round == 0:
			raising_round = raising_round - 1 #for antes
		player = stepList[step][1]
		player_prior = stepList[step-1][1]
		size_to_current = stepList[step][4]
		size_to_prior = stepList[step-1][4]
		act_prior = stepList[step-1][3]

		if (betting_round == 0) & (player == 1) & (raising_round == 0):
			player_commits[1] = 50
			pot_size = 100 #initialize pot-size before action update

		#update pot, stacks, and player commitments for the prior action
		if size_to_prior == 0:
			action_to = 0 
		else:
			player_commits[player_prior] = size_to_prior
			player_stacks[player_prior] = constants.stack_sizes - player_commits[player_prior]
			pot_size = player_commits.sum()
			if act_prior == 'c':
				action_to = 0
			else:
				action_to = player_commits[player_prior] - player_commits[player]

		import pdb; pdb.set_trace()

		#redundant - need to remove these references
		# if (betting_round == 0) & (player == 1) & (raising_round == 0):
		# 	player_commits[0] = 50
		# 	p1_commit = 100
		# 	action_to = 50
		# 	pot_size = 150
		# 	p0_stack = constants.stack_sizes - p0_commit
		# 	p1_stack = constants.stack_sizes - p1_commit
		# elif (betting_round > 0) & (player == 0) & (raising_round == 0):
		# 	action_to = 0
		# else:
		# 	#not sure this works exactly, the cardList sie to is 0 for non incrementing steps and x where x is total 
		# 	#commitment by player for the hand.
		# 	act_bin = entire_state[step-1-3][:,width_names["size_of_action_to_stay_in_hand"]]
		# 	action_to = np.sum(2**np.arange(len(act_bin))*act_bin) 
		# 	action_to = action_to * chip_divider #why am I converting back and forth? should be a better way

		#cardList[bet round == betting_round & player_postion == player or -1 for community]
		#card columns=["bet round", "player_position", "rank", "suit"]
		# raising_round == 0 because that is first moment of seeing it
		
		#TODO: move card inputs out of step for loop and make card array beforehand. No need to loop through cards every time
		cards = [] #rank, suit
		if raising_round == 0 or (betting_round == 0 & raising_round == 1 & player == 0):
			for card in cardList:
				if ((card[0] == betting_round) and ((player == card[1]) or (card[1] == - 1))):
					cards.append(card[2:])

		action = -1 #action choice
		act_ = stepList[step][3]
		if act_ == 'f':
			action = 0
		elif (act_ == 'c' and action_to == 0):
	 		#only if size_to is bet size to you - check number
			action = 1 #check
		else:
			action_pot_frac = action_to/pot_size
			action = (np.abs(act_array - action_pot_frac).argmin()) + 2
			#then bet or raised
		action_to_pot_size = int((action_to / pot_size)*100)

		entire_state.append(create_player_state_layer(betting_round, raising_round, player, cards, action_to,\
			action_to_pot_size, pot_size, player_stacks[0], player_stacks[1], action))
		#at the end of this for loop we have the entire_state list of all the states in te ahand
		#now, we have to divide up the states into player 0 and player 1 episodes.
		#player 0, each game state is all layers at or below the current state. Zero out player 1's cards and the action chosen (because it can't know what it will choose)
	


	
	return entire_state
	
	#TODO1: function for parsing states to episodes
	# player0_episode = np.copy(blank_state) #only p0 actions and zero out player 1's Cards
	# player1_episode = np.copy(blank_state) #only p1 actions and zero out player 1's Cards
	# for frame in entire_state:

	#result = pd.DataFrame(columns = ["handId", "player_pos", "step","observation","action", "reward", "done"]) #observation = game state

result = create_episodes(hand_log["Steps"][0], hand_log["Cards"][0])
print("got hand result")
print(result)
import pdb; pdb.set_trace()

#old - trying to replace
def create_state_array(stepList, cardList):
    df_steps = pd.DataFrame(stepList, columns = ["bet round", "player_position",\
                                               "raising round", "action", "size_to", "ante-flag"])
    df_cards = pd.DataFrame(cardList, columns=["bet round", "player_position", "rank", "suit"])
    num_steps = df_steps[df_steps["ante-flag"]==0]["ante-flag"].count()
    num_players = df_steps.player_position.max() + 1
    player_pos = 0
    reward_to = 0
    arr = []
    num_steps = len(df_steps)
    #can I make the states an array with dimensions: [bet round, player, [action: raise round, action, size_to, ante-flag],
    # and [cards: rank,suit]]?
    for step in range(3, num_steps):
        player_pos = df_steps.iloc[step, 1]
        bet_round = df_steps.iloc[step,0]
        raise_round = df_steps.iloc[step, 2]
        known_actions = df_steps[df_steps.index < current_step]
        known_cards = df_cards[((df_cards["player_position"] == -1) | (df_cards["player_position"] == player_pos)) \
                       & (df_cards["bet round"] <= current_round)]
        done = step == num_steps - 1
        arr.append([player_pos, bet_round, raise_round, [known_actions, known_cards], reward_to, df_steps.iloc[step], done]) #TODO: figure out reward
    return arr #[player, bet round, [(state1, reward_transitioning_to, action, done)]]

handArr = create_state_array
result = [] #[hand_num, player, [state1, state2,..., state_end], [reward1, reward2,...., reward_end], [done1, don2, done3,..., done_end]]
print("end of file")
