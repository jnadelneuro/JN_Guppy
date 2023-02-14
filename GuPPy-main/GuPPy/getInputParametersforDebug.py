# -*- coding: utf-8 -*-
"""
Created on Sat Feb  4 10:27:05 2023

@author: jacob
"""
import os
import subprocess
import json
import panel as pn 
import numpy as np
import pandas as pd
from preprocess import extractTsAndSignal
from visualizePlot import visualizeResults
from saveStoresList import execute_autoRK_JN
pn.extension()

timeForLightsTurnOn = pn.widgets.LiteralInput(name='Eliminate first few seconds (int)', value=2, type=int, width=250)

isosbestic_control = pn.widgets.Select(name='Isosbestic Control Channel? (bool)', value=True, options=[True, False], width=250)

numberOfCores = pn.widgets.LiteralInput(name='# of cores (int)', value=5, type=int, width=100)

combine_data = pn.widgets.Select(name='Combine Data? (bool)', value=False, options=[True, False], width=125)

computePsth = pn.widgets.Select(name='z_score and/or \u0394F/F? (psth)', options=['Both', 'z_score', 'dff'], width=250)

transients = pn.widgets.Select(name='z_score and/or \u0394F/F? (transients)', options=['Both', 'z_score', 'dff'], width=250)

plot_zScore_dff = pn.widgets.Select(name='z-score plot and/or \u0394F/F plot?', options=['z_score', 'dff', 'Both', 'None'], value='z_score', width=250)

moving_wd = pn.widgets.LiteralInput(name='Moving Window for transients detection (s) (int)', value=15, type=int, width=250)

highAmpFilt = pn.widgets.LiteralInput(name='HAFT (int)', value=3, type=int, width=120)

transientsThresh = pn.widgets.LiteralInput(name='TD Thresh (int)', value=3, type=int, width=120)

moving_avg_filter = pn.widgets.LiteralInput(name='Window for Moving Average filter (int)', value=100, type=int, width=250)

removeArtifacts = pn.widgets.Select(name='removeArtifacts? (bool)', value=False, options=[True, False], width=125)

artifactsRemovalMethod = pn.widgets.Select(name='removeArtifacts method', 
                                           value='replace with NaN', 
                                           options=['concatenate', 'replace with NaN'],
                                          width=100)

# JN ADDING 2/4/23
# this is to add a button that will let me select among storenames based on experiment
storeNameSelect = pn.widgets.Select(name='storenames set', 
                                           value='ASAP', 
                                           options=['ASAP', 'RI60'],
                                          width=250)


no_channels_np = pn.widgets.LiteralInput(name='Number of channels (Neurophotometrics only)',
                                        value=2, type=int, width=250)

z_score_computation = pn.widgets.Select(name='z-score computation Method', 
                                        options=['standard z-score', 'baseline z-score', 'modified z-score'], 
                                        value='standard z-score', width=200)
baseline_wd_strt = pn.widgets.LiteralInput(name='Baseline Window Start Time (s) (int)', value=0, type=int, width=200)
baseline_wd_end = pn.widgets.LiteralInput(name='Baseline Window End Time (s) (int)', value=0, type=int, width=200)

explain_z_score = pn.pane.Markdown("""
                                   ***Note :***<br>
                                   - Details about z-score computation methods are explained in Github wiki.<br>
                                   - The details will make user understand what computation method to use for 
                                   their data.<br>
                                   - Baseline Window Parameters should be kept 0 unless you are using baseline<br> 
                                   z-score computation method. The parameters are in seconds.
                                   """, width=500)

explain_nsec = pn.pane.Markdown("""
                                - ***Time Interval :*** To omit bursts of event timestamps, user defined time interval
                                is set so that if the time difference between two timestamps is less than this defined time
                                interval, it will be deleted for the calculation of PSTH.
                                - ***Compute Cross-correlation :*** Make this parameter ```True```, when user wants
                                to compute cross-correlation between PSTHs of two different signals or signals 
                                recorded from different brain regions.
                                """, width=500)

nSecPrev = pn.widgets.LiteralInput(name='Seconds before 0 (int)', value=-10, type=int,  width=120)

nSecPost = pn.widgets.LiteralInput(name='Seconds after 0 (int)', value=20, type=int,  width=120)

computeCorr = pn.widgets.Select(name='Compute Cross-correlation (bool)', 
                                        options=[True, False], 
                                        value=False, width=160)

timeInterval = pn.widgets.LiteralInput(name='Time Interval (s)', value=2, type=int,  width=200)

bin_psth_trials = pn.widgets.LiteralInput(name='Time (mins) to bin PSTH trials (int)', value=0, type=int,  width=200)

explain_baseline = pn.pane.Markdown("""
                                    ***Note :***<br>
                                    - If user does not want to do baseline correction, 
                                    put both parameters 0.<br>
                                    - If the first event timestamp is less than the length of baseline
                                    window, it will be rejected in the PSTH computation step.<br>
                                    - Baseline parameters must be within the PSTH parameters 
                                    set in the PSTH parameters section.
                                    """, width=500)

