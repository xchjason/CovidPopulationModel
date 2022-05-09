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

  us_state_to_abbrev = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
  }

  state = sheetData[5][1]
  state_abbrev = us_state_to_abbrev[state]

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


def run_sheetModel_noTrain(sheetData, worksheet2, link, gc, model_config_path=None):
	warmup_start = convert_date(sheetData[2][2])
	warmup_end = convert_date(sheetData[2][3])
	train_start = convert_date(sheetData[3][2])
	train_end = convert_date(sheetData[3][3])
	test_start = convert_date(sheetData[4][2])
	test_end = convert_date(sheetData[4][3])

	us_state_to_abbrev = {
	"Alabama": "AL",
	"Alaska": "AK",
	"Arizona": "AZ",
	"Arkansas": "AR",
	"California": "CA",
	"Colorado": "CO",
	"Connecticut": "CT",
	"Delaware": "DE",
	"Florida": "FL",
	"Georgia": "GA",
	"Hawaii": "HI",
	"Idaho": "ID",
	"Illinois": "IL",
	"Indiana": "IN",
	"Iowa": "IA",
	"Kansas": "KS",
	"Kentucky": "KY",
	"Louisiana": "LA",
	"Maine": "ME",
	"Maryland": "MD",
	"Massachusetts": "MA",
	"Michigan": "MI",
	"Minnesota": "MN",
	"Mississippi": "MS",
	"Missouri": "MO",
	"Montana": "MT",
	"Nebraska": "NE",
	"Nevada": "NV",
	"New Hampshire": "NH",
	"New Jersey": "NJ",
	"New Mexico": "NM",
	"New York": "NY",
	"North Carolina": "NC",
	"North Dakota": "ND",
	"Ohio": "OH",
	"Oklahoma": "OK",
	"Oregon": "OR",
	"Pennsylvania": "PA",
	"Rhode Island": "RI",
	"South Carolina": "SC",
	"South Dakota": "SD",
	"Tennessee": "TN",
	"Texas": "TX",
	"Utah": "UT",
	"Vermont": "VT",
	"Virginia": "VA",
	"Washington": "WA",
	"West Virginia": "WV",
	"Wisconsin": "WI",
	"Wyoming": "WY",
	}

	state = sheetData[5][1]
	state_abbrev = us_state_to_abbrev[state]

	data_dir = './data'
	covid_estim_date = '20211210'
	hhs_date = '20211210'
	owid_date = '20211210'

	log_dir = './logs/test_run_1'

	"""### Model Settings"""

	# How long can a person take to progress?
	transition_window = 10

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

def basic_project():
	link = read_sheet_link()
	load_default_data(link)
	json_to_spreadsheet(link, "model_config.json")
	return project_only(link)

def softplus_np(x): 
	return np.log1p(np.exp(-np.abs(x))) + np.maximum(x, 0)

def transfer_project():
	link = read_sheet_link()
	load_default_data(link)
	json_to_spreadsheet(link, "model_config.json")
	return transfer_test(link)

def transfer_suggestion(link):
	auth.authenticate_user()
	#gc = gspread.authorize(GoogleCredentials.get_application_default())
	creds, _ = default()
	gc = gspread.authorize(creds)
	wb = gc.open_by_url(link)
	wks = wb.sheet1
	sheetData = wks.get_all_values()
	us_state_to_abbrev = {
		"Alabama": "AL",
		"Alaska": "AK",
		"Arizona": "AZ",
		"Arkansas": "AR",
		"California": "CA",
		"Colorado": "CO",
		"Connecticut": "CT",
		"Delaware": "DE",
		"Florida": "FL",
		"Georgia": "GA",
		"Hawaii": "HI",
		"Idaho": "ID",
		"Illinois": "IL",
		"Indiana": "IN",
		"Iowa": "IA",
		"Kansas": "KS",
		"Kentucky": "KY",
		"Louisiana": "LA",
		"Maine": "ME",
		"Maryland": "MD",
		"Massachusetts": "MA",
		"Michigan": "MI",
		"Minnesota": "MN",
		"Mississippi": "MS",
		"Missouri": "MO",
		"Montana": "MT",
		"Nebraska": "NE",
		"Nevada": "NV",
		"New Hampshire": "NH",
		"New Jersey": "NJ",
		"New Mexico": "NM",
		"New York": "NY",
		"North Carolina": "NC",
		"North Dakota": "ND",
		"Ohio": "OH",
		"Oklahoma": "OK",
		"Oregon": "OR",
		"Pennsylvania": "PA",
		"Rhode Island": "RI",
		"South Carolina": "SC",
		"South Dakota": "SD",
		"Tennessee": "TN",
		"Texas": "TX",
		"Utah": "UT",
		"Vermont": "VT",
		"Virginia": "VA",
		"Washington": "WA",
		"West Virginia": "WV",
		"Wisconsin": "WI",
		"Wyoming": "WY",
	}

	state = sheetData[5][1]
	trained_state = sheetData[6][1]
	trained_state_abbrev = us_state_to_abbrev[trained_state]

	ratio_g, ratio_i = calculate_ratio(link, trained_state, trained_state_abbrev)
	print("Your target state: ", state)
	print("Your trained state: ", trained_state)
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

	us_state_to_abbrev = {
		"Alabama": "AL",
		"Alaska": "AK",
		"Arizona": "AZ",
		"Arkansas": "AR",
		"California": "CA",
		"Colorado": "CO",
		"Connecticut": "CT",
		"Delaware": "DE",
		"Florida": "FL",
		"Georgia": "GA",
		"Hawaii": "HI",
		"Idaho": "ID",
		"Illinois": "IL",
		"Indiana": "IN",
		"Iowa": "IA",
		"Kansas": "KS",
		"Kentucky": "KY",
		"Louisiana": "LA",
		"Maine": "ME",
		"Maryland": "MD",
		"Massachusetts": "MA",
		"Michigan": "MI",
		"Minnesota": "MN",
		"Mississippi": "MS",
		"Missouri": "MO",
		"Montana": "MT",
		"Nebraska": "NE",
		"Nevada": "NV",
		"New Hampshire": "NH",
		"New Jersey": "NJ",
		"New Mexico": "NM",
		"New York": "NY",
		"North Carolina": "NC",
		"North Dakota": "ND",
		"Ohio": "OH",
		"Oklahoma": "OK",
		"Oregon": "OR",
		"Pennsylvania": "PA",
		"Rhode Island": "RI",
		"South Carolina": "SC",
		"South Dakota": "SD",
		"Tennessee": "TN",
		"Texas": "TX",
		"Utah": "UT",
		"Vermont": "VT",
		"Virginia": "VA",
		"Washington": "WA",
		"West Virginia": "WV",
		"Wisconsin": "WI",
		"Wyoming": "WY",
	}

	trained_state = sheetData[6][1]
	trained_state_abbrev = us_state_to_abbrev[trained_state]
	ratio_g, ratio_i = calculate_ratio(link, trained_state, trained_state_abbrev)
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
		wks_allparam.update_cell(22 + i, 5, data_trans[4 + i][4])
		wks_allparam.update_cell(26 + i, 5, data_trans[4 + i][9])

	print("AllParam has been updated --> ready for spreadsheet_to_json")