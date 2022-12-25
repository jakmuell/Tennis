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
from elo_functions import *

def main():
    # Change working directory to the directory where file elo.py is located
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    print(os.getcwd())

    # Read matches.csv
    master = pd.read_csv('matches.csv')

    # Add columns surface and tourney_level
    T = pd.read_csv('tournaments.csv')
    T = T.loc[:,["id","surface","tourney_level"]]
    master = pd.merge(master,T,how="left",left_on="tourney_id",right_on='id')

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
    M = M.loc[:,["match_id","winner_previous_match","loser_previous_match","winner_elo","loser_elo","winner_elo_surface","loser_elo_surface"]]
    M.to_csv('elos.csv',index=False)
    print('Succesfully wrote to file \"elos.csv\".')
    P.to_csv('players_elos.csv',index=False)
    print('Succesfully wrote to file \"players_elos.csv\".')
    
    P_small = P.loc[0:9,["Name","elo_overall"]]
    print("Just for fun. This is the top 10 according to overall elo:")
    print(P_small)
main()
