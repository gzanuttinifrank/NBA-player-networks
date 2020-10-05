import pandas as pd # don't need for app
from bs4 import BeautifulSoup, Comment # don't need for app
import requests # don't need for app
import re # don't need for app
from datetime import date # don't need for app
from collections import OrderedDict # don't need for app
import pickle
from collections import deque
import os
from time import time
import sys


def save_dict(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name):
    try:
        with open(name + '.pkl', 'rb') as f:
            return pickle.load(f)
    except:
        with open(os.path.join(sys._MEIPASS, name+'.pkl'), 'rb') as f:
            return pickle.load(f)

def padded_input(message):
    txt = input(message+'\n')
    print('')
    if txt == 'exit':
        sys.exit()
    return txt


def create_dict():
    leagues = {'BAA':list(range(1947,1950)), 'ABA':list(range(1968,1977)), 'NBA':list(range(1950,2020))}

    lg_yr_abbrevs = {}
    tm_abbrs_names = {}

    # Create dict (lg_yr_abbrevs) with key being a league year (eg. NBA_2019) and value a list of abbreviations of all teams that participated in that league year
    # Create dict (tm_abbrs_names) mapping a league year team (NBA_2019_ATL) to a full name (Atlanta Hawks)

    for lg in list(leagues.keys()):
        for yr in leagues[lg]:
            lg_url = 'https://www.basketball-reference.com/leagues/' + lg + '_' + str(yr) + '.html'
            lgpage = requests.get(lg_url)
            lgsoup = BeautifulSoup(lgpage.content, 'html.parser')
            for comments in lgsoup.findAll(text=lambda text:isinstance(text, Comment)):
                curr_com = comments.extract()
                if '<table class="sortable stats_table" id="team-stats-per_game"' in curr_com:
                    stat_table = curr_com
            yr_abbrs = []
            abbr_matches = re.findall('<a href="/teams/[A-Z]+', stat_table)
            name_matches = re.findall('<a href="/teams/[A-Z]+/[0-9]+.html">[A-z .0-9-/]+', stat_table)
            for i in range(len(abbr_matches)):
                tm_abbrs_names[lg+'_'+str(yr)+'_'+abbr_matches[i][-3:]] = name_matches[i].split('>')[1]
                yr_abbrs.append(abbr_matches[i][-3:])

            lg_yr_abbrevs[lg+'_'+str(yr)] = yr_abbrs


    team_player_dict = {}
    player_team_dict = {}
    player_id_dict = {}

    # team_player_dict maps a team abbreviation to a list of player IDs for all players who recorded stats on that team throughout the whole year
    # player_team_dict maps a player ID to a list of all league year teams that he played on (eg. [NBA_2018_ATL, NBA_2019_ATL])
    # player_id_dict maps a player ID to a list with three elements: the player's full name (without special characters), the number of different league year teams he has played on, and the most recent year in which he was active

    base_url = 'https://www.basketball-reference.com/teams/'
    letter_replace_dict = {'ë':'e', 'ș':'s', 'ı':'i', 'ç':'c', 'ş':'s', 'ð':'d', 'ô':'o', 'ē':'e', 'Ó':'O', 'ü':'u', 'á':'a', 'ö':'o', 'ņ':'n', 'š':'s', 'Ž':'Z', 'Á':'A', 'ğ':'g', 'Đ':'D', 'ć':'c', 'İ':'I', 'ï':'i', 'ß':'ss', 'č':'c', 'Ö':'O', 'é':'e', 'ý':'y', 'Č':'C', 'đ':'d', 'Š':'S', 'ä':'a', 'ó':'o', 'í':'i', 'ú':'u', 'Ć':'C', 'ř':'r', 'ń':'n', 'ã':'a', 'ž':'z', 'ê':'e', 'ā':'a', 'è':'e', 'ū':'u', 'ģ':'g', 'ò':'o'}

    for key in list(lg_yr_abbrevs.keys()):
        lg, yr = key.split('_')
        for team_abbrev in lg_yr_abbrevs[key]:
            url = base_url + team_abbrev + '/' + yr + '.html'
            team_id = lg+'_'+str(yr)+'_'+team_abbrev

            page = requests.get(url)
            soup = BeautifulSoup(page.content, 'html.parser')
            try:
                roster = soup.find(id='roster').prettify()
                pergame_roster = soup.find(id='per_game').prettify()
            except:
                try:
                    commented_table = list(filter(None, [comm if 'id=\"per_game\"' in comm else None for comm in soup.findAll(text = lambda text: isinstance(text, Comment))]))[0]
                    comment_soup = BeautifulSoup(commented_table, 'html.parser')
                    pergame_roster = comment_soup.find(id='per_game').prettify()
                except:
                    print("ERROR: Cannot find", yr, "rosters.")
                    raise ValueError('A very specific bad thing happened.')

            players = pd.read_html(roster)[0]['Player']
            pergame_players = pd.read_html(pergame_roster)[0]['Unnamed: 1']
            players_full = list(OrderedDict.fromkeys(list(pd.concat([players, pergame_players]).apply(lambda pl: pl.replace('(TW)','').strip()))))
            players_full = [''.join(letter_replace_dict.get(ch, ch) for ch in name) for name in players_full]
            pl_ids = list(OrderedDict.fromkeys(re.findall('<a href="/players/[a-z]/[a-z]+[0-9]+', roster)))
            pl_ids_pergame = list(OrderedDict.fromkeys(re.findall('<a href="/players/[a-z]/[a-z]+[0-9]+', pergame_roster)))
            pl_ids_full = list(OrderedDict.fromkeys(pl_ids+pl_ids_pergame))
            pl_ids_clean = []

            for i in range(len(pl_ids_full)):
                plid = pl_ids_full[i].split('/')[-1]
                pl_ids_clean.append(plid)
                if plid in player_team_dict:
                    player_team_dict[plid].append(team_id)
                    player_id_dict[plid][1] += 1
                    player_id_dict[plid][2] = yr
                else:
                    player_team_dict[plid] = list([team_id])
                    pl_info = [players_full[i]]
                    pl_teams = player_team_dict[plid]
                    pl_info.append(len(pl_teams))
                    pl_info.append(yr)
                    player_id_dict[plid] = pl_info

            team_player_dict[team_id] = pl_ids_clean
        print(key)

    team_player_dict['latest'] = int(yr)

    save_dict(team_player_dict, 'team_player_dict')
    save_dict(player_team_dict, 'player_team_dict')
    save_dict(player_id_dict, 'player_id_dict')
    save_dict(lg_yr_abbrevs, 'lg_yr_abbrevs')
    save_dict(tm_abbrs_names, 'tm_abbrs_names')



