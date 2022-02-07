import numpy as np
import tensorflow as tf

import sys
from enum import Enum

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.layers import Dense

import tensorflow_probability as tfp
from scipy.stats import beta, truncnorm

from model import CovidModel, LogPoissonProb, get_logging_callbacks, Comp, Vax
from data import read_data, create_warmup
#from plots import make_all_plots

import scipy

import matplotlib
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 20}) # set plot font sizes

###

from google.colab import auth
import gspread
from oauth2client.client import GoogleCredentials


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

#Prep data: Rt and Vax_Pct. load default
#load in data from default and put on Google Sheet. reload new data from Google Sheet

def read_sheet_link():
  link = input("Enter Your Google Sheet Link: ")
  return link

def load_default_data(link):
  auth.authenticate_user()
  gc = gspread.authorize(GoogleCredentials.get_application_default())

  #read in the date setting
  wb = gc.open_by_url(link)
  wks = wb.sheet1
  sheetData = wks.get_all_values()

  warmup_start = convert_date(sheetData[2][2])
  warmup_end = convert_date(sheetData[2][3])
  train_start = convert_date(sheetData[3][2])
  train_end = convert_date(sheetData[3][3])
  test_start = convert_date(sheetData[4][2])
  test_end = convert_date(sheetData[4][3])

  state = sheetData[5][1]
  state_abbrev = sheetData[6][1]

  data_dir = './data'
  covid_estim_date = '20211210'
  hhs_date = '20211210'
  owid_date = '20211210'

  log_dir = './logs/test_run_1'

  """## Read data"""

  df = read_data(data_dir=data_dir,
                 covid_estim_date=covid_estim_date,
                 hhs_date=hhs_date,
                 owid_date=owid_date,
                 state=state, state_abbrev=state_abbrev)

  all_days = df.loc[warmup_start:test_end].index.values
  warmup_days = df.loc[warmup_start:warmup_end].index.values
  train_days = df.loc[train_start:train_end].index.values
  test_days = df.loc[test_start:test_end].index.values
  train_test_days = df.loc[train_start:test_end].index.values

  all_days = np.datetime_as_string(all_days, unit='D')

  size_all_days = all_days.size
  size_warmup_days = warmup_days.size 
  size_train_days = train_days.size 
  size_test_days = test_days.size 
  size_train_test_days = train_test_days.size

  rt_total = df.loc[warmup_start:test_end,'Rt'].values
  vax_pct_total = df.loc[warmup_start:warmup_end,'vax_pct'].values

  worksheet = gc.open_by_url(link).get_worksheet(2)

  #set up top row (period, timestep, date, ANY_to_HG)
  worksheet.clear()

  cell_list = worksheet.range('A1:E1')
  cell_list[0].value = 'PERIOD'
  cell_list[1].value = 'TIMESTEP'
  cell_list[2].value = 'DATE'
  cell_list[3].value = 'Rt'
  cell_list[4].value = 'Vax_Pct'
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

  rt_data = rt_total.tolist()
  rt_range = 'D2' + ':D' + end_timestep
  rt_list = worksheet.range(rt_range)
  for i, cell in enumerate(rt_list):
    cell.value = rt_data[i]
  worksheet.update_cells(rt_list)

  vax_pct_data = vax_pct_total.tolist()
  vax_pct_range = 'E2' + ':E' + end_warm
  vax_pct_list = worksheet.range(vax_pct_range)
  for i, cell in enumerate(vax_pct_list):
    cell.value = vax_pct_data[i]
  worksheet.update_cells(vax_pct_list)

  print("Successfully load in the default data. Check the specfics in GoogleSheet")

