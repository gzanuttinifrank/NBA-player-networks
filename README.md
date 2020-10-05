# NBA-player-networks

Given any two players in NBA history, this program finds the shortest connections between them through a network of mutual teammates. The user is prompted to enter one name at a time, whose spelling is compared to `basketball-reference.com` (with special characters replaced and case insensitive), and accepted if successfully matched with a corresponding player ID in the `player_id_dict`. Once two valid names are entered, bidirectional breadth-first search is used to find connections between the players, and *all* of the shortest connections are returned and shown to the user, including the teams and seasons connecting each node.

### Sample input and output:

![Sample output](https://github.com/gzanuttinifrank/NBA-player-networks/blob/main/example.png)

### File and dataset descriptions:

* **`nba_player_networks`** contains both the logic behind the bidirectional BFS algorithm as well as the input handling and the functions to create and update the pkl files containing the necessary dictionaries of data.
* **`lg_yr_abbrevs`** is a dictionary indexed by a league year (eg. NBA_2019) with values being the list of team abbreviations of all teams that participated in that league year.
* **`player_id_dict`** is a dictionary that maps a player ID to a list of three elements: the player's full name, the number of distinct team-seasons he has played on (playing for the same franchise for two seasons counts as two distinct teams), and the most recent year in which he was active.
* **`player_team_dict`** maps a player ID to a list of all of the distinct team-seasons he has played for. Each team-season is represented as the league abbreviation, the season ending year, and the team abbreviation (eg. NBA_2019_ATL).
* **`team_player_dict`** maps team-seasons (eg. NBA_2019_ATL) to a list of all player IDs corresponding to players that either recorded a single statistic during the season or who were listed on the roster at the end of the season.
* **`tm_abbrs_names`** maps team-seasons to the teams' full names (eg. NBA_2019_ATL maps to "Atlanta Hawks").
* **`NBA_Networks.zip`** contains a Unix executable file that runs the algorithm as a standalone program, without requiring the user to download all the files to a single local directory.