# Updates the five dictionaries with new season(s) if available from basketball-reference.com
def update_dict(team_player_dict, player_team_dict, player_id_dict, lg_yr_abbrevs, tm_abbrs_names):
    today = date.today()
    if today.month < 10:
        endyear = today.year
    else:
        endyear = today.year+1

    latest_yr = team_player_dict['latest']
    if endyear > latest_yr:
        # update dict
        lg = 'NBA'
        letter_replace_dict = {'ë':'e', 'ș':'s', 'ı':'i', 'ç':'c', 'ş':'s', 'ð':'d', 'ô':'o', 'ē':'e', 'Ó':'O', 'ü':'u', 'á':'a', 'ö':'o', 'ņ':'n', 'š':'s', 'Ž':'Z', 'Á':'A', 'ğ':'g', 'Đ':'D', 'ć':'c', 'İ':'I', 'ï':'i', 'ß':'ss', 'č':'c', 'Ö':'O', 'é':'e', 'ý':'y', 'Č':'C', 'đ':'d', 'Š':'S', 'ä':'a', 'ó':'o', 'í':'i', 'ú':'u', 'Ć':'C', 'ř':'r', 'ń':'n', 'ã':'a', 'ž':'z', 'ê':'e', 'ā':'a', 'è':'e', 'ū':'u', 'ģ':'g', 'ò':'o'}
        for yr in range(latest_yr+1, endyear+1):
            print("Updating with", str(yr), "rosters.")
            # get abbrevs
            lg_url = 'https://www.basketball-reference.com/leagues/' + lg + '_' + str(yr) + '.html'
            lgpage = requests.get(lg_url)
            if lgpage.status_code == 404:
                print(str(yr) + " rosters not yet available.")
                return team_player_dict, player_team_dict, player_id_dict, lg_yr_abbrevs, tm_abbrs_names
            lgsoup = BeautifulSoup(lgpage.content, 'html.parser')
            for comments in lgsoup.findAll(text=lambda text:isinstance(text, Comment)):
                curr_com = comments.extract()
                if '<table class="sortable stats_table" id="team-stats-per_game"' in curr_com:
                    stat_table = curr_com
                    break
            yr_abbrs = []
            abbr_matches = re.findall('<a href="/teams/[A-Z]+', stat_table)
            name_matches = re.findall('<a href="/teams/[A-Z]+/[0-9]+.html">[A-z .0-9-/]+', stat_table)
            for i in range(len(abbr_matches)):
                tm_abbrs_names[lg+'_'+str(yr)+'_'+abbr_matches[i][-3:]] = name_matches[i].split('>')[1]
                yr_abbrs.append(abbr_matches[i][-3:])

            lg_yr_abbrevs[lg+'_'+str(yr)] = yr_abbrs

            # get players
            base_url = 'https://www.basketball-reference.com/teams/'
            for team_abbrev in yr_abbrs:
                url = base_url + team_abbrev + '/' + str(yr) + '.html'
                team_id = lg+'_'+str(yr)+'_'+team_abbrev

                page = requests.get(url)
                soup = BeautifulSoup(page.content, 'html.parser')
                try:
                    roster = soup.find(id='roster').prettify()
                    pergame_roster = soup.find(id='per_game').prettify()
                except:
                    try:
                        commented_table = list(filter(None, [comm if 'id=\"per_game\"' in comm else None for comm in soup.findAll(text = lambda text: isinstance(text, Comment))]))[0]
                        comment_soup = BeautifulSoup(commented_table, 'html.parser')
                        pergame_roster = comment_soup.find(id='per_game').prettify()
                    except:
                        print("ERROR: Cannot find", yr, "rosters.")
                        return

                players = pd.read_html(roster)[0]['Player']
                pergame_players = pd.read_html(pergame_roster)[0]['Unnamed: 1']
                players_full = list(OrderedDict.fromkeys(list(pd.concat([players, pergame_players]).apply(lambda pl: pl.replace('(TW)','').strip()))))
                players_full = [''.join(letter_replace_dict.get(ch, ch) for ch in name) for name in players_full]
                pl_ids = list(OrderedDict.fromkeys(re.findall('<a href="/players/[a-z]/[a-z]+[0-9]+', roster)))
                pl_ids_pergame = list(OrderedDict.fromkeys(re.findall('<a href="/players/[a-z]/[a-z]+[0-9]+', pergame_roster)))
                pl_ids_full = list(OrderedDict.fromkeys(pl_ids+pl_ids_pergame))
                pl_ids_clean = []

                for i in range(len(pl_ids_full)):
                    plid = pl_ids_full[i].split('/')[-1]
                    pl_ids_clean.append(plid)
                    if plid in player_team_dict:
                        player_team_dict[plid].append(team_id)
                        player_id_dict[plid][1] += 1
                        player_id_dict[plid][2] = yr
                    else:
                        player_team_dict[plid] = list([team_id])
                        pl_info = [players_full[i]]
                        pl_teams = player_team_dict[plid]
                        pl_info.append(len(pl_teams))
                        pl_info.append(yr)
                        player_id_dict[plid] = pl_info
                
                team_player_dict[team_id] = pl_ids_clean

        # update latest
        team_player_dict['latest'] = endyear

        # save dicts
        save_dict(team_player_dict, 'team_player_dict')
        save_dict(player_team_dict, 'player_team_dict')
        save_dict(player_id_dict, 'player_id_dict')
        save_dict(lg_yr_abbrevs, 'lg_yr_abbrevs')
        save_dict(tm_abbrs_names, 'tm_abbrs_names')

    return team_player_dict, player_team_dict, player_id_dict, lg_yr_abbrevs, tm_abbrs_names



