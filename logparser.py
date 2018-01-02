import os
import numpy as np
import constants
import pandas,re
import pymongo
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client.poker
collection = db.dataframes


def parse_betting_round(action_string):
    split_string = re.split('([r,c,f])',action_string)
    return filter(None,split_string)

def bet_lists(br_list):
    act = []
    size_to = 0
    round_actions = []
    for a in br_list:
        if a == 'c':
            act = ['c', size_to]
            round_actions.append(act)
            act = []
        elif a == 'f':
            round_actions.append(['f', 0])
        elif a == 'r':
            act = ['r']
        elif a.isdigit():
            size_to = int(a)
            act.append(size_to)
            round_actions.append(act)
            act = []
    return round_actions

def split_cards(card_str):
    #example is 'Jd5c|Js8h/Qd6hQh/3c'
    s = card_str.split('|')
    s = [s[0]]+  s[1].split('/')
    return s

def card_to_nums(card):
    # returns rank, suit
    return [constants.cardRanks[card[0]], constants.suits[card[1]]]

def split_by_card(card_glob):
    result = []
    for i in range(0, len(card_glob), 2):
        result.append(card_glob[i:i+2])
    return result

def parse_cards(card_str):
    #splits cards and returns cards by [round, player, rank, suit] where for now community player = -1
    cards = []
    card_list = split_cards(card_str)
    temp = [card_to_nums(x) for x in split_by_card(card_list[0])]
    cards.append([0,0] + temp[0])
    cards.append([0,0] + temp[1])
    temp = [card_to_nums(x) for x in split_by_card(card_list[1])]
    cards.append([0,1] + temp[0])
    cards.append([0,1] + temp[1])

    if len(card_list) > 2:
        for i in range(2,len(card_list)):
            temp = [card_to_nums(x) for x in split_by_card(card_list[i])]
            [cards.append([i-1,-1] + x) for x in temp]
    return cards

def parse_handLog_line(line):
    try:
        #line = "STATE:1:r223c/cr383c/r1516f:Jd5c|Js8h/Qd6hQh/3c:383|-383:PokerCNN_2pn_2017|Intermission_2pn_2017"
        player_pos = [] #player name and player position
        actions = [] #action = [round, player_position, betting round, ante-flag]
        cards = [] # cards = [round, player_position, rank, suit]
        result = [] # result, to be used to check against function that calcs rewards -
        parts = line.split(':')
        #print(parts)
        #['STATE', '1', 'r223c/cr383c/r1516f', 'Jd5c|Js8h/Qd6hQh/3c', '383|-383', 'PokerCNN_2pn_2017|Intermission_2pn_2017\n']
        #player position, earlier in list means first to act
        player_pos = parts[-1].split('|') #['PokerCNN_2pn_2017', 'Intermission_2pn_2017']
        result = parts[-2].split('|') # ['383','-383']
        try:
            result = [int(i) for i in result]
        except:
            return None
        cards = parse_cards(parts[3])
        actions_by_round = parts[2].split('/') #['r223c', 'cr383c', 'r1516f']
        #action = [bet round, player_position, raising round, action, size_to, ante-flag]
        #note that in first round for heads up, the positions reverse.
        #essentially, antes are like a forced betting round: cr50r100, then go.
        #Add a few betting rounds for antes?
        ante_action1 = [0, 0, 0,'c',0, 1] # start hand
        ante_action2 = [0, 1, 0,'r',50, 1] #small blind
        ante_action3 = [0, 0, 1,'r', 100, 1] #big blind
        actions = [ante_action1, ante_action2, ante_action3]
        no_players = len(player_pos)
        #for each action
        rd = 0
        acting_player = 1
        size_to = 100
        bet_rd = 0
        for betting_round in actions_by_round:
            if bet_rd == 0: raise_rd = 1
            else: raise_rd = 0  # which turn of betting it is (4 max)
            round_actions = [] #to store actions each round
            act = []
            betL = bet_lists(parse_betting_round(betting_round))
            for bet in betL:
                act = [bet_rd, acting_player, raise_rd, bet[0], bet[1], 0]
                if acting_player == no_players - 1:
                    raise_rd += 1
                    acting_player = 0
                else: acting_player += 1
                round_actions.append(act)
            [actions.append(i) for i in round_actions]
            bet_rd +=1
            acting_player = 0
        return player_pos, actions, cards, result
    except Exception as e:
        print "Failed with exception as " + str(e)
        return None

def get_data_frame():
    df = pandas.DataFrame(columns=['Players', 'Steps', 'Cards', 'Result'])
    listing = os.listdir(constants.path)
    count = 0
    for infile in listing:
        print "current file is: " + infile
        f = open(constants.path + infile, "r") #
        lines = f.readlines()
        for line in lines:
            if line[0:5]=="STATE":
                result = parse_handLog_line(line.strip())
                if result != None:
                    #df.loc[count] = [result[0], result[1], result[2], result[3]]
                    data_f ={"file_name" : infile+"STATE"+str(count+1) }
                    data_f["players"] = result[0]
                    data_f["steps"] = result[1]
                    data_f["cards"] = result[2]
                    data_f["result"] = result[3]
                    post_id = collection.insert_one(data_f).inserted_id
                    print "Saved data frame in mongo for filename " + infile+"STATE"+str(count+1)
                    count += 1
        f.close()
    return df

get_data_frame()
