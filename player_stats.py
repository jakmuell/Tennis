import os
import requests
#import csv
import datetime
import pandas as pd
import numpy as np
from elo_functions import sort_matches_table
from matplotlib import pyplot as plt

plt.style.use("ggplot")

# Change working directory to the directory where file is located
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
print(os.getcwd())

def E_surface(name,E,surface):
    E_surf = E.loc[(E.winner_name == name) | (E.loser_name == name), : ]
    E_surf = E_surf.reset_index(drop=True)
    E_surf = E_surf.loc[E_surf.surface==surface,:]
    E_surf["elo_surface"] = E_surf["loser_elo_surface"]
    E_surf.loc[E_surf.winner_name == name, "elo_surface"] = E_surf.winner_elo_surface[E_surf.winner_name == name]
    return E_surf

def E_overall(name):
    E_over = E.loc[(E.winner_name == name) | (E.loser_name == name), : ]
    E_over = E_over.reset_index(drop=True)
    E_over["elo_overall"] = E_over.loser_elo
    E_over.loc[E_over.winner_name == name, "elo_overall"] = E_over.winner_elo[E_over.winner_name == name]
    return E_over

M = pd.read_csv('matches.csv')
M = M.loc[:, ["winner_name","loser_name","score","tourney_date","date","round","tourney_id","match_id","temp"] ]
M.date=pd.to_datetime(M.date)
M["hour"] = M["date"].dt.hour
M.loc[M.hour==0,"hour"] = np.nan

T = pd.read_csv('tournaments.csv')
M = pd.merge(M,T,how='left',left_on="tourney_id",right_on="id")

E = pd.read_csv('elos.csv')
E = pd.merge(E,M,how="left",on="match_id")
startdate = datetime.datetime.strptime("2009-12-01", '%Y-%m-%d')
E = sort_matches_table(E,startdate)


# Create boolean variable which tells us if the user still wants to do something
continue_program = True

