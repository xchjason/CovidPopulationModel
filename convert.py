import json
import numpy as np
from google.colab import auth
from model_config import replace_keys
from data import read_data, create_warmup
import gspread
from oauth2client.client import GoogleCredentials
from google.auth import default

def json_to_spreadsheet(link, file):
	with open(file, 'r') as openfile:
	    data = json.load(openfile)

	auth.authenticate_user()
	#gc = gspread.authorize(GoogleCredentials.get_application_default())
	creds, _ = default()
	gc = gspread.authorize(creds)
	allparam_sheet = gc.open_by_url(link).get_worksheet(3)

	allparam_sheet.update_cell(2, 3, str(data['T_serial']['prior']['loc']))
	allparam_sheet.update_cell(3, 3, str(data['T_serial']['value']['loc']))
	allparam_sheet.update_cell(2, 4, str(data['T_serial']['prior']['scale']))
	allparam_sheet.update_cell(3, 4, data['T_serial']['value']['scale'])

	allparam_sheet.update_cell(5, 3, data['delta']['prior']['a'])
	allparam_sheet.update_cell(7, 3, data['delta']['value']['loc'])
	allparam_sheet.update_cell(5, 4, data['delta']['prior']['b'])
	allparam_sheet.update_cell(7, 4, data['delta']['value']['scale'])

	allparam_sheet.update_cell(9, 3, data['epsilon']['prior']['a'])
	allparam_sheet.update_cell(11, 3, data['epsilon']['value']['loc'])
	allparam_sheet.update_cell(9, 4, data['epsilon']['prior']['b'])
	allparam_sheet.update_cell(11, 4, data['epsilon']['value']['scale'])


	rho_stages = ['M', 'G', 'I', 'D']

	for i, s in enumerate(rho_stages):
		allparam_sheet.update_cell(13+i, 5, data['rho'][s]['prior']['0']['a'])
		allparam_sheet.update_cell(22+i, 5, data['rho'][s]['value']['0']['loc'])
		allparam_sheet.update_cell(13+i, 6, data['rho'][s]['prior']['0']['b'])
		allparam_sheet.update_cell(22+i, 6, data['rho'][s]['value']['0']['scale'])

		allparam_sheet.update_cell(17+i, 5, data['eff'][s]['prior']['1']['a'])
		allparam_sheet.update_cell(26+i, 5, data['eff'][s]['value']['1']['loc'])
		allparam_sheet.update_cell(17+i, 6, data['eff'][s]['prior']['1']['b'])
		allparam_sheet.update_cell(26+i, 6, data['eff'][s]['value']['1']['scale'])



	lambda_stages = ['M', 'G', 'I', 'I_bar', 'D', 'D_bar']
	for i, s in enumerate(lambda_stages):
		allparam_sheet.update_cell(31+i*4, 5, data['lambda'][s]['prior']['0']['loc'])
		allparam_sheet.update_cell(32+i*4, 5, data['lambda'][s]['prior']['1']['loc'])
		allparam_sheet.update_cell(33+i*4, 5, data['lambda'][s]['value']['0']['loc'])
		allparam_sheet.update_cell(34+i*4, 5, data['lambda'][s]['value']['1']['loc'])

		allparam_sheet.update_cell(31+i*4, 6, data['lambda'][s]['prior']['0']['scale'])
		allparam_sheet.update_cell(32+i*4, 6, data['lambda'][s]['prior']['1']['scale'])
		allparam_sheet.update_cell(33+i*4, 6, data['lambda'][s]['value']['0']['scale'])
		allparam_sheet.update_cell(34+i*4, 6, data['lambda'][s]['value']['1']['scale'])

	nu_stages = ['M', 'G', 'I', 'I_bar', 'D', 'D_bar']
	for i, s in enumerate(nu_stages):
		allparam_sheet.update_cell(56+i*4, 5, data['nu'][s]['prior']['0']['loc'])
		allparam_sheet.update_cell(57+i*4, 5, data['nu'][s]['prior']['1']['loc'])
		allparam_sheet.update_cell(58+i*4, 5, data['nu'][s]['value']['0']['loc'])
		allparam_sheet.update_cell(59+i*4, 5, data['nu'][s]['value']['1']['loc'])

		allparam_sheet.update_cell(56+i*4, 6, data['nu'][s]['prior']['0']['scale'])
		allparam_sheet.update_cell(57+i*4, 6, data['nu'][s]['prior']['1']['scale'])
		allparam_sheet.update_cell(58+i*4, 6, data['nu'][s]['value']['0']['scale'])
		allparam_sheet.update_cell(59+i*4, 6, data['nu'][s]['value']['1']['scale'])

	init_count_stages = ['G', 'I']
	for i, s in enumerate(init_count_stages):
		allparam_sheet.update_cell(81+i*4, 5, data['init_count'][s]['prior']['0']['loc'])
		allparam_sheet.update_cell(82+i*4, 5, data['init_count'][s]['prior']['1']['loc'])
		allparam_sheet.update_cell(83+i*4, 5, data['init_count'][s]['value']['0']['loc'])
		allparam_sheet.update_cell(84+i*4, 5, data['init_count'][s]['value']['1']['loc'])

		allparam_sheet.update_cell(81+i*4, 6, data['init_count'][s]['prior']['0']['scale'])
		allparam_sheet.update_cell(82+i*4, 6, data['init_count'][s]['prior']['1']['scale'])
		allparam_sheet.update_cell(83+i*4, 6, data['init_count'][s]['value']['0']['scale'])
		allparam_sheet.update_cell(84+i*4, 6, data['init_count'][s]['value']['1']['scale'])

	warmup_stages = ['A', 'M', 'G', 'GR', 'I', 'IR']
	for i, s in enumerate(warmup_stages):
		allparam_sheet.update_cell(90+i*4, 5, data['warmup'][s]['prior']['0']['slope'])
		allparam_sheet.update_cell(91+i*4, 5, data['warmup'][s]['prior']['1']['slope'])
		allparam_sheet.update_cell(92+i*4, 5, data['warmup'][s]['value']['0']['slope'])
		allparam_sheet.update_cell(93+i*4, 5, data['warmup'][s]['value']['1']['slope'])

		allparam_sheet.update_cell(90+i*4, 6, data['warmup'][s]['prior']['0']['intercept'])
		allparam_sheet.update_cell(91+i*4, 6, data['warmup'][s]['prior']['1']['intercept'])
		allparam_sheet.update_cell(92+i*4, 6, data['warmup'][s]['value']['0']['intercept'])
		allparam_sheet.update_cell(93+i*4, 6, data['warmup'][s]['value']['1']['intercept'])

		allparam_sheet.update_cell(90+i*4, 7, data['warmup'][s]['prior']['0']['scale'])
		allparam_sheet.update_cell(91+i*4, 7, data['warmup'][s]['prior']['1']['scale'])
		allparam_sheet.update_cell(92+i*4, 7, data['warmup'][s]['value']['0']['scale'])
		allparam_sheet.update_cell(93+i*4, 7, data['warmup'][s]['value']['1']['scale'])

