import json
import numpy as np
from google.colab import auth
from model_config import replace_keys
import gspread
from oauth2client.client import GoogleCredentials

def json_to_spreadsheet(link, file):
	with open(file, 'r') as openfile:
	    data = json.load(openfile)

	auth.authenticate_user()
	gc = gspread.authorize(GoogleCredentials.get_application_default())
	allparam_sheet = gc.open_by_url(link).get_worksheet(4)

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
		allparam_sheet.update_cell(13+i*2, 5, data['rho'][s]['prior']['0']['a'])
		allparam_sheet.update_cell(14+i*2, 5, data['rho'][s]['prior']['1']['a'])
		allparam_sheet.update_cell(22+i*2, 5, data['rho'][s]['value']['0']['loc'])
		allparam_sheet.update_cell(23+i*2, 5, data['rho'][s]['value']['1']['loc'])

		allparam_sheet.update_cell(13+i*2, 6, data['rho'][s]['prior']['0']['b'])
		allparam_sheet.update_cell(14+i*2, 6, data['rho'][s]['prior']['1']['b'])
		allparam_sheet.update_cell(22+i*2, 6, data['rho'][s]['value']['0']['scale'])
		allparam_sheet.update_cell(23+i*2, 6, data['rho'][s]['value']['1']['scale'])

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

def spreadsheet_to_json(link):
	auth.authenticate_user()
	gc = gspread.authorize(GoogleCredentials.get_application_default())
	wb = gc.open_by_url(link)
	wks = wb.get_worksheet(4)
	data = wks.get_all_values()
	#print(data)
	#print(data[112][6])

	jdata = {}
	jdata['T_serial']={}
	jdata['T_serial']['prior'] = {'loc': data[1][2], 'scale': data[1][3]}
	jdata['T_serial']['value'] = {'loc': data[2][2], 'scale': data[2][3]}
	jdata['delta'] = {}
	jdata['delta']['prior'] = {'a': data[4][2], 'b': data[4][3]}
	jdata['delta']['value'] = {'loc': data[6][2], 'scale': data[6][3]}
	jdata['epsilon'] = {}
	jdata['epsilon']['prior'] = {'a': data[8][2], 'b': data[8][3]}
	jdata['epsilon']['value'] = {'loc': data[10][2], 'scale': data[10][3]}

	jdata['rho']={}
	jdata['rho']['M']={}
	jdata['rho']['M']['prior'] = {'0': {'a': data[12][4], 'b': data[12][5]},'1': {'a': data[13][4], 'b': data[13][5]}}
	jdata['rho']['M']['value'] = {'0': {'loc': data[21][4], 'scale': data[21][5]},'1': {'loc': data[22][4], 'scale': data[22][5]}}
	jdata['rho']['G'] = {}
	jdata['rho']['G']['prior'] = {'0': {'a': data[14][4], 'b': data[14][5]},'1': {'a': data[15][4], 'b': data[15][5]}}
	jdata['rho']['G']['value'] = {'0': {'loc': data[23][4], 'scale': data[23][5]},'1': {'loc': data[24][4], 'scale': data[24][5]}}
	jdata['rho']['I'] = {}
	jdata['rho']['I']['prior'] = {'0': {'a': data[16][4], 'b': data[16][5]},'1': {'a': data[17][4], 'b': data[17][5]}}
	jdata['rho']['I']['value'] = {'0': {'loc': data[25][4], 'scale': data[25][5]},'1': {'loc': data[26][4], 'scale': data[26][5]}}
	jdata['rho']['D'] = {}
	jdata['rho']['D']['prior'] = {'0': {'a': data[18][4], 'b': data[18][5]},'1': {'a': data[19][4], 'b': data[19][5]}}
	jdata['rho']['D']['value'] = {'0': {'loc': data[27][4], 'scale': data[27][5]},'1': {'loc': data[28][4], 'scale': data[28][5]}}

	lambda_stages = ['M', 'G', 'I', 'I_bar', 'D', 'D_bar']
	jdata['lambda']={}
	for i, s in enumerate(lambda_stages):
		jdata['lambda'][s] = {}
		jdata['lambda'][s]['prior'] =  {'0': {'loc': data[30+i*4][4], 'scale': data[30+i*4][5]},'1': {'loc': data[31+i*4][4], 'scale': data[31+i*4][5]}}
		jdata['lambda'][s]['value'] =  {'0': {'loc': data[32+i*4][4], 'scale': data[32+i*4][5]},'1': {'loc': data[33+i*4][4], 'scale': data[33+i*4][5]}}

	nu_stages = ['M', 'G', 'I', 'I_bar', 'D', 'D_bar']
	jdata['nu'] = {}
	for i, s in enumerate(nu_stages):
		jdata['nu'][s] = {}
		jdata['nu'][s]['prior'] =  {'0': {'loc': data[55+i*4][4], 'scale': data[55+i*4][5]},'1': {'loc': data[56+i*4][4], 'scale': data[56+i*4][5]}}
		jdata['nu'][s]['value'] =  {'0': {'loc': data[57+i*4][4], 'scale': data[57+i*4][5]},'1': {'loc': data[58+i*4][4], 'scale': data[58+i*4][5]}}

	warmup_stages = ['A', 'M', 'G', 'GR', 'I', 'IR']
	jdata['warmup'] = {}
	for i, s in enumerate(warmup_stages):
		jdata['warmup'][s] = {}
		jdata['warmup'][s]['prior'] =  {'0': {'slope': data[89+i*4][4], 'intercept': data[89+i*4][5],'scale': data[89+i*4][6]},'1': {'slope': data[90+i*4][4], 'intercept': data[90+i*4][5],'scale': data[90+i*4][6]}}
		jdata['warmup'][s]['value'] =  {'0': {'slope': data[91+i*4][4], 'intercept': data[91+i*4][5],'scale': data[91+i*4][6]},'1': {'slope': data[92+i*4][4], 'intercept': data[92+i*4][5],'scale': data[92+i*4][6]}}

	init_count_stages = ['G', 'I']
	jdata['init_count'] = {}
	for i, s in enumerate(init_count_stages):
		jdata['init_count'][s] = {}
		jdata['init_count'][s]['prior'] =  {'0': {'loc': data[80+i*4][4], 'scale': data[80+i*4][5]},'1': {'loc': data[81+i*4][4], 'scale': data[81+i*4][5]}}
		jdata['init_count'][s]['value'] =  {'0': {'loc': data[82+i*4][4], 'scale': data[82+i*4][5]},'1': {'loc': data[83+i*4][4], 'scale': data[83+i*4][5]}}

	jdata = replace_keys(jdata, str, from_tensor=True)

	out_file = open("model_config.json", "w")
	json.dump(jdata, out_file)
	out_file.close()