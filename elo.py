import os
import requests
import csv
import datetime
import re
import numpy as np
import pandas as pd
from math import exp
from math import floor
import time

def sort_matches_table(M,startdate):
    # This function returns the table M in chronological order (ascending, only entries after start_date, everything else is deleted)
    M.date=pd.to_datetime(M.date)
    M.tourney_date=pd.to_datetime(M.tourney_date)
    # Create auxiliary variable date2 which is equal to date if date exists and tourney_date else
    M.loc[:,"date2"]=M.date
    M.loc[pd.isna(M.date),"date2"]=M.loc[pd.isna(M.date),"tourney_date"]
    M=M.loc[pd.notna(M.date2),:]
    M=M.loc[M.date2>=startdate]
    # Create auxiliary variable roundvalue (higher value means later stage of tournament)
    rounds=["NA","Q1","Q2","Q3","Q4","R128","R64","R32","R16","QF","SF","BR","F"\
        "RR 1","RR 2","RR 3","RR"]
    d = {'round': rounds, 'roundvalue': [*range(len(rounds))]}
    df = pd.DataFrame(data=d)
    M_merged = pd.merge(M,df,how="left",on="round")
    # Sort the table by date2 and use roundvalue as tiebreaker
    M_final = M_merged.sort_values(by=["date2","roundvalue"])
    M_final = M_final.reset_index(drop=True)
    # Delete the auxiliary variables
    M_final = M_final.drop(["roundvalue"], axis=1)
    return M_final

def transform_to_set_format(M):
    # This function returns the table M appended by the two columns "winner_setswon" and "loser_setswon"
    # Split the variable score into (up to) 5 variables set1 up to set5 (e.g. "6-2 1-6 7-6" becomes ["6-2" "1-6" "7-6"])
    tmp=M.score.str.split()
    X=tmp.apply(pd.Series)
    m=len(X.columns)
    X2=X.drop(X.columns[5:m],axis = 1)
    #X2 = X2.set_axis(['set1', 'set2', 'set3', 'set4', 'set5'], axis=1, copy=False)
    X2 = X2.rename({0: 'set1', 1: 'set2', 2: 'set3', 3: 'set4', 4: 'set5'}, axis=1)
    N = pd.concat([M,X2],axis=1)
    N.set1=N['set1'].str.replace(r"\(.*\)","",True)
    N.set2=N['set2'].str.replace(r"\(.*\)","",True)
    N.set3=N['set3'].str.replace(r"\(.*\)","",True)
    N.set4=N['set4'].str.replace(r"\(.*\)","",True)
    N.set5=N['set5'].str.replace(r"\(.*\)","",True)
    N.set3=N['set3'].str.replace("[","",False)
    N.set3=N['set3'].str.replace("]","",False)

    valid_results1=["6-0","6-1","6-2","6-3","6-4","7-5","7-6","8-6","9-7", \
        "10-8","11-9","12-10","13-11","14-12","15-13","16-14","17-15","18-16", \
        "19-17","20-18","21-19","22-20","23-21","24-22","25-23","26-24","70-68"]
    valid_results2=["0-6","1-6","2-6","3-6","4-6","5-7","6-7","6-8","7-9", \
        "8-10" "9-11" "10-12" "11-13" "12-14" "13-15","14-16","15-17","16-18", \
        "17-19","18-20","19-21","20-22","21-23","22-24","23-25","24-26","68-70"]

    N["set1_winner"]=np.nan
    set1_winner_won = N["set1"].isin(valid_results1)
    set1_loser_won = N["set1"].isin(valid_results2)
    N.loc[set1_winner_won,'set1_winner']="winner"
    N.loc[set1_loser_won,'set1_winner']="loser"
    N["set2_winner"]=np.nan
    set2_winner_won = N["set2"].isin(valid_results1)
    set2_loser_won = N["set2"].isin(valid_results2)
    N.loc[set2_winner_won,'set2_winner']="winner"
    N.loc[set2_loser_won,'set2_winner']="loser"
    N["set3_winner"]=np.nan
    set3_winner_won = N["set3"].isin(valid_results1)
    set3_loser_won = N["set3"].isin(valid_results2)
    N.loc[set3_winner_won,'set3_winner']="winner"
    N.loc[set3_loser_won,'set3_winner']="loser"
    N["set4_winner"]=np.nan
    set4_winner_won = N["set4"].isin(valid_results1)
    set4_loser_won = N["set4"].isin(valid_results2)
    N.loc[set4_winner_won,'set4_winner']="winner"
    N.loc[set4_loser_won,'set4_winner']="loser"
    N["set5_winner"]=np.nan
    set5_winner_won = N["set5"].isin(valid_results1)
    set5_loser_won = N["set5"].isin(valid_results2)
    N.loc[set5_winner_won,'set5_winner']="winner"
    N.loc[set5_loser_won,'set5_winner']="loser"

    N.loc[:,'winner_setswon']=(N.set1_winner=="winner").astype(int)+\
        (N.set2_winner=="winner").astype(int)+(N.set3_winner=="winner").astype(int)+\
        (N.set4_winner=="winner").astype(int)+(N.set5_winner=="winner").astype(int)
    N.loc[:,'loser_setswon']=(N.set1_winner=="loser").astype(int)+\
        (N.set2_winner=="loser").astype(int)+(N.set3_winner=="loser").astype(int)+\
        (N.set4_winner=="loser").astype(int)+(N.set5_winner=="loser").astype(int)

    N = N.drop(["set1","set2","set3","set4","set5","set1_winner","set2_winner","set3_winner","set4_winner","set5_winner"], axis=1)
    return N

