import numpy as np
import pandas as pd
import constants
#import tensorflow

hand_log = pd.read_pickle("fiveLogs.pickle")
print("hand log loaded with shape: ", hand_log.shape)


import pdb;pdb.set_trace()
#Ok, now how do we represent the bet and card state?
# We have:
#- betting rounds (pre-flop, flop, turn, river = 0, 1 ,2 ,3)
#   - maximum raises per round (4 so [0, 1, 2 3])
#- players (0, 1, -1 for dealer) *until trying multiplayer
#   - cards
#      - action choice [r, c, f, collapse ante flag to this?]
#      - cost, which is negative of (reward - pot won if hand won)
#

ante_steps = 3

#depth
betRounds = 4
max_raises = 4
dealer_action = 1 #for dealing moments
player_consolidated_layer = 1 #for giving the player the total hand and last action
depth = betRounds*(max_raises)+ player_consolidated_layer
depth_names = {"consol_layer":0, "first_act": 1, "first_flop_act":8, "first_turn_act":16,"first_river_act":24, "end_state":32}


#height. I think I may use the 13 ranks as binary to represent size np.binary_rep(num, width = 13)
ranks = 13# suit, rank
height = ranks
height_names = constants.cardRanks

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

width = (suits + players + action_choice + size_of_action_to_stay_in_hand + size_of_action_related_to_pot + size_of_pot +\
size_of_stack + size_of_opponent_stack+ betting_round+ raising_round)
width_names = {"betting_round":0, "raise_round":1, "player":2, constants.suits.keys()[0]:3, constants.suits.keys()[1]:4,\
constants.suits.keys()[2]:5, constants.suits.keys()[3]:6, "action_choice":7, "size_of_action_to_stay_in_hand":8, "size_of_action_related_to_pot":9,\
"size_of_pot":10, "size_of_stack":11, "size_of_opponent_stack":12}


blank_state = np.zeros((height, width, depth)) #cards , (max_raises, cost/action)
blank_layer = np.zeros((height,width))
print("input state shape is ", blank_state.shape)


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
	layer[None,width_names["size_of_opponent_stack"]] = binarize_num(opp_stack)

	return layer

def create_episodes(handDf):
	#step columns = ["bet round", "player_position", "raising round", "action", "size_to", "ante-flag"]
	#card columns=["bet round", "player_position", "rank", "suit"]
	stepList, cardList = hand_log["Steps"][0], hand_log["Cards"][0]


	handDf["total_player_steps"] = handDf["Steps"].apply(len)
	handDf["entire_state"] = None #the state when the hand is over
	handDf["player0_episode"] = None #only p0 actions and zero out player 1's Cards
	handDf["player1_episode"] = None #only p1 actions and zero out player 1's Cards



	#handDf["player0_steps"] = (handDf.loc[(handDf["Steps"][1] == 0) & (handDf["Steps"][5] == 0), "Steps"].apply(len) # RAGHU - does this work?
	#handDf["player1_steps"] = handDf.loc[(handDf["Steps"][1] == 1) & (handDf["Steps"][5] == 0), "Steps"].apply(len)
	#layer_depth = depth_in_input_matrix(player_pos, bet_round, raise_round)
	result = pd.Dataframe(columns = ["handId", "player_pos", "step","observation","action", "reward", "done"]) #observation = game state
	#deleted for loop - was meant to run over the 2 players and over however many steps

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
#for hand in hand_log:

handArr = create_state_array

result = [] #[hand_num, player, [state1, state2,..., state_end], [reward1, reward2,...., reward_end], [done1, don2, done3,..., done_end]]

import pdb; pdb.set_trace()
print("end of file")
