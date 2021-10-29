# Covid Population Model
This repository contains code for a preliminary version of the Tufts Susceptible-to-Hospital Forecasting Model for COVID-19. This mechanistic probabilistic model describes how COVID-19 might spread in the broader population of a target region and produce daily hospital admissions. A key feature of the model is that it can account for vaccination and its impact on disease spread and need for hospital resources.

We hope this codebase can help users answer questions like:
- Given what we have seen from April thru July 2021, how many admissions to the hospital will the state of Massachusetts see in August?
- If a new drug is rolled out that can reduce the number of symptomatic patients that need to go to the hospital by 10%, how does that change the total demand for beds in August and September?
- If a new variant arises that would increase the effective reproduction rate (R<sub>T</sub>) from 1.0 to 1.1 over the next month, how would demand for total hospital beds change?

All a user needs to provide is a desired U.S. state and time period of interest (e.g. fit the model to data from MA from 04/01/2021-07/31/2021 and make a forecast for 08/2021). We provide sensible defaults for all a priori assumptions and settings, but users can specify their own values if desired.

We support a simple in-browser workflow that allows a user with access to Google Sheets, Google Drive, and Google Collaboratory to fit the model and see projections using the cloud, without needing any installation. All outputs are written to a spreadsheet, enabling the user to easily process the forecasts further as desired.

For users without access to Google cloud resources, you can install the software locally on your machine (using a provided Anaconda environment) and run the notebook locally using open-source Jupyter notebook software. Support for the output to be written to a local Excel spreadsheet is in progress.