def update_elo(M,P,c,c_hard,c_clay,c_grass,o,s1,initial_elo,recentdays,penaltyfactor,start_row,end_row):
    # Input parameters:
    # M is a data frame of matches
    # P is a data frame consisting of players and their starting elos
    # c, c_hard, c_clay, c_grass are constants
    # o is a small offset
    # s1 is a shape parameter
    # initial_elo is the rating given to new players (that are not in P)
    # recentdays is ...
    # penaltyfactor is ...

    # The function returns M appended by the variables "winner_elo", "loser_elo" and the updated P

    t = time.time()
    for i in range(start_row,end_row):
        winner_name = M.winner_name[i]
        loser_name = M.loser_name[i]

        # Retrieve data from P (numbers before the match)
        winner_row = np.where(P["Name"] == winner_name)[0][0] # position of winner in P
        loser_row = np.where(P["Name"] == loser_name)[0][0] # position of loser in P
        w_elo_old=P.loc[winner_row,"elo_overall"]
        l_elo_old=P.loc[loser_row,"elo_overall"]
        w_match_number=P.loc[winner_row,"match_number"]
        l_match_number=P.loc[loser_row,"match_number"]
        l_activityfactor=1
        w_setwinprob=1/(1+10**((l_elo_old-w_elo_old)/400))
        total_sets=M.winner_setswon[i]+M.loser_setswon[i]
        
        # The variables "winner_previous_match" and "loser_previous_match" give the id of the previous match
        # This is unrelated to the Elo but it also requires an iterative algorithm, so we deal with it in this script as well
        # These variables can later be used to determine other variables, e.g. "different_surface", "retired_last_match" etc.
        M.loc[i,"winner_previous_match"] = P.previous_match[winner_row]
        M.loc[i,"loser_previous_match"] = P.previous_match[loser_row]
        P.loc[winner_row,"previous_match"] = M.match_id[i]
        P.loc[loser_row,"previous_match"] = M.match_id[i]
        
        # Now we can calculate the Elo after the match
        # We use a weighted Elo algorithm (weight = number of sets the player won)

        # Calculate the activityfactors (if players have few recent matches, the K factor will be higher)
        # We use the formula activityfactor = exp(-0.4*recentmatches)+1
        # So 0 recentmatches -> activityfactor=2, 1 recentmatches -> activityfactor=1.67, ..., 10 recentmatches -> factor=1.02, ...
        # If recentmatches=0 there will also be a penalty (because players tend to be weaker after an injury break)
        if w_match_number>= 40: # We only do this for players with at least 40 games (below this, data too unreliable)
            date_cutoff = M.date2[i]-datetime.timedelta(days=recentdays)
            row_cutoff = M['date2'].gt(date_cutoff).idxmax() # first instance of the variable date2 being >= date_cutoff
            recent_matches = M.loc[row_cutoff:(i-1),:]
            w_recentmatches = sum((recent_matches.winner_name==winner_name) | (recent_matches.loser_name==winner_name))
            w_activityfactor=exp(-0.4*w_recentmatches)+1
            if w_recentmatches==0:
                w_penaltyfactor=1-(1-penaltyfactor)/(1+exp(-0.05*(w_elo_old-1910))*((1/0.995)-1))
                w_elo_old=w_elo_old*w_penaltyfactor
            if l_match_number>= 40:
                l_recentmatches = sum((recent_matches.winner_name==loser_name) | (recent_matches.loser_name==loser_name))
                l_activityfactor=exp(-0.4*l_recentmatches)+1
                if l_recentmatches==0:
                    l_penaltyfactor=1-(1-penaltyfactor)/(1+exp(-0.05*(l_elo_old-1910))*((1/0.995)-1))
                    l_elo_old=l_elo_old*l_penaltyfactor
            else:
                l_activityfactor=1
        else:
            w_activityfactor=1
            if l_match_number>=40:
                date_cutoff = M.date2[i]-datetime.timedelta(days=recentdays)
                row_cutoff = M['date2'].gt(date_cutoff).idxmax()
                recent_matches = M.loc[row_cutoff:(i-1),:]
                l_recentmatches = sum((recent_matches.winner_name==loser_name) | (recent_matches.loser_name==loser_name))
                l_activityfactor=exp(-0.4*l_recentmatches)+1
                if l_recentmatches==0:
                    l_penaltyfactor=1-(1-penaltyfactor)/(1+exp(-0.05*(l_elo_old-1910))*((1/0.995)-1))
                    l_elo_old=l_elo_old*l_penaltyfactor
            else:
                l_activityfactor=1
    
        w_K=w_activityfactor*c/(w_match_number+o)**s1
        l_K=l_activityfactor*c/(l_match_number+o)**s1
        M.loc[i,"winner_elo"]=w_elo_old+w_K*M.winner_setswon[i]-w_setwinprob*w_K*total_sets
        M.loc[i,"loser_elo"]=l_elo_old+l_K*total_sets*w_setwinprob-M.winner_setswon[i]*l_K
        P.loc[winner_row,"elo_overall"]=M.winner_elo[i]
        P.loc[loser_row,"elo_overall"]=M.loser_elo[i]
        P.loc[winner_row,"match_number"]+=1
        P.loc[loser_row,"match_number"]+=1

        surface = M.surface[i]
        if surface == "Hard":
            w_elo_old_surface = P.loc[winner_row,"elo_hard"]
            l_elo_old_surface = P.loc[loser_row,"elo_hard"]
            w_match_number_surface = P.loc[winner_row,"match_number_hard"]
            l_match_number_surface = P.loc[loser_row,"match_number_hard"]
            c_surface = c_hard
        elif surface == "Clay":
            w_elo_old_surface = P.loc[winner_row,"elo_clay"]
            l_elo_old_surface = P.loc[loser_row,"elo_clay"]
            w_match_number_surface = P.loc[winner_row,"match_number_clay"]
            l_match_number_surface = P.loc[loser_row,"match_number_clay"]
            c_surface = c_clay
        else: # grass or carpet
            w_elo_old_surface = P.loc[winner_row,"elo_grass"]
            l_elo_old_surface = P.loc[loser_row,"elo_grass"]
            w_match_number_surface = P.loc[winner_row,"match_number_grass"]
            l_match_number_surface = P.loc[loser_row,"match_number_grass"]
            c_surface = c_grass
        w_setwinprob_surface = 1/(1+10**((l_elo_old_surface-w_elo_old_surface)/400))
        w_K_surface=w_activityfactor*c_surface/(w_match_number_surface+o)**s1
        l_K_surface=l_activityfactor*c_surface/(l_match_number_surface+o)**s1
        M.loc[i,"winner_elo_surface"]=w_elo_old_surface+w_K_surface*M.winner_setswon[i]-w_setwinprob_surface*w_K_surface*total_sets
        M.loc[i,"loser_elo_surface"]=l_elo_old_surface+l_K_surface*total_sets*w_setwinprob_surface-M.winner_setswon[i]*l_K_surface
        if surface == "Hard":
            P.loc[winner_row,"elo_hard"]=M.winner_elo_surface[i]
            P.loc[loser_row,"elo_hard"]=M.loser_elo_surface[i]
            P.loc[winner_row,"match_number_hard"]+=1
            P.loc[loser_row,"match_number_hard"]+=1
        elif surface == "Clay":
            P.loc[winner_row,"elo_clay"]=M.winner_elo_surface[i]
            P.loc[loser_row,"elo_clay"]=M.loser_elo_surface[i]
            P.loc[winner_row,"match_number_clay"]+=1
            P.loc[loser_row,"match_number_clay"]+=1
        else:
            P.loc[winner_row,"elo_grass"]=M.winner_elo_surface[i]
            P.loc[loser_row,"elo_grass"]=M.loser_elo_surface[i]
            P.loc[winner_row,"match_number_grass"]+=1
            P.loc[loser_row,"match_number_grass"]+=1
    
    elapsed = time.time() - t
    print("Rows {} up to {} succesfully calculated in {} seconds".format(start_row+1,end_row+1,elapsed))

    P = P.sort_values(by=["elo_overall"], ascending = False)
    P = P.reset_index(drop=True)

    return M, P, elapsed

