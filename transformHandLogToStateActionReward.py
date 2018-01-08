import numpy as np
import pandas as pd
import constants
import pymongo
import pprint
#act_array = np.array(0.22,0.35,0.5,0.7,1,1.5,2.5,5)
"""
from pymongo import MongoClient
client = MongoClient('localhost', 27017)

db = client.poker
dfs = db.dataframes

for df in dfs.find():
	# call the loop of the main function here
	pprint.pprint(df)
	hand_log = df
"""
hand_log = pd.read_pickle("fiveLogs.pickle")

depth = constants.betRounds*(constants.max_raises)+ constants.player_consolidated_layer
depth_names = {"consol_layer":0, "first_act": 1, "first_flop_act":8, "first_turn_act":16,"first_river_act":24, "end_state":32}
height = constants.ranks
height_names = constants.cardRanks
width = (constants.suits + constants.players + constants.action_choice + constants.size_of_action_to_stay_in_hand + constants.size_of_action_related_to_pot + constants.size_of_pot +\
constants.size_of_stack + constants.size_of_opponent_stack+ constants.betting_round+ constants.raising_round)
width_names = {"betting_round":0, "raise_round":1, "player":2, constants.suits_1.keys()[0]:3, constants.suits_1.keys()[1]:4,\
constants.suits_1.keys()[2]:5, constants.suits_1.keys()[3]:6, "action_choice":7, "size_of_action_to_stay_in_hand":8, "size_of_action_related_to_pot":9,\
"size_of_pot":10, "size_of_stack":11, "size_of_opponent_stack":12}
blank_state = np.zeros((height, width, depth)) #cards , (max_raises, cost/action)
blank_layer = np.zeros((height,width))

def binarize_num(num, width = 13):
	bin_str = np.binary_rep(num, width = width)
	return [int(c) for c in bin_str]

def depth_in_input_matrix(player_pos, bet_round, raise_round):
	return player_consolidated_layer + bet_round*max_raises + raise_round*2 + player_pos

def create_player_state_layer(betting_round, raising_round, player, cards, action_to, action_to_pot_size, pot_size, stack, opp_stack, action):
	#create numpy array for one layer of the inputs, based on the state
	layer = blank_layer
	layer[betting_round, width_names["betting_round"]] = 1
	layer[raising_round, width_names["raise_round"]] = 1
	layer[player, width_names["player"]] = 1
	for card in cards:
		layer[card[1],card[0]+3] = 1
	if action:
		#set the action in this layer
		layer[action, width_names["action_choice"]] = 1
	layer[:,width_names["size_of_action_to_stay_in_hand"]] = binarize_num(action_to)
	layer[:,width_names["size_of_action_related_to_pot"]] = binarize_num(action_to_pot_size)
	layer[:,width_names["size_of_pot"]] = binarize_num(pot_size)
	layer[:,width_names["size_of_stack"]] = binarize_num(stack)
	layer[:,width_names["size_of_opponent_stack"]] = binarize_num(opp_stack)
	return layer

def create_episodes(stepList, cardList):
	#step columns = ["bet round", "player_position", "raising round", "action", "size_to", "ante-flag"]
	#card columns=["bet round", "player_position", "rank", "suit"]
	#stepList, cardList = hand_log["Steps"][0], hand_log["Cards"][0]
	total_player_steps = len(stepList)
	entire_state = [] #the state when the hand is over
	player0_episode = [] #only p0 actions and zero out player 1's Cards
	player1_episode = [] #only p1 actions and zero out player 1's Cards
	#first build entire_state which contains all action, then build player 0 episode and player 1 episode
	for step in range(total_player_steps):
			#get all these things to build one layer: betting_round, raising_round, player, cards, action_to,
			# action_to_pot_size, pot_size, stack, opp_stack, action
			betting_round = stepList[step][0]
			raising_round = stepList[step][2]
			player = stepList[step][1]
			#cardList[bet round == betting_round & player_postion == player or -1 for community]
			#card columns=["bet round", "player_position", "rank", "suit"]
			# raising_round == 0 because that is first moment of seeing it
			if raising_round == 0:
				cards = [] #rank, suit
				for card in cardList:
					if ((card[0] == betting_round) and ((player == card[1]) or (card[1] == - 1))):
						cards.append(card[2:])

			if (raising_round == 0) and (player == 0):
				if betting_round == 0:
					action_to = 50
				else:
					action_to = 0
			else:
				action_to = stepList[step-1][4]
			pot_size = pot_size + action_to
			action_to_pot_size = (action_to / pot_size)
			opp_stack = opp_stack - action_to
			#stack update your stack based on the action taken
			action = -1 #action choice
			act_ = stepList[step][3]
			if act_ == 'f':
				action = 0
			elif (act_ == 'c' and size_to == 0):
		 		#only if size_to is bet size to you - check number
				action = 1 #check
			else:
				action_pot_frac = size_to/pot_size
				action = (np.abs(constants.act_array - action_pot_frac).argmin()) + 2
				#then bet or raised
			entire_state.append(create_player_state_layer(betting_round, raising_round, player, cards, action_to, action_to_pot_size, pot_size, stack, opp_stack, action))
			#at the end of this for loop we have the entire_state list of all the states in te ahand
			#now, we have to divide up the states into player 0 and player 1 episodes.
			#player 0, each game state is all layers at or below the current state. Zero out player 1's cards and the action chosen (because it can't know what it will choose)
			stack = stack - size_to
	result = pd.Dataframe(columns = ["handId", "player_pos", "step","observation","action", "reward", "done"]) #observation = game state
create_episodes(hand_log["Steps"][0], hand_log["Cards"][0])

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