## Quick Links: 
[Overview](#overview-using-the-model-from-your-browser) | [Step-by-step guide](#step-by-step-guide-to-producing-your-own-forecasts) | [Team](#team-and-contact-info)

## Team and Contact Info

For questions or concerns about the code, please report an Issue
This is a joint collaboration between Tufts University computer science researchers and collaborators at the Tufts Medical Center’s Center for Evaluation of Value and Risk in health (CEVR).

Lead personnel:
- Jason Xiang (research assistant, Tufts CS)
- Kyle Heuton (research assistant, Tufts CS)
- Sibyl Sun (research assistant, Tufts CS)
- Michael C Hughes (PI, Tufts CS)
- Samuel W (research assistant, TMC CEVR)
- Josh Cohen (PI, TMC CEVR)

For general questions, please email mhughes@cs.tufts.edu.


## Overview: Using the Model from your browser
For the in-browser workflow, users will interact with 3 parts: 
- A shared workbook on Google Sheet containing multiple sheets (tabs):
  - First Sheet: ***Settings***
    - where we define the desired scenario (train on MA data from 04-07/2021)
    - where we define the desired assumptions (see below)
  - Second Sheet: ***InfluxCountsByCompartment***
    - where results of the daily forecast are written to (see below)
  - A shared folder on Google Drive, containing:Python files defining the model itself (users should not need to edit these)
  - CSV files defining observed data that can be used for training the model. Contains:
    - [Daily hospital admissions for all 50 states](https://healthdata.gov/api/views/g62h-syeh/rows.csv?accessType=DOWNLOAD)
    - [Daily vaccination information for all 50 states](https://data.cdc.gov/api/views/unsk-b7fc/rows.csv?accessType=DOWNLOAD)
    - [Estimates from the CovidEstim project](https://covidestim.s3.us-east-2.amazonaws.com/latest/state/estimates.csv) about the effective reproduction number in each state over time
- A cloud notebook in Google Colab:
  - Executing this notebook is what “runs” the model and ultimately produces the forecast that is written to the shared spreadsheet 


## Step-by-Step Guide to Producing your own forecasts 
- Prepare a shared folder in Google Drive 
  - Download all the files from this Github ( the Google Colab notebook, Google Sheet, python files, data from Github and store them in the same directory in your Google Drive. Please remember the name and location of the directory in your Google Drive. You will need it when edit the second cell of the notebook.

- Within this folder, create a  Google Sheet
  - You should copy the template Google Sheet link is at https://docs.google.com/spreadsheets/d/1nLvScw4k2d79L1Rc2NxHFOupuqiEurLsqwWNtaRZB50/edit#gid=0. You can save it as your own Google Sheet and make sure it has a sharable link.
- Edit the Google Sheet
  - Fill in the yellow cells to specify the desired US state and training period and test period
  - Adjust any a priori assumptions as needed
  - Adjust any optimization settings as needed
- Run the model by opening the Google Colab notebook in Google Drive
  - run the first cell: authorize Google Colab notebook to access the Google Drive directory
  - run the second cell: access the Google Drive directory from Google Colab notebook. (To see the location of the directory, check "Files" on the left side of the notebook)
  - run the third cell: load in the model modules to the notebook
  - run the fourth cell:
    - enter the link of the sharable Google Sheet
    - authorize access to Google Sheet
    - After all authorization is approved, the model should run and display progress iteration-by-iteration as its fitting procedure runs 
- Monitor the progress and verify expected output
  - The provided example finishes in about 5-10 minutes
   - After finishing, a diagnostic plot of the forecasted daily hospital admissions over time (as well as other quantities) is displayed
   - Check the InfluxCountsByCompartment sheet in Google Sheet to inspect detailed values produced by the forecast and displayed in the plot
 
To check out the live demonstration of how to use the model, click [here](https://tufts.zoom.us/rec/share/ML_Lrut3BxHqDcE5dTWMe16hYtQC_82c3f2uvUWRcXT_LGOdmhlDlJTAwF9AMb-.5u4RwunOERbZTuLt?startTime=1635196884000).

## Detailed Guide to Google Sheet
- Setting. User enters necessary information in the yellow cells. The grey cells are determined by yellow cells. The yellow cells are listed below:
  - Number of Warmup days
  - Number of Train days
  - Number of Test days
  - Start date of Test days
  - Name of the state of interest
  - Abbreviate of the state of interest
  - Priors(transition probability distribution of beliefs before evidence) in alpha and beta values (alpha and beta are the two parameters that determine the shape of Beta Distributions below):
    1. M: infected -> symptoms
    2. X: symptoms -> severe
    3. G: severe -> death
  - Priors(duration probability distribution of beliefs before evidence) in (lambda, sigma), (nu, tau), which represent the paramters (mean, variance) of Normal Distribution. Particularly, lambda is mode number of days until transition to the next compartment:
    1. M: infected -> symptoms
    2. X: symptoms -> severe
    3. G: severe -> death
  - transition window: maximum number of days of transitioning from one state to another
  - T_serial: fixed serial interval between successive infections
  - learning rate: step size of each iteration in training the model.
  - vax_asymp_risk: effective percentage of vaccines at preventing infection
  - vax_mild_risk: effective percentage of vaccines at preventing symptomatic
  - vax_extreme_risk: effective percentage of vaccines at preventing hospitalization


## Detailed Guide to Google Drive shared folder
- Python files:
  - data.py (read in and store all the data)
  - plots.py (plot the results)
  - model.py (contain model functionalities)
  - sheet.py (integrate Google Sheet functionalities)
- data (to acquire the latest data, click download links below):
  - [covidestim]([download link](https://covidestim.s3.us-east-2.amazonaws.com/latest/state/estimates.csv)): Estimates from the [CovidEstim project](https://covidestim.org/) about the effective reproduction number in each state over time
  - [hhs]([download link](https://healthdata.gov/api/views/g62h-syeh/rows.csv?accessType=DOWNLOAD)): Daily hospital admissions for all 50 states from [Healthdata.gov](https://healthdata.gov/)
  - [owid]([download link](https://data.cdc.gov/api/views/unsk-b7fc/rows.csv?accessType=DOWNLOAD)): Daily vaccination information for all 50 states from [Centers for Disease Control and Prevention](https://www.cdc.gov/)

## Google Colab
This is where an user accesses and runs the model. Detailed instructions are shown in the notebook. 

