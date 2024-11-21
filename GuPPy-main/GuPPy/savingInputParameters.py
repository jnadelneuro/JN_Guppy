#!/usr/bin/env python
# coding: utf-8

# In[5]:


#%load_ext autoreload
#%autoreload 2

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

def make_dir(filepath):
    op = os.path.join(filepath, 'inputParameters')
    if not os.path.exists(op):
        os.mkdir(op)
    return op


os.chdir(r'C:\Users\jacob\OneDrive\Documents\GitHub\JN_Guppy\GuPPy-main\GuPPy')
template = pn.template.MaterialTemplate(title='Input Parameters GUI')

#pn.config.sizing_mode = 'stretch_width'

mark_down_1 = pn.pane.Markdown("""**Select folders for the analysis from the file selector below**""", width=600)
#previously '~', no C:\Users\rfkov\Documents\SynapseData\LBN_Synapse_Data
files_1 = pn.widgets.FileSelector(r'D:\Data_analysis\Lerner_Lab\aCUS\aCUS_Sept2024_Avoidance', name='folderNames', height=300, width=800)


explain_time_artifacts = pn.pane.Markdown("""
                                            - ***Number of cores :*** Number of cores used for analysis. Try to 
                                            keep it less than the number of cores in your machine. 
                                            - ***Combine Data? :*** Make this parameter ``` True ``` if user wants to combine 
                                            the data, especially when there is two different 
                                            data files for the same recording session.<br>
                                            - ***Isosbestic Control Channel? :*** Make this parameter ``` False ``` if user
                                            does not want to use isosbestic control channel in the analysis.<br>
                                            - ***Eliminate first few seconds :*** It is the parameter to cut out first x seconds
                                            from the data. Default is 1 seconds.<br>
                                            - ***Window for Moving Average filter :*** The filtering of signals
                                            is done using moving average filter. Default window used for moving 
                                            average filter is 100 datapoints. Change it based on the requirement.<br>
                                            - ***Moving Window (transients detection) :*** Transients in the z-score 
                                            and/or \u0394F/F are detected using this moving window. 
                                            Default is 15 seconds. Change it based on the requirement.<br>
                                            - ***High Amplitude filtering threshold (HAFT) (transients detection) :*** High amplitude
                                            events greater than x times the MAD above the median are filtered out. Here, x is 
                                            high amplitude filtering threshold. Default is 2.
                                            - ***Transients detection threshold (TD Thresh):*** Peaks with local maxima greater than x times
                                            the MAD above the median of the trace (after filtering high amplitude events) are detected
                                            as transients. Here, x is transients detection threshold. Default is 3.
                                            - ***Number of channels (Neurophotometrics only) :*** Number of
                                            channels used while recording, when data files has no column names mentioning "Flags" 
                                            or "LedState".
                                            - ***removeArtifacts? :*** Make this parameter ``` True``` if there are 
                                            artifacts and user wants to remove the artifacts.
                                            - ***removeArtifacts method :*** Selecting ```concatenate``` will remove bad 
                                            chunks and concatenate the selected good chunks together.
                                            Selecting ```replace with NaN``` will replace bad chunks with NaN
                                            values.
                                            """)

timeForLightsTurnOn = pn.widgets.LiteralInput(name='Eliminate first few seconds (int)', value=2, type=int, width=250)

isosbestic_control = pn.widgets.Select(name='Isosbestic Control Channel? (bool)', value=True, options=[True, False], width=250)

numberOfCores = pn.widgets.LiteralInput(name='# of cores (int)', value=5, type=int, width=100)

combine_data = pn.widgets.Select(name='Combine Data? (bool)', value=False, options=[True, False], width=125)

computePsth = pn.widgets.Select(name='z_score and/or \u0394F/F? (psth)', options=['Both', 'z_score', 'dff'], value='z_score', width=250)

transients = pn.widgets.Select(name='z_score and/or \u0394F/F? (transients)', options=['Both', 'z_score', 'dff'], value='z_score', width=250)

plot_zScore_dff = pn.widgets.Select(name='z-score plot and/or \u0394F/F plot?', options=['z_score', 'dff', 'Both', 'None'], value='None', width=250)

moving_wd = pn.widgets.LiteralInput(name='Moving Window for transients detection (s) (int)', value=15, type=int, width=250)