def main():
    # Change working directory to the directory where file elo.py is located
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    print(os.getcwd())

    # Read matches.csv
    master = pd.read_csv('matches.csv')

    # Ask user if they want to calculate everything or only rows from a start point
    print('You may either calculate everything from scratch or from a specific start date.')
    print('If you choose method 1, the file \"elo_ratings_yearend_2009.csv\" will be used for the start elos.')
    print('If you choose method 2, you will need to specify an alternative file for that purpose.')
    print('Type 1 or 2 (currently only method 1 supported).')
    input1 = int(input())

    # Ask user if they want to use default parameters or set parameters manually
    print('Do you want to use the default parameters for Elo algorithm (type 1) or set values manually (type 2)?')
    input2 = int(input())

    if input1==1:
        startdate = datetime.datetime.strptime("2009-12-01", '%Y-%m-%d')
        filename = 'elo_ratings_yearend_2009.csv'
    if input1==2:
        print('Type desired start date in the format YYYY-MM-DD.')
        startdate = datetime.datetime.strptime(input(), '%Y-%m-%d')
        print('Type the name of the file used for the start elos (including .csv suffix).')
        filename = input()
    
    # Make appropriate transformations to M
    M=sort_matches_table(master,startdate)
    M=transform_to_set_format(M)

    # Add players without a start elo to P
    P = pd.read_csv(filename)
    if 'elo_hard' not in P.columns:
        P["elo_hard"] = P.elo_overall
        P["match_number_hard"] = 0
    if 'elo_clay' not in P.columns:
        P["elo_clay"] = P.elo_overall
        P["match_number_clay"] = 0
    if 'elo_grass' not in P.columns:
        P["elo_grass"] = P.elo_overall
        P["match_number_grass"] = 0
    all_names = set(M.winner_name).union(set(M.loser_name))
    available_names = set(P.Name)
    unavalaible_names = all_names.difference(available_names)
    P_unavailable = pd.DataFrame(unavalaible_names,columns=['Name'])
    P_unavailable["elo_overall"] = 1400
    P_unavailable["match_number"] = 0
    P_unavailable["elo_hard"] = 1400
    P_unavailable["elo_clay"] = 1400
    P_unavailable["elo_grass"] = 1400
    P_unavailable["match_number_hard"] = 0
    P_unavailable["match_number_clay"] = 0
    P_unavailable["match_number_grass"] = 0
    P=pd.concat([P,P_unavailable]).reset_index(drop=True)
    P["previous_match"] = np.nan


    c=250
    c_hard = 280
    c_clay = 300
    c_grass = 350
    o=20
    s1=0.6
    initial_elo=1400
    recentdays=75
    penaltyfactor=0.98
    if input2==2:
        print('Specify constant c (default setting is {}).'.format(c))
        c=float(input())
        print('Specify constant c_hard (default setting is {}).'.format(c_hard))
        c_hard = float(input())
        print('Specify constant c_clay (default setting is {}).'.format(c_clay))
        c_clay = float(input())
        print('Specify constant c_grass (default setting is {}).'.format(c_grass))
        c_grass = float(input())
        print('Specify small offset o (default setting is {}).'.format(o))
        o=float(input())
        print('Specify shape parameter s (default setting is {}).'.format(s1))
        s1=float(input())
        print('Specify the Elo rating that is given to new players (default setting is {}).'.format(initial_elo))
        initial_elo=float(input())
        recentdays=75
        penaltyfactor=0.98
    n=len(M.index)
    expected_time = round((n/10000)*100/60)
    print('Starting with the iterative algorithm over {} rows, expect about {} minutes for the program to complete.'.format(n,expected_time))
    elapsed_total = 0
    for j in range(floor(n/10000)):
        start_row = j*10000
        end_row = (j+1)*10000-1
        M,P,elapsed = update_elo(M,P,c,c_hard,c_clay,c_grass,o,s1,initial_elo,recentdays,penaltyfactor,start_row,end_row)
        elapsed_total+=elapsed
        #print('Rows {} up to {} are succesfully calculated.'.format((start_row+1),(end_row+1)))
    start_row = (floor(n/10000))*10000
    end_row = n-1
    M,P,elapsed = update_elo(M,P,c,c_hard,c_clay,c_grass,o,s1,initial_elo,recentdays,penaltyfactor,start_row,end_row)
    elapsed_total+=elapsed
    print('Done calculating. This took {} minutes'.format(elapsed_total/60))

    #M = M.drop(["date2","winner_setswon","loser_setswon"], axis=1)
    M = M.loc[:,["match-id","winner_previous_match","loser_previous_match","winner_elo","loser_elo","winner_elo_surface","loser_elo_surface"]]
    M.to_csv('elos.csv',index=False)
    print('Succesfully wrote to file \"elos.csv\".')
    P.to_csv('players_elos.csv',index=False)
    print('Succesfully wrote to file \"players_elos.csv\".')
    
    P_small = P.loc[0:9,["Name","elo_overall"]]
    print("Just for fun. This is the top 10 according to overall elo:")
    print(P_small)
main()