# Get players from a given team
def get_team(team_player_dict, lg_yr_abbrevs, player_id_dict, tm_abbrs_names):
    year = padded_input("Enter a year:")
    latest_year = int(list(lg_yr_abbrevs.keys())[-1].split('_')[1])
    while True:
        try:
            year = int(year)
            assert year >= 1947
            assert year <= latest_year
            break
        except:
            year = padded_input("Invalid year, please try again:")
    poss_lgs = ['BAA', 'ABA', 'NBA']
    good_lgs = []
    for lg in poss_lgs:
        try:
            lg_yr_abbrevs[lg+'_'+str(year)]
            good_lgs.append(lg.lower())
        except:
            continue
    # if multiple possible leagues, ask user to choose one
    if len(good_lgs) > 1:
        lg_choice = padded_input("There are "+str(len(good_lgs))+" leagues active in that year. Would you like the "+good_lgs[1].upper()+" or the "+good_lgs[0].upper()+"?").lower()
        while True:
            if lg_choice in good_lgs:
                break
            else:
                lg_choice = padded_input("Invalid league, please type one of the two options:").lower()
    else:
        lg_choice = good_lgs[0]

    # print possible abbreviations for this year with correponding team names
    good_abbrevs = sorted(lg_yr_abbrevs[lg_choice.upper()+'_'+str(year)])
    for i in range(len(good_abbrevs)):
        print(str(i+1)+'.', good_abbrevs[i], '-', tm_abbrs_names[lg_choice.upper()+'_'+str(year)+'_'+good_abbrevs[i]])
    print('')
    
    # ask for chosen one
    tm_choice = padded_input("Enter the number or the abbreviation of the team you would like to see:")
    while True:
        try:
            tm_choice = int(tm_choice)
            assert tm_choice > 0
            assert tm_choice <= len(good_abbrevs)
            break
        except:
            if str(tm_choice).upper() in good_abbrevs:
                tm_choice = tm_choice.upper()
                break
            else:
                tm_choice = padded_input("Invalid input, please try again:")

    # print players
    if type(tm_choice) == int:
        tm_players = sorted(team_player_dict[lg_choice.upper()+'_'+str(year)+'_'+good_abbrevs[tm_choice-1]])
    else:
        tm_players = sorted(team_player_dict[lg_choice.upper()+'_'+str(year)+'_'+tm_choice])
    for player in tm_players:
        print(player_id_dict[player][0])
    print('')
    


