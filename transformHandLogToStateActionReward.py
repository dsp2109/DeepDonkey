import numpy as np
import pandas as pd
import constants
#import pymongo
import pprint

act_array = np.array(constants.act_array)

from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.poker
dfs = db.dataframes
count = 0
#hand_log = pd.read_pickle("fiveLogs.pickle")

def run_iteration(hand_log):
	try:
		final_state_layer = 1 # last state.
		depth = constants.betRounds*(constants.max_raises)
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
		"size_of_action":8, "size_to_stay_in_hand":9,\
		"size_of_pot":10, "size_of_p0stack":11, "size_of_p1stack":12}

		#repeat from constants.py
		ante_steps = 3
		#depth
		betRounds = 4
		max_raises = 4
		player_consolidated_layer = 1 #for giving the player the total hand and last action
		#height
		ranks = 13# suit, rank
		#width
		num_suits = 4 #2s3h 1 at [0,0] and [1,2]. Only shown in layers when first action of the round.
		players = 1 #flag for which player
		action_choice = 1 #including ante flag - DO NOT NEED?
		#size_of_action = 1
		size_to_stay_in_hand = 1
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
			return np.sum(2**np.arange(len(bin_array))*bin_array[::-1])

		def depth_in_input_matrix(player_pos, bet_round, raise_round):
			return bet_round*constants.max_raises + raise_round*2 + player_pos - (bet_round == 0)*1

		def create_player_state_layer(betting_round, raising_round, player, cards, action, size_of_action, action_to,\
			pot_size, p0_stack, p1_stack):
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
			layer[:,width_names["size_of_action"]] = binarize_num(int(size_of_action/chip_divider))
			layer[:,width_names["size_to_stay_in_hand"]] = binarize_num(int(action_to/chip_divider))
			layer[:,width_names["size_of_pot"]] = binarize_num(int(pot_size/chip_divider))
			layer[:,width_names["size_of_p0stack"]] = binarize_num(int(p0_stack/chip_divider))
			layer[:,width_names["size_of_p1stack"]] = binarize_num(int(p1_stack/chip_divider))
			#these could cause rounding problems during check.

			return layer


		def create_entire_state(stepList, cardList, result):
			#step columns = ["bet round", "player_position", "raising round", "action", "size_to", "ante-flag"]
			#card columns=["bet round", "player_position", "rank", "suit"]
			#stepList, cardList = hand_log["Steps"][0], hand_log["Cards"][0]
			total_player_steps = len(stepList)
			entire_state = [] #the state when the hand is over

			player_stacks = np.zeros(2)
			player_commits = np.zeros(2)

			obs = [[],[]]
			acts = [[],[]]
			rew = [[],[]]
			done = [[],[]]
			all_state = np.copy(blank_state)
			layer_depth = []

			for i in range(len(cardList)):
				if cardList[i][2] == 5:
					cardList[i][2] == 12
				elif cardList[i][2] > 5:
					cardList[i][2] -= 1
				#TODO: logparser error - bad fix

			#build entire_state which contains all action, then build player 0 episode and player 1 episode
			for step in range(3,total_player_steps):
				#get all these things to build one layer: betting_round, raising_round, player, cards, action_to,
				# action_to_pot_size, pot_size, stack, opp_stack, action

				#####
				betting_round = stepList[step][0]
				raising_round = stepList[step][2]
				if betting_round == 0:
					raising_round = raising_round - 1 #for antes
				player = stepList[step][1]
				not_player = (player + 1) % 2
				size_to_current = stepList[step][4]

				if step == 3: #first player action
					#initialize
					player_commits[1] = 50
					player_commits[0] = 100
					pot_size = 150
					player_stacks = constants.stack_sizes - player_commits
					action_to = 50
					if stepList[step][3] == 'c':
						size_to_current = 100
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
					size_of_action = 0
				elif (act_ == 'c'):
			 		#only if size_to is bet size to you - check number
					action = 1 #check
					size_of_action = action_to
				else:
					size_of_action = size_to_current - player_commits[player]
					action_vs_pot = size_of_action / pot_size
					action = (np.abs(act_array - (action_vs_pot)).argmin()) + 2

				new_layer = create_player_state_layer(betting_round, raising_round, player, cards, action, size_of_action,\
					action_to, pot_size, player_stacks[0], player_stacks[1])
				entire_state.append(np.copy(new_layer))

				layer_depth.append(depth_in_input_matrix(player, betting_round, raising_round))

				all_state[:,:,layer_depth[-1]] = np.copy(new_layer)

				new_obs_ep = np.copy(all_state)
				new_obs_ep[:,[7,8],layer_depth[-1]] = 0
				if player == 0:
					new_obs_ep[:,range(3,7),0] = 0
				else:
					new_obs_ep[:,range(3,7),1] = 0
				obs[player].append(new_obs_ep)
				acts[player].append(action)
				rew[player].append(-size_of_action)
				done[player].append(False) #will make True for last one

				#update pot, stacks, and player commitments for the action
				if size_to_current == 0:
					action_to = 0
				else:
					player_commits[player] = size_to_current
					player_stacks[player] = constants.stack_sizes - player_commits[player]
					pot_size += size_of_action
					if act_ == 'c':
						action_to = 0
					else:
						action_to = player_commits[player] - player_commits[not_player]
			#FOR LOOP DONE, and Player states created!
			#just need to add the the clean up for the last round and check that the states are correct for each player
			if done[0] == []:
				done[1][-1] = True
				obs[1].append(all_state)
			else:
				done[0][-1] = True
				done[1][-1] = True
				#append final obs
				obs[0].append(all_state)
				obs[1].append(all_state)

				if result[0] > 0:
					rew[0][-1] += pot_size
				elif result[0] == 0:
					rew[0][-1] += pot_size/2
					rew[1][-1] += pot_size/2
				else:
					rew[1][-1] += pot_size

				if not (result[0] + 100 == sum(rew[0])) & (result[1] + 50 == sum(rew[1])):
					print("RESULT DOES NOT MATCH REWARD")
					import pdb; pdb.set_trace()

			return obs, acts, rew, done, [len(rew[0]),len(rew[1])]
		result = create_entire_state(hand_log["steps"][11], hand_log["cards"][11], hand_log["result"][11])
		test = []
		for i in range(1000):
			try:
				test.append(create_entire_state(hand_log["steps"][i], hand_log["cards"][i], hand_log["result"][i]))
				print("hand worked ", str(i))
			except:
				pass
		df = pd.DataFrame(data = test, columns = ["obs", "acts", "reward", "done", "num_steps"])
		#df.to_pickle("../test_episodes1000.pickle")
		print("file complete, hands saved")
		#import pdb;pdb.set_trace()
		return df
	except Exception as e:
		import pdb;pdb.set_trace()
		print ("Failed with exception: "+ str(e))

for df in dfs.find():
	# call the loop of the main function here
	pprint.pprint(df)
	print ("Filecount: " + str(count))
	count += 1
	hand_log = df
	output_df = run_iteration(hand_log)
	db.outputs.insert(output_df)