def update_ratio(link, ratio_g, ratio_i):
	auth.authenticate_user()
	#gc = gspread.authorize(GoogleCredentials.get_application_default())
	creds, _ = default()
	gc = gspread.authorize(creds)
	setting_sheet = gc.open_by_url(link).get_worksheet(0)
	setting_sheet.update_cell(9, 2, ratio_g)
	setting_sheet.update_cell(10, 2, ratio_g)

def softplus_np(x): 
	return np.log1p(np.exp(-np.abs(x))) + np.maximum(x, 0)

def softplus_inv(x): 
	return np.log(np.expm1(x))

def calculate_ratio(link, state, state_abbrev):
	auth.authenticate_user()
	#gc = gspread.authorize(GoogleCredentials.get_application_default())
	creds, _ = default()
	gc = gspread.authorize(creds)
	#read in the date setting
	wb = gc.open_by_url(link)
	wks = wb.sheet1
	sheetData = wks.get_all_values()

	wks4 = wb.get_worksheet(3)
	alldata = wks4.get_all_values()

	train_start = (sheetData[3][2])

	data_dir = './data'
	covid_estim_date = '20211210'
	hhs_date = '20211210'
	owid_date = '20211210'

	log_dir = './logs/test_run_1'

	df = read_data(data_dir=data_dir,
	             covid_estim_date=covid_estim_date,
	             hhs_date=hhs_date,
	             owid_date=owid_date,
	             state=state, state_abbrev=state_abbrev)

	ratio_g = df['general_ward_count'][train_start]/(softplus_np(100 * float(alldata[82][4]))+ softplus_np(100 * float(alldata[83][4])))
	ratio_i = df['icu_count'][train_start]/(softplus_np(100 * float(alldata[86][4]))+ softplus_np(100 * float(alldata[87][4])))
	return ratio_g, ratio_i


