# Covid Population Model
**NEW SPREADSHEET FOR TOTAL COUNT MODEL**: https://docs.google.com/spreadsheets/d/1Yj1aTiNa_ZFFbMH1IcuFYK5c774kK_vXzsu9sbxeS2A/edit#gid=0

This repository contains code for a preliminary version of the Tufts Susceptible-to-Hospital Forecasting Model for COVID-19. This mechanistic probabilistic model describes how COVID-19 might spread in the broader population of a target region and produce daily hospital admissions, general ward population counts, ICU counts, and death counts due to COVID-19. A key feature of the model is that it can account for vaccination and its impact on disease spread and need for hospital resources.

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
  - Third Sheet: ***Context(Rt, Vax_Pct)***
    - where default Rt(viral reproductive constant which determines how fast the virus spreads) and Vaccination Percentage of the given state are shown. Can be modified by users and project under different context.
  - Fourth Sheet: ***AllParam***
    - where all parameters are contained
  - Fifth Sheet: ***Durations(Vax)***
    - where learned duration parameters for vaccinated population are shown. Can be modified by users to project under different paramters.
  - Sixth Sheet: ***Durations(Unvax)***
    - where learned duration parameters for unvaccinated population are shown. Can be modified by users to project under different paramters.
  - Seventh Sheet: ***Transitions***
    - where learned transition parameters for unvaccinated population are shown. Can be modified by users to project under different paramters.
  - A shared folder on Google Drive, containing: Python files defining the model itself (users should not need to edit these)
  - model_config.json. A json file that contains all parameters.
  - CSV files defining observed data that can be used for training the model. Contains:
    - [Daily hospital admissions for all 50 states](https://healthdata.gov/api/views/g62h-syeh/rows.csv?accessType=DOWNLOAD)
    - [Daily vaccination information for all 50 states](https://data.cdc.gov/api/views/unsk-b7fc/rows.csv?accessType=DOWNLOAD)
    - [Estimates from the CovidEstim project](https://covidestim.s3.us-east-2.amazonaws.com/latest/state/estimates.csv) about the effective reproduction number in each state over time
- A cloud notebook in Google Colab:
  - Executing this notebook is what “runs” the model and ultimately produces the forecast that is written to the shared spreadsheet 


## Step-by-Step Guide to Producing your own forecasts 
- Prepare a shared folder in Google Drive 
  - Download all the files from this Github ( the Google Colab notebook, Google Sheet, python files, json file, data from Github and store them in the same directory in your Google Drive. Please remember the name and location of the directory in your Google Drive. You will need it when edit the second cell of the notebook.
- Within this folder, create a  Google Sheet
  - You should copy the template Google Sheet link is at https://docs.google.com/spreadsheets/d/1E8NoSwS7cCBYOuWp1trKhyXd3mBMQyL5FjHhGh0rOOw/edit#gid=0. You can save it as your own Google Sheet and make sure it has a sharable link.
- Edit the Google Sheet
  - Fill in the yellow cells to specify the desired US state and training period and test period
- Run the model by opening the Google Colab notebook in Google Drive
  - run the 1st cell: authorize Google Colab notebook to access the Google Drive directory
  - run the 2nd cell: access the Google Drive directory from Google Colab notebook. (To see the location of the directory, check "Files" on the left side of the notebook)
  - run the 3rd cell: load in the model modules to the notebook
  - run the 4th cell: enter the link of the sharable Google Sheet
  - run the 5th cell: load the default Rt and Vaccination Rate to Google Sheet so that user can edit
  - run the 6th cell: load in all parameters value to spreadsheet from json file
  - run the 7th cell: train the model and make the prediction 
    - Monitor the progress and verify expected output
    - The provided example finishes in about 5-10 minutes
    - After finishing, a diagnostic plot of the forecasted daily hospital admissions over time (as well as other quantities) is displayed
    - Check the InfluxCountsByCompartment sheet in Google Sheet to inspect detailed values produced by the forecast and displayed in the plot. Check the Param sheet to inspect exact values of learned parameters.
   - run the 8th cell: user can customize parameters in AllParam in Google Sheet and generate new json file that contains the latest customized parameters. After a new json file is generated, user can go back to run sixth cell to make projection with new parameters
   - run the 9th cell: enter other state in Setting in Google Sheet, the program automatically adjusts the transfer ratio and make projections for the other selected state with current learned parameters
   - run the 10th cell: project with user-customized ratios
   - run the 11th cell: users can change parameter values in user interface sheet (Durations(Vax), Durations(Unvax), Transitions) and sync the changed values on AllParam sheet.


## Detailed Guide to Google Sheet
- **Setting**. User enters necessary information in the yellow cells. The grey cells are determined by yellow cells. The yellow cells are listed below:
  - Number of Warmup days
  - Number of Train days
  - Number of Test days
  - Start date of Test days
  - Name of the state of interest
  - Abbreviate of the state of interest
  - transition window: maximum number of days of transitioning from one state to another
  - learning rate: step size of each iteration in training the model.
  - transfer_ratio_GeneralWard: ratio of number of patients in General Ward at first day of training between current state and new selected state
  - transfer_ratio_ICU: ratio of number of patients in ICU at first day of training between current state and new selected state
- **InfluxCountsByCompartment**. The result sheet.
  - PERIOD: distinguish warmup, training, and testing period
  - TIMESTEP: 0 is the beginning of traning period and any negative timestep refers to warmup period
  - DATE
  - general_ward_in: number of people entering general ward on the given day
  - general_ward_count: number of people in general ward on the given day
  - ICU_count: number of people in ICU on the given day
  - deaths_covid: number of people died due to COVID-19 on the given day
- **Context(Rt, Vax_Pct)**. The context sheet.
  - Rt: viral reproductive constant which determines how fast the virus spreads
  - Vax_Pct: Vaccination Rate of the given state on the given day.
- **AllParam**. the sheet that contains all parameters and allows user customization
- ***Durations(Vax)***
- ***Durations(Unvax)***
- ***Transitions***
## Detailed Guide to Google Drive shared folder
- Python files:
  - data.py (read in and store all the data)
  - plots.py (plot the results)
  - model.py (contain model functionalities)
  - sheet.py (integrate Google Sheet functionalities)
  - project.py (contains model functionalities without training)
  - convert.py
  - model_config.py
- data (to acquire the latest data, click download links below):
  - [covidestim]([download link](https://covidestim.s3.us-east-2.amazonaws.com/latest/state/estimates.csv)): Estimates from the [CovidEstim project](https://covidestim.org/) about the effective reproduction number in each state over time
  - [hhs]([download link](https://healthdata.gov/api/views/g62h-syeh/rows.csv?accessType=DOWNLOAD)): Daily hospital admissions for all 50 states from [Healthdata.gov](https://healthdata.gov/)
  - [owid]([download link](https://data.cdc.gov/api/views/unsk-b7fc/rows.csv?accessType=DOWNLOAD)): Daily vaccination information for all 50 states from [Centers for Disease Control and Prevention](https://www.cdc.gov/)

## Google Colab
This is where an user accesses and runs the model. Detailed instructions are shown in the notebook. 

