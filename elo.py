import os
import requests
import csv
import datetime
import re
import numpy as np
import pandas as pd

def sort_master_table(master_table):
    M=master_table
    M.date=pd.to_datetime(M.date)
    M.tourney_date=pd.to_datetime(M.tourney_date)
    M.loc[:,"date2"]=M.date
    #M.loc[M["date2"].isna(),"date2"]=M.tourney_date[M["date2"].isna()]
    M.loc[pd.isna(M.date),"date2"]=M.loc[pd.isna(M.date),"tourney_date"]
    rounds=["NA","Q1","Q2","Q3","Q4","R128","R64","R32","R16","QF","SF","BR","F"\
        "RR 1","RR 2","RR 3","RR"]
    d = {'round': rounds, 'roundvalue': [*range(len(rounds))]}
    df = pd.DataFrame(data=d)
    M_merged = pd.merge(master_table,df,how="left",on="round")
    M_final = M_merged.sort_values(by=["date2","roundvalue"])
    M_final = M_final.reset_index(drop=True)
    #M_final.drop(["roundvalue"], axis=1)
    #print(M_final.date2.head(10))
    return M_final

# Die Funktion transform_to_set_format nimmt als Parameter die Master-Tabelle und erstellt
# zwei neue Spalten "winner_setswon" und "loser_setswon"
# Sie gibt die Mastertabelle zurück mit den zwei zusätzlichen Spalten
def transform_to_set_format(master_table):
    M=master_table
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

    N.drop(["set1","set2","set3","set4","set5","set1_winner","set2_winner","set3_winner","set4_winner","set5_winner"], axis=1)
    return N


#print(type(master.loc[224514,"tourney_date"]))
#print(type(master.loc[224514,"date"]))
#print(master.loc[224514,"tourney_date"])
#print(master.loc[224514,"date"])


# Die Funktion update_elo nimmt als Parameter:
# 1. die um die Spalten "winner_setswon" und "loser_setswon" und zeitlich sortierte Mastertabelle (hier: M)
# 2. die Spielertabelle mit den Anfangs-Elos (hier: P)
# 3. 

# Sie gibt aus:
# 1. die Mastertabelle mit den aktualisierten Spalten "w_elo", "l_elo"
# 2. die Spielertabelle mit den aktualisierten Elos


def update_elo(M,P,c,o,s1,initial_elo,recentdays,penaltyfactor):
    
    # M is a data frame of matches
    # P is a data frame consisting of players and their starting elos
    # c is a constant
    # o is a small offset
    # s1 is a shape parameter
    # initial_elo is the rating given to new players (that are not in P)
    # recentdays is ...
    # penaltyfactor is ...
    #print(len(M0.date2))
    #print(sum(pd.isna(M0.date2)))
    M=M.loc[pd.notna(M.date2),:]
    #print(len(M1.date2))
    #print(M1.loc[0,"date2"])
    #M=M1.iloc[0:10000]
    #print(len(M.date2))
    M.loc[:,"w_elo_old"]=0
    M.loc[:,"l_elo_old"]=0
    M.loc[:,"w_setwinprob"]=0
    M.loc[:,"total_sets"]=0
    M.loc[:,"w_K"]=0
    M.loc[:,"l_K"]=0

    # P auffüllen
    #winner_names = pd.Series(M.winner_name.unique())
    #print(type(winner_names))
    #loser_names = pd.Series(M.loser_name.unique())
    #all_names = pd.concat([winner_names,loser_names]).unique()
    #print(len(all_names))
    #available_names = P.Name.unique()
    #print(len(available_names))
    #unavalaible_names = set(all_names).difference(set(available_names))
    #print(len(unavalaible_names))
    #P_unavailable = pd.DataFrame(unavalaible_names, columns = ['Name'])
    #print(P_unavailable)
    #P_unavailable.loc[:,"EloRating"]=initial_elo
    #P_unavailable.loc[:,"match_number"]=0
    #print(type(P))
    #print(type(P_unavailable))
    #P= pd.concat([P, P_unavailable])
    #print(P)

    #Available=pd.DataFrame(available_names)
    #All_Names=pd.DataFrame(all_names)
    #Available.to_csv('Available.csv')
    #All_Names.to_csv('All_Names.csv')

    n=len(M.index)
    #l=n-1
    for i in range(n-1):
        winner_row = np.where(P["Name"] == M.loc[i,"winner_name"])[0][0] # index of row in table P where winner is located
        M.loc[i,"winner_matches"] = sum(P.Name==M.winner_name[i])
        loser_row = np.where(P["Name"] == M.loc[i,"loser_name"])[0][0] # index of row in table P where loser is located
        M.loc[i,"winner_row"]=winner_row
        M.loc[i,"loser_row"]=loser_row
        w_elo_old=P.loc[winner_row,"EloRating"]
        l_elo_old=P.loc[loser_row,"EloRating"]
        M.loc[i,"w_elo_old"]=w_elo_old
        M.loc[i,"l_elo_old"]=l_elo_old
        w_match_number=P.loc[winner_row,"match_number"]
        l_match_number=P.loc[loser_row,"match_number"]
        w_activityfactor=1
        l_activityfactor=1
        w_setwinprob=1/(1+10**((l_elo_old-w_elo_old)/400))
        M.loc[i,"w_setwinprob"]=w_setwinprob
        total_sets=M.winner_setswon[i]+M.loser_setswon[i]
        M.loc[i,"total_sets"]=total_sets
        w_K=w_activityfactor*c/(w_match_number+o)**s1
        l_K=l_activityfactor*c/(l_match_number+o)**s1
        M.loc[i,"w_K"]=w_K
        M.loc[i,"l_K"]=l_K
        M.loc[i,"winner_elo"]=w_elo_old+w_K*M.winner_setswon[i]-w_setwinprob*w_K*total_sets
        M.loc[i,"loser_elo"]=l_elo_old+l_K*total_sets*w_setwinprob-M.winner_setswon[i]*l_K
        P.loc[winner_row,"EloRating"]=M.winner_elo[i]
        P.loc[loser_row,"EloRating"]=M.loser_elo[i]
        P.loc[winner_row,"match_number"]+=1
        P.loc[loser_row,"match_number"]+=1

    return M, P

def main():
    # Change working directory to the directory where file elo.py is located
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    print(os.getcwd())

    # Read matches.csv and make necessary transformations
    master = pd.read_csv('matches.csv')
    M=sort_master_table(master)
    M=M.loc[pd.notna(M.date2),:]
    M=transform_to_set_format(M)
    #M=M.loc[0:200]
    P = pd.read_csv('elo_ratings_yearend_2009.csv')
    all_names = set(M.winner_name).union(set(M.loser_name))
    available_names = set(P.Name)
    unavalaible_names = all_names.difference(available_names)
    P_unavailable = pd.DataFrame(unavalaible_names,columns=['Name'])
    P_unavailable["EloRating"]=1400
    P_unavailable["match_number"]=0
    P=pd.concat([P,P_unavailable]).reset_index(drop=True)
    #P.to_csv('P_start.csv')

    M=M
    P=P
    c=250
    o=20
    s1=0.6
    initial_elo=1400
    recentdays=75
    penaltyfactor=0.985

    M,P = update_elo(M,P,c,o,s1,initial_elo,recentdays,penaltyfactor)
    M.to_csv('matches2.csv')
    P.to_csv('players_elos.csv')

    print(M['date2'].dtypes)


main()