def spreadsheet_to_json(link):
	auth.authenticate_user()
	#gc = gspread.authorize(GoogleCredentials.get_application_default())
	creds, _ = default()
	gc = gspread.authorize(creds)
	wb = gc.open_by_url(link)
	wks = wb.get_worksheet(3)
	data = wks.get_all_values()

	firstSheet = wb.sheet1
	firstData = firstSheet.get_all_values()
	ratio = float(firstData[8][1])
	ratio_i = float(firstData[9][1])

	jdata = {}
	jdata['T_serial']={}
	jdata['T_serial']['prior'] = {'loc': data[1][2], 'scale': data[1][3]}
	jdata['T_serial']['value'] = {'loc': data[2][2], 'scale': data[2][3]}
	#jdata['T_serial']['mean_transform'] = 'softplus'

	jdata['delta'] = {}
	jdata['delta']['prior'] = {'a': data[4][2], 'b': data[4][3]}
	jdata['delta']['value'] = {'loc': data[6][2], 'scale': data[6][3]}
	#jdata['delta']['mean_transform'] = 'sigmoid'

	jdata['epsilon'] = {}
	jdata['epsilon']['prior'] = {'a': data[8][2], 'b': data[8][3]}
	jdata['epsilon']['value'] = {'loc': data[10][2], 'scale': data[10][3]}
	#jdata['epsilon']['mean_transform'] = 'sigmoid'


	rho_stages = ['M', 'G', 'I', 'D']
	jdata['rho']={}
	for i, s in enumerate(rho_stages):
		jdata['rho'][s] = {}
		jdata['rho'][s]['prior'] =  {'0': {'a': data[12+i][4], 'b': data[12+i][5]}}
		jdata['rho'][s]['value'] =  {'0': {'loc': data[21+i][4], 'scale': data[21+i][5]}}	
	#jdata['rho']['mean_transform'] = 'sigmoid'


	eff_stages = ['M', 'G', 'I', 'D']
	jdata['eff']={}
	for i, s in enumerate(eff_stages):
		jdata['eff'][s] = {}
		jdata['eff'][s]['prior'] =  {'1': {'a': data[16+i][4], 'b': data[16+i][5]}}
		jdata['eff'][s]['value'] =  {'1': {'loc': data[25+i][4], 'scale': data[25+i][5]}}	
	#jdata['eff']['mean_transform'] = 'sigmoid'

	lambda_stages = ['M', 'G', 'I', 'I_bar', 'D', 'D_bar']
	jdata['lambda']={}
	for i, s in enumerate(lambda_stages):
		jdata['lambda'][s] = {}
		jdata['lambda'][s]['prior'] =  {'0': {'loc': data[30+i*4][4], 'scale': data[30+i*4][5]},'1': {'loc': data[31+i*4][4], 'scale': data[31+i*4][5]}}
		jdata['lambda'][s]['value'] =  {'0': {'loc': data[32+i*4][4], 'scale': data[32+i*4][5]},'1': {'loc': data[33+i*4][4], 'scale': data[33+i*4][5]}}
	#jdata['lambda']['mean_transform'] = 'softplus'

	nu_stages = ['M', 'G', 'I', 'I_bar', 'D', 'D_bar']
	jdata['nu'] = {}
	for i, s in enumerate(nu_stages):
		jdata['nu'][s] = {}
		jdata['nu'][s]['prior'] =  {'0': {'loc': data[55+i*4][4], 'scale': data[55+i*4][5]},'1': {'loc': data[56+i*4][4], 'scale': data[56+i*4][5]}}
		jdata['nu'][s]['value'] =  {'0': {'loc': data[57+i*4][4], 'scale': data[57+i*4][5]},'1': {'loc': data[58+i*4][4], 'scale': data[58+i*4][5]}}
	#jdata['nu']['mean_transform'] = 'softplus'

	warmup_stages = ['A', 'M', 'G', 'GR', 'I', 'IR']
	jdata['warmup'] = {}
	for i, s in enumerate(warmup_stages):
		jdata['warmup'][s] = {}
		jdata['warmup'][s]['prior'] =  {'0': {'slope': data[89+i*4][4], 'intercept': data[89+i*4][5],'scale': data[89+i*4][6]},'1': {'slope': data[90+i*4][4], 'intercept': data[90+i*4][5],'scale': data[90+i*4][6]}}
		jdata['warmup'][s]['value'] =  {'0': {'slope': data[91+i*4][4], 'intercept': softplus_inv((softplus_np(100 * float(data[91+i*4][5])) * ratio)/100),'scale': data[91+i*4][6]},'1': {'slope': data[92+i*4][4], 'intercept': softplus_inv((softplus_np(100 * float(data[92+i*4][5])) * ratio)/100),'scale': data[92+i*4][6]}}
	#jdata['warmup']['mean_transform'] = 'scale_100_softplus'

	#softplus_inv((softplus_np(100 * float(data[83+i*4][4])) * ratio)/100)

	init_count_stages = ['G', 'I']
	jdata['init_count'] = {}
	for i, s in enumerate(init_count_stages):
		jdata['init_count'][s] = {}
		jdata['init_count'][s]['prior'] =  {'0': {'loc': data[80+i*4][4], 'scale': data[80+i*4][5]},'1': {'loc': data[81+i*4][4], 'scale': data[81+i*4][5]}}
		jdata['init_count'][s]['value'] =  {'0': {'loc': softplus_inv((softplus_np(100 * float(data[82+i*4][4])) * ratio)/100), 'scale': data[82+i*4][5]},'1': {'loc': softplus_inv((softplus_np(100 * float(data[83+i*4][4])) * ratio)/100), 'scale': data[83+i*4][5]}}
	#jdata['warmup']['mean_transform'] = 'scale_100_softplus'

	jdata['init_count']['I']['value']['0']['loc'] = softplus_inv((softplus_np(100 * float(data[86][4])) * ratio_i)/100)
	jdata['init_count']['I']['value']['1']['loc'] = softplus_inv((softplus_np(100 * float(data[87][4])) * ratio_i)/100)

	jdata['warmup']['I']['value']['0']['intercept'] = softplus_inv((softplus_np(100 * float(data[107][5])) * ratio_i)/100)
	jdata['warmup']['I']['value']['1']['intercept'] = softplus_inv((softplus_np(100 * float(data[108][5])) * ratio_i)/100)

	jdata['warmup']['IR']['value']['0']['intercept'] = softplus_inv((softplus_np(100 * float(data[111][5])) * ratio_i)/100)
	jdata['warmup']['IR']['value']['1']['intercept'] = softplus_inv((softplus_np(100 * float(data[112][5])) * ratio_i)/100)

	jdata = replace_keys(jdata, str, from_tensor=True)

	out_file = open("model_config.json", "w")
	json.dump(jdata, out_file, indent = 4)
	out_file.close()