def run_sheetModel(sheetData, worksheet2, link, gc):
  warmup_start = convert_date(sheetData[2][2])
  warmup_end = convert_date(sheetData[2][3])
  train_start = convert_date(sheetData[3][2])
  train_end = convert_date(sheetData[3][3])
  test_start = convert_date(sheetData[4][2])
  test_end = convert_date(sheetData[4][3])

  state = sheetData[5][1]
  state_abbrev = sheetData[6][1]

  data_dir = './data'
  covid_estim_date = '20211210'
  hhs_date = '20211210'
  owid_date = '20211210'

  log_dir = './logs/test_run_1'

  """### Model Settings"""

  # How long can a person take to progress?
  transition_window = int(sheetData[19][1])

  # CovidEstim Hyper param
  T_serial = float(sheetData[20][1])

  """### Model prior parameters"""

  # Parameters for the Beta distribution prior over rho, the probablility that
  # someone progresses to the next state. Here we use a uniform distribution
  # for all compartments, but we could specify a different prior for each M, X, G


  # Learning rate
  learning_rate = float(sheetData[21][1])

  #worksheet2
  #first_column = wroksheet2.get_col()
  rt_column = (worksheet2.col_values(4))[1:]
  vax_column = (worksheet2.col_values(5))[1:]

  """## Read data"""

  df = read_data(data_dir=data_dir,
                 covid_estim_date=covid_estim_date,
                 hhs_date=hhs_date,
                 owid_date=owid_date,
                 state=state, state_abbrev=state_abbrev)

  for count, value in enumerate(rt_column):
    df.loc[warmup_start:test_end,'Rt'][count] = rt_column[count]

  for count, value in enumerate(vax_column):
    df.loc[warmup_start:warmup_end,'vax_pct'][count] = vax_column[count]

  # get warmup arrays, splitting on vaccination status
  warmup_asymp, warmup_mild, warmup_extreme = create_warmup(df, 
                                                            warmup_start, 
                                                            warmup_end,
                                                            0,0,0)
  vax_statuses = [Vax.yes, Vax.no]

  warmup_A_params = {}
  warmup_M_params = {}

  for vax_status in [status.value for status in vax_statuses]:
                  
      
      warmup_A_params[vax_status] = {}
      warmup_A_params[vax_status]['prior'] = []
      warmup_A_params[vax_status]['posterior_init'] = []

      warmup_M_params[vax_status] = {}
      warmup_M_params[vax_status]['prior'] = []
      warmup_M_params[vax_status]['posterior_init'] = []

      for day in range(transition_window):
          warmup_A_params[vax_status]['prior'].append({'loc': warmup_asymp[vax_status][day]/2,
                                                      'scale': warmup_asymp[vax_status][day]/2/10})

          warmup_M_params[vax_status]['prior'].append({'loc': warmup_mild[vax_status][day]/2/100,
                                                      'scale': warmup_mild[vax_status][day]/2/10})

  x_train = tf.cast(df.loc[train_start:train_end,'Rt'].values, dtype=tf.float32)
  x_test = tf.cast(df.loc[train_start:test_end,'Rt'].values, dtype=tf.float32)

  y_train = tf.cast(df.loc[train_start:train_end,'general_ward'], dtype=tf.float32)
  y_test = tf.cast(df.loc[train_start:test_end,'general_ward'], dtype=tf.float32)


  T_serial = {}
  T_serial['prior'] ={'loc':5.8, 'scale':1}


  epsilon = {}
  epsilon['prior'] ={'a':1, 'b':1}

  delta = {}
  delta['prior'] ={'a':1, 'b':1}

  rho_M = {}
  lambda_M = {}
  nu_M = {}
  rho_G = {}
  lambda_G = {}
  nu_G = {}

      
  rho_M[0] = {}
  rho_M[0]['prior'] = {'a': float(sheetData[9][1]), 'b': float(sheetData[9][2])}
  rho_M[1] = {}
  rho_M[1]['prior'] = {'a': float(sheetData[10][1]), 'b': float(sheetData[10][2])}


  lambda_M[0] = {}
  lambda_M[0]['prior'] = {'loc': float(sheetData[14][1]), 'scale': float(sheetData[14][2])}
  lambda_M[1] = {}
  lambda_M[1]['prior'] = {'loc': float(sheetData[15][1]), 'scale': float(sheetData[15][2])}

  nu_M[0] = {}
  nu_M[0]['prior'] = {'loc': float(sheetData[14][3]), 'scale': float(sheetData[14][4])}
  nu_M[1] = {}
  nu_M[1]['prior'] = {'loc': float(sheetData[15][3]), 'scale': float(sheetData[15][4])}


  rho_G[0] = {}
  rho_G[0]['prior'] = {'a': float(sheetData[11][1]), 'b': float(sheetData[11][2])}
  rho_G[1] = {}
  rho_G[1]['prior'] = {'a': float(sheetData[12][1]), 'b': float(sheetData[12][2])}

  lambda_G[0] = {}
  lambda_G[0]['prior'] = {'loc': float(sheetData[16][1]), 'scale': float(sheetData[16][2])}
  lambda_G[1] = {}
  lambda_G[1]['prior'] = {'loc': float(sheetData[17][1]), 'scale': float(sheetData[17][2])}

  nu_G[0] = {}
  nu_G[0]['prior'] = {'loc': float(sheetData[16][3]), 'scale': float(sheetData[16][4])}
  nu_G[1] = {}
  nu_G[1]['prior'] = {'loc': float(sheetData[17][3]), 'scale': float(sheetData[17][4])}


  T_serial_scale = 1.0
  delta_scale = 0.2
  epsilon_scale = 0.3
  rho_M_scale = 0.1
  lambda_M_scale = 1.0
  nu_M_scale = 1.2

  rho_G_scale = 0.1
  lambda_G_scale = 1.0
  nu_G_scale = 0.2


  T_serial['posterior_init'] = {'loc': tfp.math.softplus_inverse(4.0),
                                       'scale':tf.cast(tfp.math.softplus_inverse(T_serial_scale),dtype=tf.float32)}
  delta['posterior_init'] = {'loc':  tf.cast(np.log(0.1/(1-0.1)),dtype=tf.float32),
                                       'scale':tf.cast(tfp.math.softplus_inverse(delta_scale),dtype=tf.float32)}
  epsilon['posterior_init'] = {'loc':  tf.cast(np.log(0.5/(1-0.5)),dtype=tf.float32),
                                       'scale':tf.cast(tfp.math.softplus_inverse(epsilon_scale),dtype=tf.float32)}


  for vax_status in [status.value for status in vax_statuses]:
      
      rho_M[vax_status]['posterior_init'] = {'loc': tf.cast(np.log(0.5/(1-0.5)),dtype=tf.float32),
                                            'scale':tf.cast(tfp.math.softplus_inverse(rho_M_scale),dtype=tf.float32)}

      lambda_M[vax_status]['posterior_init'] = {'loc': tf.cast(tfp.math.softplus_inverse(3.0),dtype=tf.float32),
                                               'scale':tf.cast(tfp.math.softplus_inverse(lambda_M_scale),dtype=tf.float32)}

      nu_M[vax_status]['posterior_init'] = {'loc': tf.cast(tfp.math.softplus_inverse(5.0),dtype=tf.float32),
                                           'scale':tf.cast(tfp.math.softplus_inverse(nu_M_scale),dtype=tf.float32)}

      rho_G[vax_status]['posterior_init'] = {'loc': tf.cast(np.log(0.1/(1-0.1)),dtype=tf.float32),
                                            'scale':tf.cast(tfp.math.softplus_inverse(rho_G_scale),dtype=tf.float32)}

      lambda_G[vax_status]['posterior_init'] = {'loc': tf.cast(tfp.math.softplus_inverse(3.3),dtype=tf.float32),
                                               'scale':tf.cast(tfp.math.softplus_inverse(lambda_G_scale),dtype=tf.float32)}

      nu_G[vax_status]['posterior_init'] = {'loc': tf.cast(tfp.math.softplus_inverse(9.0),dtype=tf.float32),
                                           'scale':tf.cast(tfp.math.softplus_inverse(nu_G_scale),dtype=tf.float32)}

      for day in range(transition_window):
          # must be positive so reverse softplus the mean
          warmup_A_params[vax_status]['posterior_init'].append({'loc': tf.cast(tfp.math.softplus_inverse(2000.0/2),dtype=tf.float32),
                                                               'scale': tf.cast(tfp.math.softplus_inverse(500.0/2),dtype=tf.float32)})#tf.cast(tfp.math.softplus_inverse(warmup_asymp[day]/10),dtype=tf.float32)})

          warmup_M_params[vax_status]['posterior_init'].append({'loc': tf.cast(tfp.math.softplus_inverse(1000.0/2),dtype=tf.float32),
                                                               'scale': tf.cast(tfp.math.softplus_inverse(100.0/2),dtype=tf.float32)})#tf.cast(tfp.math.softplus_inverse(warmup_asymp[day]/10),dtype=tf.float32)})

  model = CovidModel([Vax.no, Vax.yes], [Comp.A, Comp.M, Comp.G],
                   transition_window,
                  T_serial, epsilon, delta, rho_M, lambda_M, nu_M, rho_G, lambda_G, nu_G,
                   warmup_A_params, warmup_M_params, posterior_samples=1000, debug_disable_theta=False)

  pre_training_preds=tf.reduce_mean(model.call(x_train), axis=-1)

  loss = LogPoissonProb() 
  optimizer = tf.keras.optimizers.Adam(
      learning_rate=learning_rate #beta_1=0.1, beta_2=0.1
  )

  logging_callbacks = get_logging_callbacks('/content/logs/scale_nicely')

  model.compile(loss=loss, optimizer=optimizer, run_eagerly=True)
  model.fit(x=np.asarray([x_train]), y=np.asarray([y_train]),
           epochs=20, batch_size=0,
          callbacks=logging_callbacks)


  return model

def train_and_project(link):
  auth.authenticate_user()
  gc = gspread.authorize(GoogleCredentials.get_application_default())

  #worksheet = gc.open('CovidModelSheet').sheet1
  wb = gc.open_by_url(link)
  worksheet = wb.sheet1
  sheetData = worksheet.get_all_values()

  worksheet2 = gc.open_by_url(link).get_worksheet(2)

  return run_sheetModel(sheetData, worksheet2, link, gc)

