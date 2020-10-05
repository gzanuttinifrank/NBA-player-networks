import pandas as pd
from bs4 import BeautifulSoup, Comment
import requests
import re
from collections import OrderedDict
import pickle


def save_dict(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


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



if __name__ == '__main__':

    # Create the 5 dictionaries necessary for the algorithm to run
    create_dict()

