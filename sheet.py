# -*- coding: utf-8 -*-
"""sheetModel1.5.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1RmnToue60tNIiXRPWhaqbZm6N5tKCQMI

## Imports
"""

# Commented out IPython magic to ensure Python compatibility.
# %load_ext autoreload
# %autoreload 2

import numpy as np
import tensorflow as tf

# Local imports from model.py, data.py
from model import CovidModel, Compartments, LogPoissonProb, get_logging_callbacks
from data import read_data, create_warmup
from plots import make_all_plots
import pandas as pd
from google.colab import auth
import gspread
from oauth2client.client import GoogleCredentials
import ipywidgets

def convert_date(date_str):
  date_list = date_str.split('-')
  return concatenate_list_data(date_list)

def concatenate_list_data(list):
    result= ''
    for element in list:
        result += str(element)
    return result

"""## Controllable Parameters

### Data details
"""
def run_sheetModel(sheetData, link, gc):

  warmup_start = convert_date(sheetData[2][2])
  warmup_end = convert_date(sheetData[2][3])
  train_start = convert_date(sheetData[3][2])
  train_end = convert_date(sheetData[3][3])
  test_start = convert_date(sheetData[4][2])
  test_end = convert_date(sheetData[4][3])

  state = sheetData[5][1]
  state_abbrev = sheetData[6][1]

  data_dir = './data'
  covid_estim_date = '20210901'
  hhs_date = '20210903'
  owid_date = '20210903'

  log_dir = './logs/test_run_1'

  """### Model Settings"""

  # How long can a person take to progress?
  transition_window = int(sheetData[17][1])

  # CovidEstim Hyper param
  T_serial = float(sheetData[18][1])

  """### Vaccine efficacy for incorrect warmup data split"""

  # Vaccines are 90% effective at preventing infection
  # according to a study of 4000 healthcare workers in early 2021
  # https://www.cdc.gov/mmwr/volumes/70/wr/mm7013e3.htm
  vax_asymp_risk = float(sheetData[21][1])
  # Vaccines are 94% effective at preventing symptomatic
  # according to a study of healthcare workers in early 2021
  # https://www.cdc.gov/mmwr/volumes/70/wr/mm7020e2.htm
  vax_mild_risk = float(sheetData[22][1])
  vax_extreme_risk = float(sheetData[23][1])
  # Vaccines are 94% effective at preventing hospitalization
  # according to a study of adults over 65 early 2021
  # https://www.cdc.gov/mmwr/volumes/70/wr/mm7018e1.htm?s_cid=mm7018e1_w
  vax_general_ward_risk = 0.94 # not used

  """### Model prior parameters"""

  # Parameters for the Beta distribution prior over rho, the probablility that
  # someone progresses to the next state. Here we use a uniform distribution
  # for all compartments, but we could specify a different prior for each M, X, G

  # Copied from covid estim
  # covidestim infected -> symptoms
  alpha_bar_M = float(sheetData[9][1])
  beta_bar_M = float(sheetData[9][2])
  # covidestim symptoms -> severe
  alpha_bar_X = float(sheetData[10][1])
  beta_bar_X = float(sheetData[10][2])
  # covid estim severe -> death
  alpha_bar_G = float(sheetData[11][1])
  beta_bar_G = float(sheetData[11][2])

  # Parameters for the positive truncated Normal distribution prior over lambda, the rate
  # parameter of the Poisson distribution controlling pi,
  # which determines how quickly someone who progresses does so +
  # Parameters for the positive truncated Normal distribution prior over nu, the parameter used
  # to scale the poisson distribution governed by pi, allowing for a more expressive
  # range of possible transition days

  # We choose these values to match the gamma priors in covid estim
  # Covidestim infected -> symptoms = Gamma(3.41, 0.61)
  lambda_bar_M = float(sheetData[13][1])
  sigma_bar_M = float(sheetData[13][2])
  nu_bar_M = float(sheetData[13][3])
  tau_bar_M = float(sheetData[13][4])

  # Covidestim Symptoms -> severe = Gamma(1.72, 0.22)
  lambda_bar_X = float(sheetData[14][1])
  sigma_bar_X = float(sheetData[14][2])
  nu_bar_X = float(sheetData[14][3])
  tau_bar_X = float(sheetData[14][4])

  # Covidestim severe -> death = Gamma(2.10, 0.23)
  lambda_bar_G = float(sheetData[15][1])
  sigma_bar_G = float(sheetData[15][2])
  nu_bar_G = float(sheetData[15][3])
  tau_bar_G = float(sheetData[15][4])


  # Learning rate
  learning_rate = float(sheetData[19][1])

  """## Read data"""

  df = read_data(data_dir=data_dir,
                 covid_estim_date=covid_estim_date,
                 hhs_date=hhs_date,
                 owid_date=owid_date,
                 state=state, state_abbrev=state_abbrev)

  # Optional, replace covidestim warmup data with fixed constants
  #df.loc[:,'extreme'] = 7*df.loc[:,'general_ward']
  #df.loc[:,'mild'] = 10*df.loc[:,'extreme']
  #df.loc[:,'asymp'] = 1.5*df.loc[:,'mild']

  """## Create warmup using incorrect efficacy assumption"""

  warmup_asymp, warmup_mild, warmup_extreme = create_warmup(df, 
                                                            warmup_start, 
                                                            warmup_end,
                                                            vax_asymp_risk,
                                                            vax_mild_risk,
                                                            vax_extreme_risk)

  """## Create training Rt and outcome"""

  training_rt = df.loc[train_start:train_end,'Rt'].values
  training_general_ward = df.loc[train_start:train_end,'general_ward'].values

  # Start the model from the training period so we are continuous
  testing_rt = df.loc[train_start:test_end,'Rt'].values
  testing_general_ward = df.loc[train_start:test_end,'general_ward'].values

  """## Build Model"""

  model = CovidModel(transition_window, T_serial,
                       alpha_bar_M, beta_bar_M, alpha_bar_X, beta_bar_X, alpha_bar_G, beta_bar_G,
                   lambda_bar_M, sigma_bar_M, lambda_bar_X, sigma_bar_X, lambda_bar_G, sigma_bar_G,
                   nu_bar_M, tau_bar_M, nu_bar_X, tau_bar_X, nu_bar_G, tau_bar_G)

  """## Fit model"""

  # Define optimizer
  optimizer = tf.keras.optimizers.Adam(
      learning_rate=learning_rate,
  )

  loss = LogPoissonProb()

  model.compile(loss=loss, optimizer=optimizer, run_eagerly=True)
  callbacks = get_logging_callbacks(log_dir)

  # Awkwardly stuff everything into an array

  model.fit(x=(np.asarray([training_rt]),
         np.asarray([warmup_asymp[0]]), np.asarray([warmup_asymp[1]]),
         np.asarray([warmup_mild[0]]), np.asarray([warmup_mild[1]]),
         np.asarray([warmup_extreme[0]]), np.asarray([warmup_extreme[1]])),
               y=np.asarray([training_general_ward]),
           epochs=200, batch_size=0, callbacks=callbacks)

  """## Get predictions for train and test"""

  train_preds = model((training_rt,
         warmup_asymp[0], warmup_asymp[1],
         warmup_mild[0], warmup_mild[1],
         warmup_extreme[0], warmup_extreme[1]))

  test_preds = model((testing_rt,
         warmup_asymp[0], warmup_asymp[1],
         warmup_mild[0], warmup_mild[1],
         warmup_extreme[0], warmup_extreme[1]))
      
  test_loss = loss(tf.convert_to_tensor(testing_general_ward, dtype=tf.float32), test_preds)

  """## Call model with special flag to get values of all internal compartments"""

  forecasted_fluxes = model((testing_rt,
         warmup_asymp[0], warmup_asymp[1],
         warmup_mild[0], warmup_mild[1],
         warmup_extreme[0], warmup_extreme[1]), return_all=True)

  all_days = df.loc[warmup_start:test_end].index.values
  warmup_days = df.loc[warmup_start:warmup_end].index.values
  train_days = df.loc[train_start:train_end].index.values
  test_days = df.loc[test_start:test_end].index.values
  train_test_days = df.loc[train_start:test_end].index.values

  size_all_days = all_days.size
  size_warmup_days = warmup_days.size 
  size_train_days = train_days.size 
  size_test_days = test_days.size 
  size_train_test_days = train_test_days.size
  #auth.authenticate_user()
  #gc = gspread.authorize(GoogleCredentials.get_application_default())

  #link = 'https://docs.google.com/spreadsheets/d/15kwp_4nn-o1r2wW7IuXLsqDSoZYc1OxG46hB4HfeCDY/edit#gid=0'
  #link2= 'https://docs.google.com/spreadsheets/d/15kwp_4nn-o1r2wW7IuXLsqDSoZYc1OxG46hB4HfeCDY/edit#gid=167636255'
  # Open our new sheet and add some data.
  #worksheet = gc.open_by_url(link).sheet2
  worksheet = gc.open_by_url(link).get_worksheet(1)
  #set cell_list for each column and iterate to fill up with values
  all_days = np.datetime_as_string(all_days, unit='D')
  #clear sheet
  clear_range = 'A1' + ':G' + str(2000)
  clear_list = worksheet.range(clear_range)
  for cell in clear_list:
    cell.value = ''
  worksheet.update_cells(clear_list)
  #set up top row (period, timestep, date, ANY_to_HG)
  cell_list = worksheet.range('A1:G1')
  cell_list[0].value = 'PERIOD'
  cell_list[1].value = 'TIMESTEP'
  cell_list[2].value = 'DATE'
  cell_list[3].value = 'IA'
  cell_list[4].value = 'IM'
  cell_list[5].value = 'IX'
  cell_list[6].value = 'HG'
  worksheet.update_cells(cell_list)

  #Set the period column
  end_warm = str(size_warmup_days + 1)
  warmup_range = 'A2:A' + end_warm
  warmup_list = worksheet.range(warmup_range)
  for cell in warmup_list:
    cell.value = 'WARMUP'
  worksheet.update_cells(warmup_list)

  start_train = str(int(end_warm)+1)
  end_train = str(int(start_train) + size_train_days-1)
  train_range = 'A'+ start_train + ':' +'A' +end_train
  train_list = worksheet.range(train_range)
  for cell in train_list:
    cell.value = 'TRAIN'
  worksheet.update_cells(train_list)

  start_test = str(int(end_train)+1)
  end_test = str(int(start_test)+ size_test_days-1)
  test_range = 'A'+ start_test + ':' +'A' +end_test
  test_list = worksheet.range(test_range)
  for cell in test_list:
    cell.value = 'TEST'
  worksheet.update_cells(test_list)

  #Set the timestep column
  t_list = list(range(-size_warmup_days, size_train_test_days))
  end_timestep = str(size_all_days+1)
  timestep_range = 'B2:B' + end_timestep
  timestep_list = worksheet.range(timestep_range)
  for i, cell in enumerate(timestep_list):
    cell.value = t_list[i]
  worksheet.update_cells(timestep_list)

  #Set the date column
  date_range = 'C2:C' + end_timestep
  date_list = worksheet.range(date_range)
  for i, cell in enumerate(date_list):
    cell.value = all_days[i]
  worksheet.update_cells(date_list)

  #IA
  IA_data = (forecasted_fluxes[0][0].stack() + forecasted_fluxes[0][1].stack()).numpy().tolist()
  IA_range = 'D2' + ':D' + end_timestep
  IA_list = worksheet.range(IA_range)
  for i, cell in enumerate(IA_list):
    cell.value = IA_data[i]
  worksheet.update_cells(IA_list)

  #IM
  IM_data = (forecasted_fluxes[1][0].stack() + forecasted_fluxes[1][1].stack()).numpy().tolist()
  IM_range = 'E2' + ':E' + end_timestep
  IM_list = worksheet.range(IM_range)
  for i, cell in enumerate(IM_list):
    cell.value = IM_data[i]
  worksheet.update_cells(IM_list)

  #IX
  IX_data = (forecasted_fluxes[2][0].stack() + forecasted_fluxes[2][1].stack()).numpy().tolist()
  IX_range = 'F2' + ':F' + end_timestep
  IX_list = worksheet.range(IX_range)
  for i, cell in enumerate(IX_list):
    cell.value = IX_data[i]
  worksheet.update_cells(IX_list)

  #HG
  HG_data = (forecasted_fluxes[3][0].stack() + forecasted_fluxes[3][1].stack()).numpy().tolist()
  HG_range = 'G' + start_train + ':G' + end_timestep
  HG_list = worksheet.range(HG_range)
  for i, cell in enumerate(HG_list):
    cell.value = HG_data[i]
  worksheet.update_cells(HG_list)

  print("COVID MODEL SHEET on INFLUXES is UPDATED!")

  make_all_plots(df, model,
                 alpha_bar_M, beta_bar_M,
                 alpha_bar_X, beta_bar_X,
                 alpha_bar_G, beta_bar_G,
                     warmup_start, warmup_end,
                     train_start, train_end,
                     test_start, test_end,
                     train_preds, test_preds,
                     vax_asymp_risk, vax_mild_risk, vax_extreme_risk,
                     forecasted_fluxes)

def RunModel():
  link = input("Enter Your Google Sheet Link: ")
  auth.authenticate_user()
  gc = gspread.authorize(GoogleCredentials.get_application_default())

  #worksheet = gc.open('CovidModelSheet').sheet1
  wb = gc.open_by_url(link)
  worksheet = wb.sheet1
  sheetData = worksheet.get_all_values()
  run_sheetModel(sheetData, link, gc)