# find shortest paths between 2 nodes using bidirectional bfs
def bidirectional_search(graph, start, goal):
    inittime = time()
    alerted = False
    # Check if start and goal are equal.
    if start == goal:
        return "That was easy! Start = goal"
    # Get dictionary of currently active nodes with their corresponding paths (path string : [origin, active node])
    active_nodes_path_dict = {start: [start, start], goal: [goal, goal]}
    # Nodes we have already visited
    inactive_nodes = set()
    explored_len = {}
    
    good_paths = []
    best_length = 999

    while active_nodes_path_dict:
        currtime = time()
        if currtime-inittime > 10 and not alerted:
            print("Searching...these players are far apart!\n")
            alerted = True
        # Make a copy of active nodes so we can modify the original dictionary
        active_nodes = list(active_nodes_path_dict.keys())
        for node in active_nodes:
            # Get the path to where we are
            current_path = node.split(',')
            # If double the current path length is already longer than the best length, return
            if len(current_path)*2 > best_length:
                return good_paths
            # Record whether we started at start or goal
            origin = active_nodes_path_dict[node][0]
            current_node = active_nodes_path_dict[node][1]
            # Check for new neighbors
            current_neighbors = set(graph[current_node]) - inactive_nodes
            # Check if our neighbors hit an active node
            active_goal_nodes = [value[1] for value in active_nodes_path_dict.values()]
            curr_neighbor_intersect = current_neighbors.intersection(active_goal_nodes)
            if len(curr_neighbor_intersect) > 0:
                active_indices = [i for i, x in enumerate(active_goal_nodes) if x in curr_neighbor_intersect]
                dict_key_list = list(active_nodes_path_dict.keys())
                curr_neighbor_paths = [dict_key_list[i] for i in active_indices]
                for meeting_path in curr_neighbor_paths:
                    # Check the two paths didn't start at same place. If not, then we have a path from start to goal
                    if origin != active_nodes_path_dict[meeting_path][0]:
                        # Reverse one of the paths and return the combined results
                        new_good_path = current_path + meeting_path.split(',')[::-1]
                        good_paths.append(new_good_path[::-1])
                        if best_length == 999:
                            best_length = len(new_good_path)
            

            neighbors_extend = current_neighbors - inactive_nodes
            if len(neighbors_extend) > 0:
                for neighbor_node in neighbors_extend:
                    increased_path = current_path + [neighbor_node]
                    increased_path_string = ','.join(increased_path)
                    increased_path_len = len(increased_path)
                    try:
                        nodelen = explored_len[neighbor_node]
                        if increased_path_len <= nodelen:
                            # keep exploring path
                            active_nodes_path_dict[increased_path_string] = [origin, neighbor_node]
                            explored_len[neighbor_node] = min(nodelen, increased_path_len)
                        else:
                            inactive_nodes.add(neighbor_node)
                    except:
                        nodelen = increased_path_len
                        explored_len[neighbor_node] = nodelen
                        active_nodes_path_dict[increased_path_string] = [origin, neighbor_node]
            
            inactive_nodes.add(node)
            active_nodes_path_dict.pop(node, None)

    return good_paths


# gets unique shortest paths (by players involved, not teams) and converts player IDs to names for printing
def shortest_path_names(graph, start, goal):
    paths = bidirectional_search(graph, start, goal)
    if not paths:
        return "Sorry, but a connecting path doesn't exist."
    if type(paths)==str:
        return paths
    path_len = len(paths[0])
    named_paths = []
    unique_paths = {}
    for p in paths:
        named_p = []
        for i in range(0, path_len, 2):
            named_p.append(player_id_dict[p[i]][0])
            if i < path_len-1:
                named_p.append(p[i+1][4:])
        try:
            unique_path_id = ''.join(named_p[::2])
            res = unique_paths[unique_path_id]
        except:
            named_paths.append(named_p)
            unique_paths[unique_path_id] = 1
    return named_paths


# convert input name to player ID to pass to other functions
def name_to_id(name, player_id_dict):
    lowername = name.lower().strip()
    if lowername == 'roster':
        return [lowername]
    matching_ids = list({key for key,value in player_id_dict.items() if value[0].lower()==lowername})
    matches = len(matching_ids)
    if matches == 0:
        return None
    else:
        return matching_ids


# take user input of player names and handle a range of cases, and return the player's corresponding ID when valid
def handle_input_name(name, player_id_dict, player_team_dict, team_player_dict, lg_yr_abbrevs):
    nameid = name_to_id(name, player_id_dict)
    while True:
        if not nameid:
            print("Sorry, no player with the name '" + name + "' could be found. Spelling is according to basketball-reference.com. If you know his team you may type 'roster' to see team rosters.\n")
            name = padded_input("Try again:")
            nameid = name_to_id(name, player_id_dict)
            continue
        elif len(nameid) > 1:
            num_names = len(nameid)
            print("There are multiple players with that exact name, here are each of their teams:")
            for i in range(num_names):
                print(str(i+1) + ": " + ', '.join(list(map(lambda x: x[4:], player_team_dict[nameid[i]]))))
            pick = padded_input("\nWhich number player would you like to select?")
            while True:
                try:
                    if int(pick) < num_names+1 and int(pick) > 0:
                        return nameid[int(pick)-1]
                    pick = padded_input("Invalid number entered, try again:")
                except:
                    pick = padded_input("Invalid number entered, try again:")
        elif nameid[0] == 'roster':
            get_team(team_player_dict, lg_yr_abbrevs, player_id_dict, tm_abbrs_names)
            name = padded_input("Enter a player name:")
            nameid = name_to_id(name, player_id_dict)
        else:
            try:
                player_team_dict[nameid[0]]
                return nameid[0]
            except:
                nameid = name_to_id(padded_input("That player was not active past the specified year. Try again:"), player_id_dict)


