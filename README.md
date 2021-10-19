# Covid Population Model
The COVID Population Model is used to predict the COVID patients admitted to hospitals per day of a state in the US. The Model requires access to Google Sheet, Google Drive, and Google Colab to run successfully.

## Overview
The Model consists of 3 parts: Google Sheet, Google Drive, and Google Colab.
- Google Sheet:
  - First Sheet: Setting 
  - Second Sheet: InfluxCountsByCompartment
- Google Drive:
  - Python files
  - CSV data
- Google Colab:
  - a notebook that runs the model

## Google Sheet
- Setting. User enters necessary information in the yellow cells. The grey cells are determined by yellow cells. The yellow cells are listed below:
  - Number of Warmup days
  - Number of Train days
  - Number of Test days
  - Start date of Test days
  - Name of the state of interest
  - Abbreviate of the state of interest
  - Priors on transition in alpha and beta values (transition probability distribution of beliefs before evidence):
    1. A: covidestim infected -> symptoms
    2. M: covidestim symptoms -> severe
    3. G: covidestim severe -> death
  - Priors on duration in lambda, sigma, nu, tau (duration probability distribution of beliefs before evidence):
    1. A: covidestim infected -> symptoms
    2. X: covidestim symptoms -> severe
    3. G: covidestim severe -> death
  - transition window: maximum number of days of transitioning from one state to another
  - T_serial: fixed serial interval between successive infections
  - learning rate: step size of each iteration in training the model.
  - vax_asymp_risk: effective percentage of vaccines at preventing infection
  - vax_mild_risk: effective percentage of vaccines at preventing symptomatic
  - vax_extreme_risk: effective percentage of vaccines at preventing hospitalization


## Google Drive
- Python files:
  - data.py
  - plots.py
  - model.py
  - sheet.py
- data:
  - covidestim: prior data
  - hhs: hospital admission data
  - owid: vaccination data

## Google Colab
This is where an user accesses and runs the model. Detailed instructions are shown in the notebook. 

## User Procedure
- Preparation
  1. Download the Google Colab notebook, Google Sheet, python files, data from Github and store them in the same directory in your Google Drive
  2. Ensure the formated Google Sheet has a sharable link. The template Google Sheet link is at https://docs.google.com/spreadsheets/d/1nLvScw4k2d79L1Rc2NxHFOupuqiEurLsqwWNtaRZB50/edit#gid=0. You can save it as your own Google Sheet and make sure it has a sharable link. 
- Fill in the yellow cells in the Google Sheet
- Open the Google Colab notebook
  1. run the first cell: authorize Google Colab notebook to access the Google Drive directory
  2. run the second cell: access the Google Drive directory from Google Colab notebook. (To see the location of the directorry, check "Files" on the left side of the notebook)
  3. run the third cell: load in the model modules to the notebook
  4. run the fourth cell: 
    - enter the link of the sharable Google Sheet
    - authorize access to Google Sheet
    - model runs by displaying iteration progress
    - model finishes running and displays the plot as result
    - check the InfluxCountsByCompartment sheet in Google Sheet to inspect detailed statistics displayed in the resulting plot
  