highAmpFilt = pn.widgets.LiteralInput(name='HAFT (int)', value=3, type=int, width=120)

transientsThresh = pn.widgets.LiteralInput(name='TD Thresh (int)', value=3, type=int, width=120)

moving_avg_filter = pn.widgets.LiteralInput(name='Window for Moving Average filter (int)', value=100, type=int, width=250)

removeArtifacts = pn.widgets.Select(name='removeArtifacts? (bool)', value=True, options=[True, False], width=125)

artifactsRemovalMethod = pn.widgets.Select(name='removeArtifacts method', 
                                           value='replace with NaN', 
                                           options=['concatenate', 'replace with NaN'],
                                          width=100)

# JN ADDING 2/4/23
# this is to add a button that will let me select among storenames based on experiment
storeNameSelect = pn.widgets.Select(name='storenames set', 
                                           value='Avoid', 
                                           options=['ASAP', 'RI60',"Avoid"],
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


start_end_point_df = pd.DataFrame({'Peak Start time': [], 
                                   'Peak End time':   []})

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

individual_analysis_wd_2 = pn.Column(
                                    explain_time_artifacts, pn.Row(numberOfCores, combine_data), 
                                    storeNameSelect, isosbestic_control, timeForLightsTurnOn,
                                    moving_avg_filter, computePsth, transients, plot_zScore_dff, 
                                    moving_wd, pn.Row(highAmpFilt, transientsThresh),
                                    no_channels_np, pn.Row(removeArtifacts, artifactsRemovalMethod)
                                    )

group_analysis_wd_1 = pn.Column(mark_down_2, files_2, averageForGroup, width=800)

visualization_wd = pn.Row(visualize_zscore_or_dff, visualizeAverageResults, width=800)

def getInputParameters():
    abspath = getAbsPath()
    inputParameters = {
        "abspath": abspath[0],
        "folderNames": files_1.value,
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

def checkSameLocation(arr, abspath):
    #abspath = []
    for i in range(len(arr)):
        abspath.append(os.path.dirname(arr[i]))
    abspath = np.asarray(abspath)
    abspath = np.unique(abspath)
    if len(abspath)>1:
        raise Exception('All the folders selected should be at the same location')
    
    return abspath

def getAbsPath():
    arr_1, arr_2 = files_1.value, files_2.value 
    if len(arr_1)==0 and len(arr_2)==0:
        raise Exception('No folder is selected for analysis')
    
    abspath = []
    if len(arr_1)>0:
        abspath = checkSameLocation(arr_1, abspath)
    else:
        abspath = checkSameLocation(arr_2, abspath)
    
    abspath = np.unique(abspath)
    if len(abspath)>1:
        raise Exception('All the folders selected should be at the same location')
    return abspath

def onclickProcess(event=None):
    
    analysisParameters = {
        "combine_data": combine_data.value,
        "isosbestic_control": isosbestic_control.value,
        "timeForLightsTurnOn": timeForLightsTurnOn.value,
        "filter_window": moving_avg_filter.value,
        "removeArtifacts": removeArtifacts.value,
        "noChannels": no_channels_np.value,
        "zscore_method": z_score_computation.value,
        "baselineWindowStart": baseline_wd_strt.value,
        "baselineWindowEnd": baseline_wd_end.value,
        "nSecPrev": nSecPrev.value,
        "nSecPost": nSecPost.value,
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
        "transientsThresh": transientsThresh.value
    }
    for folder in files_1.value:
        with open(os.path.join(folder, 'GuPPyParamtersUsed.json'), 'w') as f:
            json.dump(analysisParameters, f, indent=4)
            
    #path.value = (os.path.join(op, 'inputParameters.json')).replace('\\', '/')
    print('Input Parameters File Saved.')

def onclickStoresList(event=None):
    inputParameters = getInputParameters()
    execute_autoRK_JN(inputParameters)

def onclickVisualization(event=None):
    inputParameters = getInputParameters()
    visualizeResults(inputParameters)
    
def onclickreaddata(event=None):
    read_progress.active=True
    inputParameters = getInputParameters()
    subprocess.call(["python", "readTevTsq.py", json.dumps(inputParameters)])
    read_progress.active=False
    
def onclickextractts(event=None):
    extract_progress.active=True
    inputParameters = getInputParameters()
    extractTsAndSignal(inputParameters)
    extract_progress.active=False
    
def onclickpsth(event=None):
    psth_progress.active=True
    inputParameters = getInputParameters()
    subprocess.call(["python", "computePsth.py", json.dumps(inputParameters)])
    subprocess.call(["python", "findTransientsFreqAndAmp.py", json.dumps(inputParameters)])
    psth_progress.active=False
    
mark_down_ip = pn.pane.Markdown("""**Step 1 : Save Input Parameters**""", width=500)
mark_down_ip_note = pn.pane.Markdown("""***Note : ***<br>
                                         - Save Input Parameters will save input parameters used for the analysis
                                         in all the folders you selected for the analysis (useful for future
                                         reference). All analysis steps will run without saving input parameters.
                                      """, width=500, sizing_mode="stretch_width")
save_button = pn.widgets.Button(name='Save to file...', button_type='primary', width=500, sizing_mode="stretch_width", align='end')
mark_down_storenames = pn.pane.Markdown("""**Step 2 : Open Storenames GUI <br> and save storenames**""", width=500)
open_storesList = pn.widgets.Button(name='RK_JN auto Storenames', button_type='primary', width=500, sizing_mode="stretch_width", align='end')
mark_down_read = pn.pane.Markdown("""**Step 3 : Read Raw Data**""", width=500)
read_rawData = pn.widgets.Button(name='Read Raw Data', button_type='primary', width=500, sizing_mode="stretch_width", align='end')
mark_down_extract = pn.pane.Markdown("""**Step 4 : Extract timestamps <br> and its correction**""", width=500)
extract_ts = pn.widgets.Button(name="Extract timestamps and it's correction", button_type='primary', width=500, sizing_mode="stretch_width", align='end')
mark_down_psth = pn.pane.Markdown("""**Step 5 : PSTH Computation**""", width=500)
psth_computation = pn.widgets.Button(name="PSTH Computation", button_type='primary', width=500, sizing_mode="stretch_width", align='end')
mark_down_visualization = pn.pane.Markdown("""**Step 6 : Visualization**""", width=500)
open_visualization = pn.widgets.Button(name='Open Visualization GUI', button_type='primary', width=500, sizing_mode="stretch_width", align='end')

read_progress = pn.widgets.Progress(name='Progress', active=False, width=200, sizing_mode="stretch_width")
extract_progress = pn.widgets.Progress(name='Progress', active=False, width=200, sizing_mode="stretch_width")
psth_progress = pn.widgets.Progress(name='Progress', active=False, width=200, sizing_mode="stretch_width")

save_button.on_click(onclickProcess)
open_storesList.on_click(onclickStoresList)
read_rawData.on_click(onclickreaddata)
extract_ts.on_click(onclickextractts)
psth_computation.on_click(onclickpsth)
open_visualization.on_click(onclickVisualization)


template.sidebar.append(mark_down_ip)
template.sidebar.append(mark_down_ip_note)
template.sidebar.append(save_button)
#template.sidebar.append(path)
template.sidebar.append(mark_down_storenames)
template.sidebar.append(open_storesList)
template.sidebar.append(mark_down_read)
template.sidebar.append(read_rawData)
template.sidebar.append(read_progress)
template.sidebar.append(mark_down_extract)
template.sidebar.append(extract_ts)
template.sidebar.append(extract_progress)
template.sidebar.append(mark_down_psth)
template.sidebar.append(psth_computation)
template.sidebar.append(psth_progress)
template.sidebar.append(mark_down_visualization)
template.sidebar.append(open_visualization)


psth_baseline_param = pn.Column(zscore_param_wd, psth_param_wd, baseline_param_wd, peak_param_wd)

widget = pn.Column(mark_down_1, files_1, pn.Row(individual_analysis_wd_2, psth_baseline_param))

#file_selector = pn.WidgetBox(files_1)
individual = pn.Card(widget, title='Individual Analysis', background='WhiteSmoke', width=850)
group = pn.Card(group_analysis_wd_1, title='Group Analysis', background='WhiteSmoke', width=850)
visualize = pn.Card(visualization_wd, title='Visualization Parameters', background='WhiteSmoke', width=850)

#template.main.append(file_selector)
template.main.append(individual)
template.main.append(group)
template.main.append(visualize)

template.show()


# In[ ]:





# In[ ]:




