import os
import requests
import csv
import datetime
import re
import numpy as np
import pandas as pd

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
    M_final = M_final.drop(["date2","roundvalue"], axis=1)
    return M_final

def transform_to_set_format(M):
    # This function returns the table M appended by the two columns "winner_setswon" and "loser_setswon"
    # Split the variable score into (up to) 5 variables set1 up to set5 (e.g. "6-2 1-6 7-6" becomes ["6-2" "1-6" "7-6"])
    tmp=M.score.str.split()
    X=tmp.apply(pd.Series)
    m=len(X.columns)
    X2=X.drop(X.columns[5:m],axis = 1)
    X2 = X2.set_axis(['set1', 'set2', 'set3', 'set4', 'set5'], axis=1, copy=False)
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

def update_elo(M,P,c,o,s1,initial_elo,recentdays,penaltyfactor):
    # Input parameters:
    # M is a data frame of matches
    # P is a data frame consisting of players and their starting elos
    # c is a constant
    # o is a small offset
    # s1 is a shape parameter
    # initial_elo is the rating given to new players (that are not in P)
    # recentdays is ...
    # penaltyfactor is ...

    # The function returns M appended by the variables "winner_elo", "loser_elo" and the updated P

    n=len(M.index)
    for i in range(n-1):
        winner_row = np.where(P["Name"] == M.loc[i,"winner_name"])[0][0] # index of row in table P where winner is located
        loser_row = np.where(P["Name"] == M.loc[i,"loser_name"])[0][0] # index of row in table P where loser is located
        w_elo_old=P.loc[winner_row,"EloRating"]
        l_elo_old=P.loc[loser_row,"EloRating"]
        w_match_number=P.loc[winner_row,"match_number"]
        l_match_number=P.loc[loser_row,"match_number"]
        w_activityfactor=1
        l_activityfactor=1
        w_setwinprob=1/(1+10**((l_elo_old-w_elo_old)/400))
        total_sets=M.winner_setswon[i]+M.loser_setswon[i]
        w_K=w_activityfactor*c/(w_match_number+o)**s1
        l_K=l_activityfactor*c/(l_match_number+o)**s1
        M.loc[i,"winner_elo"]=w_elo_old+w_K*M.winner_setswon[i]-w_setwinprob*w_K*total_sets
        M.loc[i,"loser_elo"]=l_elo_old+l_K*total_sets*w_setwinprob-M.winner_setswon[i]*l_K
        P.loc[winner_row,"EloRating"]=M.winner_elo[i]
        P.loc[loser_row,"EloRating"]=M.loser_elo[i]
        P.loc[winner_row,"match_number"]+=1
        P.loc[loser_row,"match_number"]+=1

    P = P.sort_values(by=["EloRating","roundvalue"])
    P = P.reset_index(drop=True)

    return M, P

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
    print('Type 1 or 2.')
    input1 = int(input())
    if input1==1:
        startdate = datetime.datetime.strptime("2009-12-01", '%Y-%m-%d %H:%M')
        filename = 'elo_ratings_yearend_2009.csv'
    if input1==2:
        print('Type desired start date in the format YYYY-MM-DD.')
        startdate = datetime.datetime.strptime(input(), '%Y-%m-%d')
        print('Type the name of the file used for the start elos (including .csv suffix).')
        filename = input()
    
    # Make appropriate transformations
    M=sort_matches_table(master,startdate)
    M=transform_to_set_format(M)
    P = pd.read_csv(filename)
    all_names = set(M.winner_name).union(set(M.loser_name))
    available_names = set(P.Name)
    unavalaible_names = all_names.difference(available_names)
    P_unavailable = pd.DataFrame(unavalaible_names,columns=['Name'])
    P_unavailable["EloRating"]=1400
    P_unavailable["match_number"]=0
    P=pd.concat([P,P_unavailable]).reset_index(drop=True)

    # Ask user if they want to use default parameters or set parameters manually
    print('Do you want to use the default parameters for Elo algorithm (type 1) or set values manually (type 2)?')
    input2 = int(input())
    if input2==1:
        c=250
        o=20
        s1=0.6
        initial_elo=1400
        recentdays=75
        penaltyfactor=0.98
    elif input2==2:
        print('Specify constant c.')
        c=float(input())
        print('Specify small offset o.')
        o=float(input())
        print('Specify shape parameter s')
        s1=float(input())
        print('Specify the Elo rating that is given to new players')
        initial_elo=float(input())
        recentdays=75
        penaltyfactor=0.98

    print('Starting to calculate (Note: This is an iterative algorith, therefore this may take a while).')
    M,P = update_elo(M,P,c,o,s1,initial_elo,recentdays,penaltyfactor)

    M.to_csv('matches2.csv',index=False)
    print('Succesfully wrote file \"matches2.csv\".')
    P.to_csv('players_elos.csv',index=False)
    print('Succesfully written file \"players_elos.csv\".')

main()