def get_connections(graph, player_id_dict, player_team_dict):
    # Get input for players
    p1id = handle_input_name(padded_input("Enter a player name:"), player_id_dict, player_team_dict, team_player_dict, lg_yr_abbrevs)
    p2id = handle_input_name(padded_input("Enter another player name:"), player_id_dict, player_team_dict, team_player_dict, lg_yr_abbrevs)
    print('')

    start_pl = p1id
    goal_pl = p2id

    connections = shortest_path_names(graph, start_pl, goal_pl)

    if type(connections) == str:
        print(connections)
        print('--------------------------------------------------------------------------------\n')
    else:
        print("There are", len(connections), "unique shortest player connections between", player_id_dict[p1id][0], "and", player_id_dict[p2id][0] + ":")
        for conn in connections:
            conn[1::2] = list(map(lambda x: x.replace('_', ' '), conn[1::2]))
            print(u"\u00B7", " - ".join(conn))
        print('--------------------------------------------------------------------------------\n')





if __name__ == '__main__':

    # load dict
    team_player_dict = load_obj('team_player_dict')
    player_team_dict = load_obj('player_team_dict')
    player_id_dict = load_obj('player_id_dict')
    lg_yr_abbrevs = load_obj('lg_yr_abbrevs')
    tm_abbrs_names = load_obj('tm_abbrs_names')

    # update dict
    # team_player_dict, player_team_dict, player_id_dict, lg_yr_abbrevs, tm_abbrs_names = update_dict(team_player_dict, player_team_dict, player_id_dict, lg_yr_abbrevs, tm_abbrs_names)

    # remove ['latest'] from team_player_dict before doing anything
    del team_player_dict['latest']

    # option to select minimum year in which players (and teams) that appear in graph were active
    min_year = 0
    if min_year > 0:
        team_player_dict_active = {key:value for key,value in team_player_dict.items() if int(key.split('_')[1])>=min_year}
        player_team_dict_active = {}
        for key,value in player_team_dict.items():
            if player_id_dict[key][2] >= min_year:
                player_team_dict_active[key] = [tm for tm in value if int(tm.split('_')[1])>=min_year]
    else:
        team_player_dict_active = team_player_dict
        player_team_dict_active = player_team_dict

    # create graph with edges from teams to players and players to teams
    graph = {**team_player_dict_active, **player_team_dict_active}

    print("\nWelcome! Enter two NBA player names to see their shortest connections. Type 'exit' at any time to terminate the application.\n")

    while True:
        get_connections(graph, player_id_dict, player_team_dict_active)