baselineCorrectionStart = pn.widgets.LiteralInput(name='Baseline Correction Start time(int)', value=-7, type=int, width=200)

baselineCorrectionEnd = pn.widgets.LiteralInput(name='Baseline Correction End time(int)', value=-2, type=int, width=200)

zscore_param_wd = pn.WidgetBox("### Z-score Parameters", explain_z_score,
                                                         z_score_computation,
                                                         pn.Row(baseline_wd_strt, baseline_wd_end),
                                                         width=500, height=350)

psth_param_wd = pn.WidgetBox("### PSTH Parameters", explain_nsec, 
                                                    pn.Row(nSecPrev, nSecPost, computeCorr), 
                                                    pn.Row(timeInterval, bin_psth_trials), 
                                                    width=500, height=350)

baseline_param_wd = pn.WidgetBox("### Baseline Parameters", explain_baseline, 
                                 pn.Row(baselineCorrectionStart, baselineCorrectionEnd), 
                                 width=500, height=300)

peak_explain = pn.pane.Markdown("""
                                ***Note :***<br>
                                - Peak and area are computed between the window set below.<br>
                                - Peak and AUC parameters must be within the PSTH parameters set in the PSTH parameters section.<br>
                                - Please make sure when user changes the parameters in the table below, click on any other cell after 
                                   changing a value in a particular cell.
                                """, width=500)


start_end_point_df = pd.DataFrame({'Peak Start time': [-2.0, -2.0, 0.0, -5.0, 0.0, 5.0, -1.0, 0.0, -0.5, 0.0], 
                                   'Peak End time':   [2.0, 0.0, 2.0, 0.0, 3.0, 10.0, 0.0, 1.0, 0.0, 0.5]})

df_widget = pn.widgets.DataFrame(start_end_point_df, name='DataFrame', 
                                 auto_edit=True, show_index=False, row_height=20, width=450)


peak_param_wd = pn.WidgetBox("### Peak and AUC Parameters", 
                             peak_explain, df_widget,
                            height=400) 



mark_down_2 = pn.pane.Markdown("""**Select folders for the average analysis from the file selector below**""", width=600)

files_2 = pn.widgets.FileSelector('~', name='folderNamesForAvg', height=300, width=800)

averageForGroup = pn.widgets.Select(name='Average Group? (bool)', value=False, options=[True, False], width=400)

visualizeAverageResults = pn.widgets.Select(name='Visualize Average Results? (bool)', 
                                            value=False, options=[True, False], width=400)

visualize_zscore_or_dff = pn.widgets.Select(name='z-score or \u0394F/F? (for visualization)', options=['z_score', 'dff'], width=400)

#path = pn.widgets.TextAreaInput(name='Location to Input Parameters file', width=300, height=100)

#individual_analysis_wd_1 = pn.Column(mark_down_1, files_1, width=800)



def getInputParameters():
    #abspath = getAbsPath()
    inputParameters = {
      #  "abspath": abspath[0],
     #   "folderNames": files_1.value,
        "numberOfCores": numberOfCores.value,
        "combine_data": combine_data.value,
        "isosbestic_control": isosbestic_control.value,
        "timeForLightsTurnOn": timeForLightsTurnOn.value,
        "filter_window": moving_avg_filter.value,
        "storeNameSelect" : storeNameSelect.value,
        "removeArtifacts": removeArtifacts.value,
        "artifactsRemovalMethod": artifactsRemovalMethod.value,
        "noChannels": no_channels_np.value,
        "zscore_method": z_score_computation.value,
        "baselineWindowStart": baseline_wd_strt.value,
        "baselineWindowEnd": baseline_wd_end.value,
        "nSecPrev": nSecPrev.value,
        "nSecPost": nSecPost.value,
        "computeCorr": computeCorr.value,
        "timeInterval": timeInterval.value,
        "bin_psth_trials": bin_psth_trials.value,
        "baselineCorrectionStart": baselineCorrectionStart.value,
        "baselineCorrectionEnd": baselineCorrectionEnd.value,
        "peak_startPoint": list(df_widget.value['Peak Start time']), #startPoint.value,
        "peak_endPoint": list(df_widget.value['Peak End time']), #endPoint.value,
        "selectForComputePsth": computePsth.value,
        "selectForTransientsComputation": transients.value,
        "moving_window": moving_wd.value,
        "highAmpFilt": highAmpFilt.value,
        "transientsThresh": transientsThresh.value,
        "plot_zScore_dff": plot_zScore_dff.value,
        "visualize_zscore_or_dff": visualize_zscore_or_dff.value,
        "folderNamesForAvg": files_2.value,
        "averageForGroup": averageForGroup.value,
        "visualizeAverageResults": visualizeAverageResults.value
    }
    return inputParameters

inputParameters = getInputParameters()
execute_autoRK_JN(inputParameters)