while continue_program:
    print("You have the following options:")
    print("[1] Create list of all matches a player played.")
    print("[2] Create plot of a player's Elo rating over time.")
    print("[3] Compare stats of two players in a table.")

    option = int(input())
    if option == 1:
        print('Type a player name.')
        name = input()
        col = ["winner_name","loser_name","score","tourney_date","date","round","tourney_id","temp"]
        M_player = M_player.loc[(M.winner_name == name) | (M.loser_name == name), col ]
        M_player["won/lost"] = "lost"
        M_player.loc[M_player.winner_name == name, "won/lost"] = "won"
        M_player["opponent"] = M_player.winner_name
        M_player.loc[M_player.winner_name == name, "opponent"] = M_player.loser_name[M_player.winner_name==name]
        startdate = datetime.datetime.strptime("2009-12-01", '%Y-%m-%d')
        M_player = sort_matches_table(M_player,startdate)
        M_player = M_player.drop(["winner_name","loser_name","date"], axis=1)
        M_player.to_csv(name+"_stats.csv",index=False)

    if option == 2:
        print('Type the name of one or more players (e.g. type \"Rafael Nadal, Novak Djokovic, Roger Federer\" or simply type \"Rafael Nadal\").')
        name_input = input()
        name_list = name_input.split(", ")
        if len(name_list)==1:
            name = name_list[0]
            E_hard = E_surface(name,E,"Hard")
            E_clay = E_surface(name,E,"Clay")
            E_grass = E_surface(name,E,"Grass")
            plt.plot(E_hard.date2,E_hard.elo_surface,label="hard court elo",color="blue")
            plt.plot(E_clay.date2,E_clay.elo_surface,label="clay court elo",color="chocolate")
            plt.plot(E_grass.date2,E_grass.elo_surface,label="grass court elo",color="green")
            plt.xlabel("Year")
            plt.ylabel("Elo rating")
            plt.title("Elo chart of " + name)
            plt.legend()
            plt.show()
        if len(name_list)>1:
            for name in name_list:
                E_player = E_overall(name)
                plt.plot(E_player.date2,E_player.elo_overall,label="overall elo (" + name + ")")
                plt.xlabel("Year")
                plt.ylabel("Elo rating")
            plt.title("Elo chart of " + name_input)
            plt.legend()
            plt.grid(True)
            plt.show()
    
    if option==3:
        # https://stackoverflow.com/questions/65761938/matplotlib-table-size-and-position
        print('Type the name of one or more players (e.g. type \"Rafael Nadal, Novak Djokovic, Roger Federer\" or simply type \"Rafael Nadal\").')
        name_input = input()
        name_list = name_input.split(", ")
        n = len(name_list)
        record_overall = [0]*n
        record_hard = [0]*n
        record_clay = [0]*n
        record_grass = [0]*n
        elo_max = [0]*n
        elo_max_hard = [0]*n
        elo_max_clay = [0]*n
        elo_max_grass = [0]*n
        current_elo = [0]*n
        current_elo_hard = [0]*n
        current_elo_clay = [0]*n
        current_elo_grass = [0]*n
        record_hot = [0]*n
        record_cold = [0]*n
        record_evening = [0]*n
        record_morning = [0]*n
        record_afternoon = [0]*n
        i=0
        for name in name_list:
            matches_no = sum((M.winner_name==name) | (M.loser_name==name))
            wins_no = sum(M.winner_name==name)
            losses_no = sum(M.loser_name==name)
            wins_percent = str(round((wins_no/matches_no)*100,1))+" %"
            record_overall[i] = str(wins_no)+" — "+str(losses_no)+" ("+wins_percent+")"
            
            wins_hard_no = sum((M.winner_name==name) & (M.surface=="Hard"))
            losses_hard_no = sum((M.loser_name==name) & (M.surface=="Hard"))
            matches_hard_no = wins_hard_no + losses_hard_no
            wins_percent_hard = str(round((wins_hard_no/matches_hard_no)*100,1))+" %"
            record_hard[i] = str(wins_hard_no)+" — "+str(losses_hard_no)+" ("+wins_percent_hard+")"

            wins_clay_no = sum((M.winner_name==name) & (M.surface=="Clay"))
            losses_clay_no = sum((M.loser_name==name) & (M.surface=="Clay"))
            matches_clay_no = wins_clay_no + losses_clay_no
            wins_percent_clay = str(round((wins_clay_no/matches_clay_no)*100,1))+" %"
            record_clay[i] = str(wins_clay_no)+" — "+str(losses_clay_no)+" ("+wins_percent_clay+")"

            wins_grass_no = sum((M.winner_name==name) & (M.surface=="Grass"))
            losses_grass_no = sum((M.loser_name==name) & (M.surface=="Grass"))
            matches_grass_no = wins_grass_no + losses_grass_no
            wins_percent_grass = str(round((wins_grass_no/matches_grass_no)*100,1))+" %"
            record_grass[i] = str(wins_grass_no)+" — "+str(losses_grass_no)+" ("+wins_percent_grass+")"


            
            E_player = E_overall(name)
            E_player = E_player.reset_index(drop=True)
            elo_absolutemax = E_player["elo_overall"].max()
            elo_max_index = np.where(E_player["elo_overall"] == elo_absolutemax)[0][0]
            elo_max_date = E_player.loc[elo_max_index,"date2"].strftime("%d %b, %Y")
            elo_max[i] = str(round(elo_absolutemax,1))+" ("+elo_max_date+")"

            m = len(E_player.index)
            current_elo_number = E_player.loc[(m-1),"elo_overall"]
            current_elo_date = E_player.loc[(m-1),"date2"].strftime("%d %b, %Y")
            current_elo[i] = str(round(current_elo_number,1))+" ("+current_elo_date+")"

            E_hard = E_surface(name,E,"Hard")
            E_hard = E_hard.reset_index(drop=True)
            elo_absolutemax_hard = E_hard["elo_surface"].max()
            elo_max_index_hard = np.where(E_hard["elo_surface"] == elo_absolutemax_hard)[0][0]
            elo_max_hard_date = E_hard.loc[elo_max_index_hard,"date2"].strftime("%d %b, %Y")
            elo_max_hard[i] = str(round(elo_absolutemax_hard,1))+" ("+elo_max_hard_date+")"

            m_hard = len(E_hard.index)
            current_elo_number_hard = E_hard.loc[(m_hard-1),"elo_surface"]
            current_elo_date_hard = E_hard.loc[(m_hard-1),"date2"].strftime("%d %b, %Y")
            current_elo_hard[i] = str(round(current_elo_number_hard,1))+" ("+current_elo_date_hard+")"

            E_clay = E_surface(name,E,"Clay")
            E_clay = E_clay.reset_index(drop=True)
            elo_absolutemax_clay = E_clay["elo_surface"].max()
            elo_max_index_clay = np.where(E_clay["elo_surface"] == elo_absolutemax_clay)[0][0]
            elo_max_clay_date = E_clay.loc[elo_max_index_clay,"date2"].strftime("%d %b, %Y")
            elo_max_clay[i] = str(round(elo_absolutemax_clay,1))+" ("+elo_max_clay_date+")"

            m_clay = len(E_clay.index)
            current_elo_number_clay = E_clay.loc[(m_clay-1),"elo_surface"]
            current_elo_date_clay = E_clay.loc[(m_clay-1),"date2"].strftime("%d %b, %Y")
            current_elo_clay[i] = str(round(current_elo_number_clay,1))+" ("+current_elo_date_clay+")"

            E_grass = E_surface(name,E,"Grass")
            E_grass = E_grass.reset_index(drop=True)
            elo_absolutemax_grass = E_grass["elo_surface"].max()
            elo_max_index_grass = np.where(E_grass["elo_surface"] == elo_absolutemax_grass)[0][0]
            elo_max_grass_date = E_grass.loc[elo_max_index_grass,"date2"].strftime("%d %b, %Y")
            elo_max_grass[i] = str(round(elo_absolutemax_grass,1))+" ("+elo_max_grass_date+")"

            m_grass = len(E_grass.index)
            current_elo_number_grass = E_grass.loc[(m_grass-1),"elo_surface"]
            current_elo_date_grass = E_grass.loc[(m_grass-1),"date2"].strftime("%d %b, %Y")
            current_elo_grass[i] = str(round(current_elo_number_grass,1))+" ("+current_elo_date_grass+")"

            wins_hot_no = sum((M.winner_name==name) & (M.temp>27))
            losses_hot_no = sum((M.loser_name==name) & (M.temp>27))
            matches_hot_no = wins_hot_no + losses_hot_no
            wins_percent_hot = str(round((wins_hot_no/matches_hot_no)*100,1))+" %"
            record_hot[i] = str(wins_hot_no)+" — "+str(losses_hot_no)+" ("+wins_percent_hot+")"

            wins_cold_no = sum((M.winner_name==name) & (M.temp<17))
            losses_cold_no = sum((M.loser_name==name) & (M.temp<17))
            matches_cold_no = wins_cold_no + losses_cold_no
            wins_percent_cold = str(round((wins_cold_no/matches_cold_no)*100,1))+" %"
            record_cold[i] = str(wins_cold_no)+" — "+str(losses_cold_no)+" ("+wins_percent_cold+")"

            wins_evening_no = sum((M.winner_name==name) & (M.hour>=18))
            losses_evening_no = sum((M.loser_name==name) & (M.hour>=18))
            matches_evening_no = wins_evening_no + losses_evening_no
            wins_percent_evening = str(round((wins_evening_no/matches_evening_no)*100,1))+" %"
            record_evening[i] = str(wins_evening_no)+" — "+str(losses_evening_no)+" ("+wins_percent_evening+")"

            wins_morning_no = sum((M.winner_name==name) & (M.hour<13))
            losses_morning_no = sum((M.loser_name==name) & (M.hour<13))
            matches_morning_no = wins_morning_no + losses_morning_no
            wins_percent_morning = str(round((wins_morning_no/matches_morning_no)*100,1))+" %"
            record_morning[i] = str(wins_morning_no)+" — "+str(losses_morning_no)+" ("+wins_percent_morning+")"

            wins_afternoon_no = sum((M.winner_name==name) & (M.hour.between(13,18)))
            losses_afternoon_no = sum((M.loser_name==name) & (M.hour.between(13,18)))
            matches_afternoon_no = wins_afternoon_no + losses_afternoon_no
            wins_percent_afternoon = str(round((wins_afternoon_no/matches_afternoon_no)*100,1))+" %"
            record_afternoon[i] = str(wins_afternoon_no)+" — "+str(losses_afternoon_no)+" ("+wins_percent_afternoon+")"
            
            i+=1
        
        row1 = record_overall
        row1.insert(0,"overall record")
        row2 = record_hard
        row2.insert(0,"record on hard courts")
        row3 = record_clay
        row3.insert(0,"record on clay courts")
        row4 = record_grass
        row4.insert(0,"record on grass courts")
        row5 = current_elo
        row5.insert(0,"current elo")
        row6 = current_elo_hard
        row6.insert(0,"current hard court elo")
        row7 = current_elo_clay
        row7.insert(0,"current clay court elo")
        row8 = current_elo_grass
        row8.insert(0,"current grass court elo")
        row9 = elo_max
        row9.insert(0,"Highest elo overall")
        row10 = elo_max_hard
        row10.insert(0,"Highest hard court elo")
        row11 = elo_max_clay
        row11.insert(0,"Highest clay court elo")
        row12 = elo_max_grass
        row12.insert(0,"Highest grass court elo")
        row13 = record_hot
        row13.insert(0,"record in hot weather (>27C)")
        row14 = record_cold
        row14.insert(0,"record in cold weather (<17C)")
        row15 = record_evening
        row15.insert(0,"evening record (6pm and after)")
        row16 = record_morning
        row16.insert(0,"morning record (before 1pm)")
        row17 = record_afternoon
        row17.insert(0,"afternoon record (1pm-6pm)")

        data = [name_list,row1,row2,row3,row4,row5,row6,row7,row8,row9,row10,row11,row12,row13,row14,row15,row16,row17]
        column_headers = data[0]
        row_headers = [row[0] for row in data[1:]]
        cell_text = [row[1:] for row in data[1:]]
        nrow = 2
        fig, ax1 = plt.subplots(figsize=(10, 2 + nrow / 2.5))

        rcolors = np.full(len(row_headers), 'linen')
        ccolors = np.full(len(column_headers), 'lavender')

        table = ax1.table(cellText=cell_text,
                        cellLoc='center',
                        rowLabels=row_headers,
                        rowColours=rcolors,
                        rowLoc='center',
                        colColours=ccolors,
                        colLabels=column_headers,
                        loc='center')
        table.scale(1, 2)
        table.set_fontsize(16)
        ax1.axis('off')
        #title = "demo title"
        #subtitle = "demo subtitle"
        #ax1.set_title(f'{title}\n({subtitle})', weight='bold', size=14, color='k')

        plt.savefig("demo_table.png", dpi=200, bbox_inches='tight')
        plt.show()

    print("Do you want to do something else [Y/N]?")
    continue_program = (input()=="Y")



