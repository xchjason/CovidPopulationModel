import numpy as np
import tensorflow as tf

import datetime
import os
import sys

from enum import Enum

import tensorflow as tf
import tensorflow_probability as tfp

# Local imports from model.py, data.py
from model import CovidModel, LogPoissonProb, get_logging_callbacks, Comp, Vax
from data import read_data, create_warmup
from convert import *
from model_config import ModelConfig

import scipy
from scipy.special import logit

import matplotlib
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 20}) # set plot font sizes


###

from google.colab import auth
import gspread
from oauth2client.client import GoogleCredentials
from google.auth import default


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
  #gc = gspread.authorize(GoogleCredentials.get_application_default())
  creds, _ = default()
  gc = gspread.authorize(creds)

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
	transition_window = int(sheetData[31][1])
	learning_rate = float(sheetData[32][1])
	num_epoch = int(sheetData[33][1])

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

	warmup_asymp, warmup_mild, count_gen, count_icu = create_warmup(df, 
	                                                      warmup_start, 
	                                                      warmup_end,
	                                                      0,0,0,0)
	print(f'Approximately {warmup_asymp[0][0]} asymptomatic people, total')
	print(f'Approximately {warmup_mild[0][0]} mild people, total')

	vax_statuses = [Vax.yes, Vax.no]

  # Set warmup priors/initializations

	warmup_A_params = {}
	warmup_M_params = {}
	warmup_G_params = {}
	warmup_GR_params = {}
	init_count_G = {}
	warmup_I_params = {}
	warmup_IR_params = {}
	init_count_I = {}

	for vax_status in [status.value for status in vax_statuses]:
	                
	    
	    warmup_A_params[vax_status] = {}
	    warmup_A_params[vax_status]['prior'] = []
	    warmup_A_params[vax_status]['posterior_init'] = []

	    warmup_M_params[vax_status] = {}
	    warmup_M_params[vax_status]['prior'] = []
	    warmup_M_params[vax_status]['posterior_init'] = []

	    warmup_G_params[vax_status] = {}
	    warmup_G_params[vax_status]['prior'] = []
	    warmup_G_params[vax_status]['posterior_init'] = []
	    warmup_GR_params[vax_status] = {}
	    warmup_GR_params[vax_status]['prior'] = []
	    warmup_GR_params[vax_status]['posterior_init'] = []
	    
	    warmup_I_params[vax_status] = {}
	    warmup_I_params[vax_status]['prior'] = []
	    warmup_I_params[vax_status]['posterior_init'] = []
	    warmup_IR_params[vax_status] = {}
	    warmup_IR_params[vax_status]['prior'] = []
	    warmup_IR_params[vax_status]['posterior_init'] = []
	    
	    init_count_G[vax_status] = {}
	    init_count_G[vax_status]['prior'] ={}
	    init_count_G[vax_status]['posterior_init'] ={}
	    
	    init_count_I[vax_status] = {}
	    init_count_I[vax_status]['prior'] ={}
	    init_count_I[vax_status]['posterior_init'] ={}

	#print(df['general_ward_count'])

	#x_train = tf.cast(df.loc[train_start:train_end,'Rt'].values, dtype=tf.float32)
	#x_test = tf.cast(df.loc[train_start:test_end,'Rt'].values, dtype=tf.float32)

	#y_train = tf.cast(df.loc[train_start:train_end,'general_ward'], dtype=tf.float32)
	#y_test = tf.cast(df.loc[train_start:test_end,'general_ward'], dtype=tf.float32)

	# Set priors

	T_serial = {}
	T_serial['prior'] ={'loc':5.8, 'scale':1}

	# Go flat so we have some flexibility
	epsilon = {}
	epsilon['prior'] ={'a':1, 'b':1}

	delta = {}
	delta['prior'] ={'a':1, 'b':1}


	for vax_status in [status.value for status in vax_statuses]:

	    # Use HHS number number of total Gen/ICU people on day 0 with large variance
	    init_count_G[vax_status]['prior'] = {'loc':count_gen[vax_status], 'scale':count_gen[vax_status]/4}
	    init_count_I[vax_status]['prior'] = {'loc':count_icu[vax_status], 'scale':count_icu[vax_status]/4}
	   
	    # warmup_asymp doesn't have vaccine-status specific numbers
	    # so here we divide total in half for our estimate
	    # with a large variance
	    warmup_A_params[vax_status]['prior'] = {'intercept': warmup_asymp[vax_status][0]/2,
	                                            'slope': 0,
	                                                'scale': warmup_asymp[vax_status][0]/2/4}

	    warmup_M_params[vax_status]['prior'] = {'intercept': warmup_mild[vax_status][0]/2,
	                                            'slope': 0,
	                                                'scale': warmup_mild[vax_status][0]/2/4}


	    # Assume new entries to hospital = 10% of total population (because you spend 10 days there max)
	    warmup_G_params[vax_status]['prior'] = {'intercept': count_gen[vax_status]/10,
	                                            'slope': 0,
	                                                'scale': count_gen[vax_status]/4}
	    warmup_I_params[vax_status]['prior'] = {'intercept': count_icu[vax_status]/10,
	                                            'slope': 0,
	                                                'scale': count_icu[vax_status]/10}

	    # assume half of the total recover, and 10% recover each day
	    warmup_GR_params[vax_status]['prior'] = {'intercept': count_gen[vax_status]/2/10,
	                                            'slope': 0,
	                                                'scale': count_gen[vax_status]/2/10/2}
	    warmup_IR_params[vax_status]['prior'] = {'intercept': count_icu[vax_status]/2/10,
	                                            'slope': 0,
	                                                'scale': count_icu[vax_status]/2/10/2}


	rho_M = {}
	lambda_M = {}
	nu_M = {}
	rho_G = {}
	lambda_G = {}
	nu_G = {}
	###new addition
	rho_I = {}
	lambda_I = {}
	nu_I = {}
	lambda_I_bar = {}
	nu_I_bar = {}

	rho_D = {}
	lambda_D = {}
	nu_D = {}
	lambda_D_bar = {}
	nu_D_bar = {}

	  
	rho_M[0] = {}
	rho_M[0]['prior'] = {'a': float(sheetData[9][1]), 'b': float(sheetData[9][2])}
	rho_M[1] = {}
	rho_M[1]['prior'] = {'a': float(sheetData[10][1]), 'b': float(sheetData[10][2])}

	rho_G[0] = {}
	rho_G[0]['prior'] = {'a': float(sheetData[11][1]), 'b': float(sheetData[11][2])}
	rho_G[1] = {}
	rho_G[1]['prior'] = {'a': float(sheetData[12][1]), 'b': float(sheetData[12][2])}

	rho_I[0] = {}
	rho_I[0]['prior'] = {'a': float(sheetData[13][1]), 'b': float(sheetData[13][2])}
	rho_I[1] = {}
	rho_I[1]['prior'] = {'a': float(sheetData[14][1]), 'b': float(sheetData[14][2])}

	rho_D[0] = {}
	rho_D[0]['prior'] = {'a': float(sheetData[15][1]), 'b': float(sheetData[15][2])}
	rho_D[1] = {}
	rho_D[1]['prior'] = {'a': float(sheetData[16][1]), 'b': float(sheetData[16][2])}

	lambda_M[0] = {}
	lambda_M[0]['prior'] = {'loc': float(sheetData[18][1]), 'scale': float(sheetData[18][2])}
	lambda_M[1] = {}
	lambda_M[1]['prior'] = {'loc': float(sheetData[19][1]), 'scale': float(sheetData[19][2])}

	lambda_G[0] = {}
	lambda_G[0]['prior'] = {'loc': float(sheetData[20][1]), 'scale': float(sheetData[20][2])}
	lambda_G[1] = {}
	lambda_G[1]['prior'] = {'loc': float(sheetData[21][1]), 'scale': float(sheetData[21][2])}

	lambda_I[0] = {}
	lambda_I[0]['prior'] = {'loc': float(sheetData[22][1]), 'scale': float(sheetData[22][2])}
	lambda_I[1] = {}
	lambda_I[1]['prior'] = {'loc': float(sheetData[23][1]), 'scale': float(sheetData[23][2])}

	lambda_I_bar[0] = {}
	lambda_I_bar[0]['prior'] = {'loc': float(sheetData[24][1]), 'scale': float(sheetData[24][2])}
	lambda_I_bar[1] = {}
	lambda_I_bar[1]['prior'] = {'loc': float(sheetData[25][1]), 'scale': float(sheetData[25][2])}

	lambda_D[0] = {}
	lambda_D[0]['prior'] = {'loc': float(sheetData[26][1]), 'scale': float(sheetData[26][2])}
	lambda_D[1] = {}
	lambda_D[1]['prior'] = {'loc': float(sheetData[27][1]), 'scale': float(sheetData[27][2])}

	lambda_D_bar[0] = {}
	lambda_D_bar[0]['prior'] = {'loc': float(sheetData[28][1]), 'scale': float(sheetData[28][2])}
	lambda_D_bar[1] = {}
	lambda_D_bar[1]['prior'] = {'loc': float(sheetData[29][1]), 'scale': float(sheetData[29][2])}


	nu_M[0] = {}
	nu_M[0]['prior'] = {'loc': float(sheetData[18][3]), 'scale': float(sheetData[18][4])}
	nu_M[1] = {}
	nu_M[1]['prior'] = {'loc': float(sheetData[19][3]), 'scale': float(sheetData[19][4])}


	nu_G[0] = {}
	nu_G[0]['prior'] = {'loc': float(sheetData[20][3]), 'scale': float(sheetData[20][4])}
	nu_G[1] = {}
	nu_G[1]['prior'] = {'loc': float(sheetData[21][3]), 'scale': float(sheetData[21][4])}

	nu_I[0] = {}
	nu_I[0]['prior'] = {'loc': float(sheetData[22][3]), 'scale': float(sheetData[22][4])}
	nu_I[1] = {}
	nu_I[1]['prior'] = {'loc': float(sheetData[23][3]), 'scale': float(sheetData[23][4])}

	nu_I_bar[0] = {}
	nu_I_bar[0]['prior'] = {'loc': float(sheetData[24][3]), 'scale': float(sheetData[24][4])}
	nu_I_bar[1] = {}
	nu_I_bar[1]['prior'] = {'loc': float(sheetData[25][3]), 'scale': float(sheetData[25][4])}

	nu_D[0] = {}
	nu_D[0]['prior'] = {'loc': float(sheetData[26][3]), 'scale': float(sheetData[26][4])}
	nu_D[1] = {}
	nu_D[1]['prior'] = {'loc': float(sheetData[27][3]), 'scale': float(sheetData[27][4])}

	nu_D_bar[0] = {}
	nu_D_bar[0]['prior'] = {'loc': float(sheetData[28][3]), 'scale': float(sheetData[28][4])}
	nu_D_bar[1] = {}
	nu_D_bar[1]['prior'] = {'loc': float(sheetData[28][3]), 'scale': float(sheetData[28][4])}


	# Set posteriors
	T_serial_scale = 1.0
	delta_scale = 0.2
	epsilon_scale = 0.3


	rho_M_scale = 0.1
	lambda_M_scale = 1.0
	nu_M_scale = 1.2

	rho_G_scale = 0.1
	lambda_G_scale = 1.0
	nu_G_scale = 0.2

	rho_I_scale = 0.1
	lambda_I_scale = 1.0
	nu_I_scale = 0.2
	lambda_I_bar_scale = 1.0
	nu_I_bar_scale = 0.2

	rho_D_scale = 0.1
	lambda_D_scale = 1.0
	nu_D_scale = 0.2
	lambda_D_bar_scale = 1.0
	nu_D_bar_scale = 0.2

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

		rho_I[vax_status]['posterior_init'] = {'loc': tf.cast(np.log(0.1/(1-0.1)),dtype=tf.float32),
		                                      'scale':tf.cast(tfp.math.softplus_inverse(rho_I_scale),dtype=tf.float32)}
		lambda_I[vax_status]['posterior_init'] = {'loc': tf.cast(tfp.math.softplus_inverse(3.3),dtype=tf.float32),
		                                         'scale':tf.cast(tfp.math.softplus_inverse(lambda_I_scale),dtype=tf.float32)}
		nu_I[vax_status]['posterior_init'] = {'loc': tf.cast(tfp.math.softplus_inverse(9.0),dtype=tf.float32),
		                                     'scale':tf.cast(tfp.math.softplus_inverse(nu_I_scale),dtype=tf.float32)}
		lambda_I_bar[vax_status]['posterior_init'] = {'loc': tf.cast(tfp.math.softplus_inverse(3.3),dtype=tf.float32),
		                                         'scale':tf.cast(tfp.math.softplus_inverse(lambda_I_bar_scale),dtype=tf.float32)}
		nu_I_bar[vax_status]['posterior_init'] = {'loc': tf.cast(tfp.math.softplus_inverse(9.0),dtype=tf.float32),
		                                     'scale':tf.cast(tfp.math.softplus_inverse(nu_I_bar_scale),dtype=tf.float32)}

		rho_D[vax_status]['posterior_init'] = {'loc': tf.cast(np.log(0.1/(1-0.1)),dtype=tf.float32),
		                                      'scale':tf.cast(tfp.math.softplus_inverse(rho_D_scale),dtype=tf.float32)}
		lambda_D[vax_status]['posterior_init'] = {'loc': tf.cast(tfp.math.softplus_inverse(3.3),dtype=tf.float32),
		                                         'scale':tf.cast(tfp.math.softplus_inverse(lambda_D_scale),dtype=tf.float32)}
		nu_D[vax_status]['posterior_init'] = {'loc': tf.cast(tfp.math.softplus_inverse(9.0),dtype=tf.float32),
		                                     'scale':tf.cast(tfp.math.softplus_inverse(nu_D_scale),dtype=tf.float32)}
		lambda_D_bar[vax_status]['posterior_init'] = {'loc': tf.cast(tfp.math.softplus_inverse(3.3),dtype=tf.float32),
		                                         'scale':tf.cast(tfp.math.softplus_inverse(lambda_D_bar_scale),dtype=tf.float32)}
		nu_D_bar[vax_status]['posterior_init'] = {'loc': tf.cast(tfp.math.softplus_inverse(9.0),dtype=tf.float32),
		                                     'scale':tf.cast(tfp.math.softplus_inverse(nu_D_bar_scale),dtype=tf.float32)}

		init_count_G[vax_status]['posterior_init'] = {'loc':tf.cast(tfp.math.softplus_inverse(count_gen[vax_status]/100),dtype=tf.float32),
		                                              'scale': tf.cast(tfp.math.softplus_inverse(count_gen[vax_status]/100/10),dtype=tf.float32)}
		init_count_I[vax_status]['posterior_init'] = {'loc':tf.cast(tfp.math.softplus_inverse(count_icu[vax_status]/100),dtype=tf.float32),
		                                              'scale': tf.cast(tfp.math.softplus_inverse(count_icu[vax_status]/100/10),dtype=tf.float32)}



		# must be positive so reverse softplus the mean
		warmup_A_params[vax_status]['posterior_init'] = {'intercept': tf.cast(tfp.math.softplus_inverse(2000.0/100/2),dtype=tf.float32),
		                                                      'slope': tf.cast(0.0, dtype=tf.float32),
		                                                     'scale': tf.cast(tfp.math.softplus_inverse(500.0/100/2),dtype=tf.float32)}
		warmup_M_params[vax_status]['posterior_init'] = {'intercept': tf.cast(tfp.math.softplus_inverse(1000.0/100/2),dtype=tf.float32),
		                                                      'slope': tf.cast(0.0, dtype=tf.float32),
		                                                     'scale': tf.cast(tfp.math.softplus_inverse(100.0/100/2),dtype=tf.float32)}

		warmup_G_params[vax_status]['posterior_init'] = {'intercept': tf.cast(tfp.math.softplus_inverse(500.0/100/2),dtype=tf.float32),
		                                                      'slope': tf.cast(0.0, dtype=tf.float32),
		                                                     'scale': tf.cast(tfp.math.softplus_inverse(50.0/100/2),dtype=tf.float32)}
		warmup_GR_params[vax_status]['posterior_init']= {'intercept': tf.cast(tfp.math.softplus_inverse(400.0/100/2),dtype=tf.float32),
		                                                      'slope': tf.cast(0.0, dtype=tf.float32),
		                                                     'scale': tf.cast(tfp.math.softplus_inverse(50.0/100/2),dtype=tf.float32)}
		warmup_I_params[vax_status]['posterior_init'] = {'intercept': tf.cast(tfp.math.softplus_inverse(100.0/100/2),dtype=tf.float32),
		                                                      'slope': tf.cast(0.0, dtype=tf.float32),
		                                                     'scale': tf.cast(tfp.math.softplus_inverse(30.0/100/2),dtype=tf.float32)}
		warmup_IR_params[vax_status]['posterior_init']= {'intercept': tf.cast(tfp.math.softplus_inverse(90.0/100/2),dtype=tf.float32),
		                                                      'slope': tf.cast(0.0, dtype=tf.float32),
		                                                     'scale': tf.cast(tfp.math.softplus_inverse(30.0/100/2),dtype=tf.float32)}
    # Make data

	x_train = tf.cast(df.loc[train_start:train_end,'Rt'].values, dtype=tf.float32)
	x_test = tf.cast(df.loc[train_start:test_end,'Rt'].values, dtype=tf.float32)

	y_train = {}
	y_train['G_in'] = tf.cast(df.loc[train_start:train_end,'general_ward_in'], dtype=tf.float32)
	y_train['G_count'] = tf.cast(df.loc[train_start:train_end,'general_ward_count'], dtype=tf.float32)
	y_train['I_count'] = tf.cast(df.loc[train_start:train_end,'icu_count'], dtype=tf.float32)
	y_train['D_in'] = tf.cast(df.loc[train_start:train_end,'deaths_covid'], dtype=tf.float32) 

	y_test = {}
	y_test['G_in'] = tf.cast(df.loc[train_start:test_end,'general_ward_in'], dtype=tf.float32)
	y_test['G_count'] = tf.cast(df.loc[train_start:test_end,'general_ward_count'], dtype=tf.float32)
	y_test['I_count'] = tf.cast(df.loc[train_start:test_end,'icu_count'], dtype=tf.float32)
	y_test['D_in'] = tf.cast(df.loc[train_start:test_end,'deaths_covid'], dtype=tf.float32)

	model = CovidModel([Vax.no, Vax.yes], [Comp.A, Comp.M, Comp.G, Comp.GR, Comp.I, Comp.IR, Comp.D],
	                 transition_window,
	                T_serial, epsilon, delta,
	                 rho_M, lambda_M, nu_M,
	                 rho_G, lambda_G, nu_G,
	                 rho_I, lambda_I, nu_I,
	                 lambda_I_bar, nu_I_bar,
	                 rho_D, lambda_D, nu_D,
	                 lambda_D_bar, nu_D_bar,
	                 warmup_A_params,
	                 warmup_M_params,
	                 warmup_G_params, warmup_GR_params, init_count_G,
	                 warmup_I_params, warmup_IR_params, init_count_I, posterior_samples=1000, debug_disable_theta=False)

	pre_training_preds=model.call(x_train)

	loss = LogPoissonProb() 
	optimizer = tf.keras.optimizers.Adam(
	    learning_rate=learning_rate,#beta_1=0.1, beta_2=0.1
	)
	logdir = os.path.join("logs", datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
	logging_callbacks = get_logging_callbacks(logdir)

	model.compile(loss=loss, optimizer=optimizer, run_eagerly=True)
	model.fit(x=np.asarray([x_train]), y=np.asarray([(y_train['G_count'], y_train['G_in'], y_train['I_count'], y_train['D_in'])]),
	         epochs=num_epoch, batch_size=0,
	        callbacks=logging_callbacks) 

	preds = tf.reduce_mean(model.call(x_test), axis=-1)


	#set up
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

  	# update param sheet
	param_worksheet = gc.open_by_url(link).get_worksheet(3)

	param_worksheet.update_cell(2, 2, str(tf.math.sigmoid(model.unconstrained_rho_M[1]['loc']).numpy()))
	param_worksheet.update_cell(3, 2, str(tf.math.sigmoid(model.unconstrained_rho_G[1]['loc']).numpy()))
	param_worksheet.update_cell(4, 2, str(tf.math.sigmoid(model.unconstrained_rho_I[1]['loc']).numpy()))
	param_worksheet.update_cell(5, 2, str(tf.math.sigmoid(model.unconstrained_rho_D[1]['loc']).numpy()))

	param_worksheet.update_cell(2, 4, str(tf.math.sigmoid(model.unconstrained_rho_M[0]['loc']).numpy()))
	param_worksheet.update_cell(3, 4, str(tf.math.sigmoid(model.unconstrained_rho_G[0]['loc']).numpy()))
	param_worksheet.update_cell(4, 4, str(tf.math.sigmoid(model.unconstrained_rho_I[0]['loc']).numpy()))
	param_worksheet.update_cell(5, 4, str(tf.math.sigmoid(model.unconstrained_rho_D[0]['loc']).numpy()))

	param_worksheet.update_cell(8, 2, str(tf.math.softplus(model.unconstrained_lambda_M[1]['loc']).numpy()))
	param_worksheet.update_cell(9, 2, str(tf.math.softplus(model.unconstrained_lambda_G[1]['loc']).numpy()))
	param_worksheet.update_cell(10, 2, str(tf.math.softplus(model.unconstrained_lambda_I[1]['loc']).numpy()))
	param_worksheet.update_cell(11, 2, str(tf.math.softplus(model.unconstrained_lambda_I_bar[1]['loc']).numpy()))
	param_worksheet.update_cell(12, 2, str(tf.math.softplus(model.unconstrained_lambda_D[1]['loc']).numpy()))
	param_worksheet.update_cell(13, 2, str(tf.math.softplus(model.unconstrained_lambda_D_bar[1]['loc']).numpy()))

	param_worksheet.update_cell(8, 3, str(tf.math.softplus(model.unconstrained_nu_M[1]['loc']).numpy()))
	param_worksheet.update_cell(9, 3, str(tf.math.softplus(model.unconstrained_nu_G[1]['loc']).numpy()))
	param_worksheet.update_cell(10, 3, str(tf.math.softplus(model.unconstrained_nu_I[1]['loc']).numpy()))
	param_worksheet.update_cell(11, 3, str(tf.math.softplus(model.unconstrained_nu_I_bar[1]['loc']).numpy()))
	param_worksheet.update_cell(12, 3, str(tf.math.softplus(model.unconstrained_nu_D[1]['loc']).numpy()))
	param_worksheet.update_cell(13, 3, str(tf.math.softplus(model.unconstrained_nu_D_bar[1]['loc']).numpy()))

	param_worksheet.update_cell(8, 5, str(tf.math.sigmoid(model.unconstrained_lambda_M[0]['loc']).numpy()))
	param_worksheet.update_cell(9, 5, str(tf.math.sigmoid(model.unconstrained_lambda_G[0]['loc']).numpy()))
	param_worksheet.update_cell(10, 5, str(tf.math.sigmoid(model.unconstrained_lambda_I[0]['loc']).numpy()))
	param_worksheet.update_cell(11, 5, str(tf.math.sigmoid(model.unconstrained_lambda_I_bar[0]['loc']).numpy()))
	param_worksheet.update_cell(12, 5, str(tf.math.sigmoid(model.unconstrained_lambda_D[0]['loc']).numpy()))
	param_worksheet.update_cell(13, 5, str(tf.math.sigmoid(model.unconstrained_lambda_D_bar[0]['loc']).numpy()))

	param_worksheet.update_cell(8, 6, str(tf.math.softplus(model.unconstrained_nu_M[0]['loc']).numpy()))
	param_worksheet.update_cell(9, 6, str(tf.math.softplus(model.unconstrained_nu_G[0]['loc']).numpy()))
	param_worksheet.update_cell(10, 6, str(tf.math.softplus(model.unconstrained_nu_I[0]['loc']).numpy()))
	param_worksheet.update_cell(11, 6, str(tf.math.softplus(model.unconstrained_nu_I_bar[0]['loc']).numpy()))
	param_worksheet.update_cell(12, 6, str(tf.math.softplus(model.unconstrained_nu_D[0]['loc']).numpy()))
	param_worksheet.update_cell(13, 6, str(tf.math.softplus(model.unconstrained_nu_D_bar[0]['loc']).numpy()))


	worksheet = gc.open_by_url(link).get_worksheet(1)
	#set cell_list for each column and iterate to fill up with values
	all_days = np.datetime_as_string(all_days, unit='D')
	#clear sheet
	clear_range = 'A1' + ':G' + str(3000)
	clear_list = worksheet.range(clear_range)
	for cell in clear_list:
		cell.value = ''
	worksheet.update_cells(clear_list)
	#set up top row (period, timestep, date, ANY_to_HG)
	cell_list = worksheet.range('A1:G1')
	cell_list[0].value = 'PERIOD'
	cell_list[1].value = 'TIMESTEP'
	cell_list[2].value = 'DATE'
	cell_list[3].value = 'general_ward_in'
	cell_list[4].value = 'general_ward_count'
	cell_list[5].value = 'ICU_count'
	cell_list[6].value = 'deaths_covid'
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

	#G_in
	G_in_data = preds[0][1].numpy().tolist()
	#G_in_range = 'D2' + ':D' + end_timestep
	G_in_range = 'D' + start_train + ':D' + end_timestep
	G_in_list = worksheet.range(G_in_range)
	for i, cell in enumerate(G_in_list):
		cell.value = G_in_data[i]
	worksheet.update_cells(G_in_list)

	#G_count
	G_count_data = preds[0][0].numpy().tolist()
	#G_count_range = 'E2' + ':E' + end_timestep
	G_count_range = 'E' + start_train + ':E' + end_timestep
	G_count_list = worksheet.range(G_count_range)
	for i, cell in enumerate(G_count_list):
		cell.value = G_count_data[i]
	worksheet.update_cells(G_count_list)

	#I_count
	I_count_data = preds[0][2].numpy().tolist()
	#I_count_range = 'F2' + ':F' + end_timestep
	I_count_range = 'F' + start_train + ':F' + end_timestep
	I_count_list = worksheet.range(I_count_range)
	for i, cell in enumerate(I_count_list):
		cell.value = I_count_data[i]
	worksheet.update_cells(I_count_list)

	#Death
	D_data = preds[0][3].numpy().tolist()
	D_range = 'G' + start_train + ':G' + end_timestep
	D_list = worksheet.range(D_range)
	for i, cell in enumerate(D_list):
		cell.value = D_data[i]
	worksheet.update_cells(D_list)



	plt.figure(figsize=(8, 6))
	plt.plot(df.loc[train_start:test_end].index.values, y_test['I_count'], label='ICU')
	plt.plot(df.loc[train_start:test_end].index.values, preds[0][2], label='ICU')
	month_ticks = matplotlib.dates.MonthLocator(interval=1)
	ax = plt.gca()
	ax.xaxis.set_major_locator(month_ticks)
	plt.legend()
	plt.title('ICU Count')

	plt.figure(figsize=(8, 6))
	plt.plot(df.loc[train_start:test_end].index.values, y_test['G_count'], )
	plt.plot(df.loc[train_start:test_end].index.values, preds[0][0])
	month_ticks = matplotlib.dates.MonthLocator(interval=1)
	ax = plt.gca()
	ax.xaxis.set_major_locator(month_ticks)
	plt.legend()
	plt.title('Gen Count')

	plt.figure(figsize=(8, 6))
	plt.plot(df.loc[train_start:test_end].index.values, y_test['G_in'], )
	plt.plot(df.loc[train_start:test_end].index.values, preds[0][1])
	month_ticks = matplotlib.dates.MonthLocator(interval=1)
	ax = plt.gca()
	ax.xaxis.set_major_locator(month_ticks)
	plt.legend()
	plt.title('Gen Influx')

	plt.figure(figsize=(8, 6))
	plt.plot(df.loc[train_start:test_end].index.values, y_test['D_in'], )
	plt.plot(df.loc[train_start:test_end].index.values, preds[0][3])
	month_ticks = matplotlib.dates.MonthLocator(interval=1)
	ax = plt.gca()
	ax.xaxis.set_major_locator(month_ticks)
	plt.legend()
	plt.title('Death Influx')

	return model

def train_and_project(link):
  auth.authenticate_user()
  #gc = gspread.authorize(GoogleCredentials.get_application_default())
  creds, _ = default()
  gc = gspread.authorize(creds)
  #worksheet = gc.open('CovidModelSheet').sheet1
  wb = gc.open_by_url(link)
  worksheet = wb.sheet1
  sheetData = worksheet.get_all_values()

  worksheet2 = gc.open_by_url(link).get_worksheet(2)

  return run_sheetModel(sheetData, worksheet2, link, gc)

def run_sheetModel_noTrain(sheetData, worksheet2, link, gc, model_config_path=None):
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
	transition_window = int(sheetData[8][1])
	learning_rate = float(sheetData[9][1])

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

	warmup_asymp, warmup_mild, count_gen, count_icu = create_warmup(df, 
	                                                      warmup_start, 
	                                                      warmup_end,
	                                                      0,0,0,0)

	vax_statuses = [Vax.yes, Vax.no]
	x_train = tf.cast(df.loc[train_start:train_end, 'Rt'].values, dtype=tf.float32)
	x_test = tf.cast(df.loc[train_start:test_end, 'Rt'].values, dtype=tf.float32)

	y_train = {}
	y_train['G_in'] = tf.cast(df.loc[train_start:train_end, 'general_ward_in'], dtype=tf.float32)
	y_train['G_count'] = tf.cast(df.loc[train_start:train_end, 'general_ward_count'], dtype=tf.float32)
	y_train['I_count'] = tf.cast(df.loc[train_start:train_end, 'icu_count'], dtype=tf.float32)
	y_train['D_in'] = tf.cast(df.loc[train_start:train_end, 'deaths_covid'], dtype=tf.float32)

	y_test = {}
	y_test['G_in'] = tf.cast(df.loc[train_start:test_end, 'general_ward_in'], dtype=tf.float32)
	y_test['G_count'] = tf.cast(df.loc[train_start:test_end, 'general_ward_count'], dtype=tf.float32)
	y_test['I_count'] = tf.cast(df.loc[train_start:test_end, 'icu_count'], dtype=tf.float32)
	y_test['D_in'] = tf.cast(df.loc[train_start:test_end, 'deaths_covid'], dtype=tf.float32)
	config = ModelConfig.from_json(model_config_path)
	model = CovidModel([Vax.no, Vax.yes], [Comp.A, Comp.M, Comp.G, Comp.GR, Comp.I, Comp.IR, Comp.D],
	                   transition_window,
	                   config, posterior_samples=1000,
	                   debug_disable_theta=False, fix_variance=False)

	preds=tf.reduce_mean(model.call(x_test), axis=-1)
	#set up
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

  	# update param sheet
	param_worksheet = gc.open_by_url(link).get_worksheet(3)

	worksheet = gc.open_by_url(link).get_worksheet(1)
	#set cell_list for each column and iterate to fill up with values
	all_days = np.datetime_as_string(all_days, unit='D')
	#clear sheet
	clear_range = 'A1' + ':G' + str(3000)
	clear_list = worksheet.range(clear_range)
	for cell in clear_list:
		cell.value = ''
	worksheet.update_cells(clear_list)
	#set up top row (period, timestep, date, ANY_to_HG)
	cell_list = worksheet.range('A1:G1')
	cell_list[0].value = 'PERIOD'
	cell_list[1].value = 'TIMESTEP'
	cell_list[2].value = 'DATE'
	cell_list[3].value = 'general_ward_in'
	cell_list[4].value = 'general_ward_count'
	cell_list[5].value = 'ICU_count'
	cell_list[6].value = 'deaths_covid'
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

	#G_in
	G_in_data = preds[0][1].numpy().tolist()
	#G_in_range = 'D2' + ':D' + end_timestep
	G_in_range = 'D' + start_train + ':D' + end_timestep
	G_in_list = worksheet.range(G_in_range)
	for i, cell in enumerate(G_in_list):
		cell.value = G_in_data[i]
	worksheet.update_cells(G_in_list)

	#G_count
	G_count_data = preds[0][0].numpy().tolist()
	#G_count_range = 'E2' + ':E' + end_timestep
	G_count_range = 'E' + start_train + ':E' + end_timestep
	G_count_list = worksheet.range(G_count_range)
	for i, cell in enumerate(G_count_list):
		cell.value = G_count_data[i]
	worksheet.update_cells(G_count_list)

	#I_count
	I_count_data = preds[0][2].numpy().tolist()
	#I_count_range = 'F2' + ':F' + end_timestep
	I_count_range = 'F' + start_train + ':F' + end_timestep
	I_count_list = worksheet.range(I_count_range)
	for i, cell in enumerate(I_count_list):
		cell.value = I_count_data[i]
	worksheet.update_cells(I_count_list)

	#Death
	D_data = preds[0][3].numpy().tolist()
	D_range = 'G' + start_train + ':G' + end_timestep
	D_list = worksheet.range(D_range)
	for i, cell in enumerate(D_list):
		cell.value = D_data[i]
	worksheet.update_cells(D_list)


	###########
	pred_draws = model.call(x_test)
	numpy_draws  = pred_draws.numpy().squeeze()
	pred_G_count = numpy_draws[0,:,:]
	pred_G_in =  numpy_draws[1,:,:]
	pred_I_count = numpy_draws[2,:,:]
	pred_D_in = numpy_draws[3,:,:]

	pred_G_count_lower, pred_G_count_mean, pred_G_count_upper = (np.percentile(pred_G_count,2.5, axis=1),
	                                                             np.mean(pred_G_count, axis=1),
	                                                             np.percentile(pred_G_count,97.5, axis=1))

	pred_G_in_lower, pred_G_in_mean, pred_G_in_upper = (np.percentile(pred_G_in,2.5, axis=1),
	                                                             np.mean(pred_G_in, axis=1),
	                                                             np.percentile(pred_G_in,97.5, axis=1))

	pred_I_count_lower, pred_I_count_mean, pred_I_count_upper = (np.percentile(pred_I_count,2.5, axis=1),
	                                                             np.mean(pred_I_count, axis=1),
	                                                             np.percentile(pred_I_count,97.5, axis=1))

	pred_D_in_lower, pred_D_in_mean, pred_D_in_upper = (np.percentile(pred_D_in,2.5, axis=1),
	                                                             np.mean(pred_D_in, axis=1),
	                                                             np.percentile(pred_D_in,97.5, axis=1))

	##########
	plt.figure(figsize=(20, 12))
	plt.plot(df.loc[train_start:test_end].index.values, pred_I_count_mean, label='Predicted Mean')
	plt.plot(df.loc[train_start:test_end].index.values, y_test['I_count'], label='Data')
	plt.fill_between(df.loc[train_start:test_end].index.values, pred_I_count_lower, pred_I_count_upper,
	                label='95% CI', alpha=0.3)

	max_y = max(max(pred_I_count_upper), max(y_test['I_count']))
	plt.plot([df.loc[train_end:train_end].index.values, df.loc[train_end:train_end].index.values], [0,max_y],
	         '--', color='red',linewidth=5, alpha=0.15, label='Train/Test Split')

	month_ticks = matplotlib.dates.MonthLocator(interval=1)
	ax = plt.gca()
	ax.xaxis.set_major_locator(month_ticks)
	plt.legend()
	plt.ylabel('Patients')
	plt.title('ICU Census')
	#####################
	plt.figure(figsize=(20, 12))
	plt.plot(df.loc[train_start:test_end].index.values, pred_G_count_mean, label='Predicted Mean')
	plt.plot(df.loc[train_start:test_end].index.values, y_test['G_count'], label='Data')
	plt.fill_between(df.loc[train_start:test_end].index.values, pred_G_count_lower, pred_G_count_upper,
	                label='95% CI', alpha=0.3)

	max_y = max(max(pred_G_count_upper), max(y_test['G_count']))
	plt.plot([df.loc[train_end:train_end].index.values, df.loc[train_end:train_end].index.values], [0,max_y],
	         '--', color='red',linewidth=5, alpha=0.15, label='Train/Test Split')

	month_ticks = matplotlib.dates.MonthLocator(interval=1)
	ax = plt.gca()
	ax.xaxis.set_major_locator(month_ticks)
	plt.legend()
	plt.ylabel('Patients')
	plt.title('General Ward Census')
	##########################3

	plt.figure(figsize=(20, 12))
	plt.plot(df.loc[train_start:test_end].index.values, pred_G_in_mean, label='Predicted Mean')
	plt.plot(df.loc[train_start:test_end].index.values, y_test['G_in'], label='Data')
	plt.fill_between(df.loc[train_start:test_end].index.values, pred_G_in_lower, pred_G_in_upper,
	                label='95% CI', alpha=0.3)

	max_y = max(max(pred_G_in_upper), max(y_test['G_in']))
	plt.plot([df.loc[train_end:train_end].index.values, df.loc[train_end:train_end].index.values], [0,max_y],
	         '--', color='red',linewidth=5, alpha=0.15, label='Train/Test Split')

	month_ticks = matplotlib.dates.MonthLocator(interval=1)
	ax = plt.gca()
	ax.xaxis.set_major_locator(month_ticks)
	plt.legend()
	plt.ylabel('Patients')
	plt.title('General Ward Daily New Patients')
#####################
	plt.figure(figsize=(20, 12))
	plt.plot(df.loc[train_start:test_end].index.values, pred_D_in_mean, label='Predicted Mean')
	plt.plot(df.loc[train_start:test_end].index.values, y_test['D_in'], label='Data')
	plt.fill_between(df.loc[train_start:test_end].index.values, pred_D_in_lower, pred_D_in_upper,
	                label='95% CI', alpha=0.3)

	max_y = max(max(pred_D_in_upper), max(y_test['D_in']))
	plt.plot([df.loc[train_end:train_end].index.values, df.loc[train_end:train_end].index.values], [0,max_y],
	         '--', color='red',linewidth=5, alpha=0.15, label='Train/Test Split')

	month_ticks = matplotlib.dates.MonthLocator(interval=1)
	ax = plt.gca()
	ax.xaxis.set_major_locator(month_ticks)
	plt.legend()
	plt.ylabel('Patients')
	plt.title('Daily Deaths')

	return model

def project_only(link):
	auth.authenticate_user()
	#gc = gspread.authorize(GoogleCredentials.get_application_default())
	creds, _ = default()
	gc = gspread.authorize(creds)
	wb = gc.open_by_url(link)
	wks = wb.sheet1
	sheetData = wks.get_all_values()
	worksheet2 = gc.open_by_url(link).get_worksheet(2)
	model_config_path = '/content/drive/MyDrive/BayesianCovidPopulationModel/model_config.json'
	return run_sheetModel_noTrain(sheetData, worksheet2, link, gc, model_config_path)

def transfer_suggestion(link):
	auth.authenticate_user()
	#gc = gspread.authorize(GoogleCredentials.get_application_default())
	creds, _ = default()
	gc = gspread.authorize(creds)
	wb = gc.open_by_url(link)
	wks = wb.sheet1
	sheetData = wks.get_all_values()
	state = sheetData[5][1]
	state_abbrev = sheetData[6][1]
	ratio_g, ratio_i = calculate_ratio(link, state, state_abbrev)
	print("Your selected state: ", state)
	print("recommended ratio for general ward: ", ratio_g)
	print("recommended ratio for ICU: ", ratio_i)

	to_update = input("Do you want to update with recommended ratios for your selected state (Y/N): ")
	if (to_update == 'Y'):
		update_ratio(link, ratio_g, ratio_i)
		print("Ratios updated!")
	elif (to_update == 'N'):
		print("Ratios not updated!")
	else:
		print("Invalid input!")

def transfer_test(link):
	auth.authenticate_user()
	#gc = gspread.authorize(GoogleCredentials.get_application_default())
	creds, _ = default()
	gc = gspread.authorize(creds)
	wb = gc.open_by_url(link)
	wks = wb.sheet1
	sheetData = wks.get_all_values()
	state = sheetData[5][1]
	state_abbrev = sheetData[6][1]
	ratio_g, ratio_i = calculate_ratio(link, state, state_abbrev)
	update_ratio(link, ratio_g, ratio_i)
	load_default_data(link)
	#option for Rt
	spreadsheet_to_json(link)
	return project_only(link)

def customized_test(link):
	spreadsheet_to_json(link)
	#just show the ratio,
	return project_only(link)

def update_allparam(link):
	auth.authenticate_user()
	#gc = gspread.authorize(GoogleCredentials.get_application_default())
	creds, _ = default()
	gc = gspread.authorize(creds)
	wks_allparam = gc.open_by_url(link).get_worksheet(3)
	data_dur_vax = gc.open_by_url(link).get_worksheet(4).get_all_values()
	data_dur_unvax = gc.open_by_url(link).get_worksheet(5).get_all_values()
	data_trans = gc.open_by_url(link).get_worksheet(6).get_all_values()

	for i in range(5):
		#unvax lambda
		wks_allparam.update_cell(33 + 4 * i, 5, data_dur_unvax[4 + i][4])
		wks_allparam.update_cell(33 + 4 * i, 6, data_dur_unvax[4 + i][5])
		#unvax nu
		wks_allparam.update_cell(58 + 4 * i, 5, data_dur_unvax[4 + i][7])
		wks_allparam.update_cell(58 + 4 * i, 6, data_dur_unvax[4 + i][8])

		#vax lambda
		wks_allparam.update_cell(34 + 4 * i, 5, data_dur_vax[4 + i][4])
		wks_allparam.update_cell(34 + 4 * i, 6, data_dur_vax[4 + i][5])
		#vax nu
		wks_allparam.update_cell(59 + 4 * i, 5, data_dur_vax[4 + i][7])
		wks_allparam.update_cell(59 + 4 * i, 6, data_dur_vax[4 + i][8])

	for i in range(4):
		wks_allparam.update_cell(22 + i, 5, data_trans[1 + i][1])

	print("AllParam has been updated --> ready for spreadsheet_to_json")