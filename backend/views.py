from django.shortcuts import render
import pathlib #get current path

#https://www.postgresqltutorial.com/postgresql-python/connect/
#https://www.postgresqltutorial.com/postgresql-python/
import psycopg2
#HttpRequest for ajax check
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
# Create your views here.
from django.template import loader
#https://stackoverflow.com/questions/22162027/how-do-i-generate-a-static-html-file-from-a-django-template
from django.template.loader import render_to_string
from .models import dashboard
from django.forms.models import model_to_dict
import hashlib #untuk Md5
#https://www.mongodb.com/blog/post/getting-started-with-python-and-mongodb
from pymongo import MongoClient
#https://pynative.com/python-mysql-database-connection/
import mysql.connector
from mysql.connector import Error
#https://stackoverflow.com/questions/3483318/performing-regex-queries-with-pymongo
import re
#https://api.mongodb.com/python/current/examples/custom_type.html
from bson.decimal128 import Decimal128, create_decimal128_context
#https://gist.github.com/jackiekazil/6201722
from decimal import Decimal
#https://stackoverflow.com/questions/16458166/how-to-disable-djangos-csrf-validation
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F

#---------------------------------------------------------------------testing
# from .models import test_scheduller
import pprint
#---------------------------------------------------------------------testing

from datetime import datetime #untuk print date time

#https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable
import json
import time
#https://stackoverflow.com/questions/6286192/using-json-in-django-template
from django.utils.safestring import SafeString
#https://django-background-tasks.readthedocs.io/en/latest/
from background_task import background #from background_task untuk menjalankan setiap waktu function yang ada

#https://stackoverflow.com/questions/757022/how-do-you-serialize-a-model-instance-in-django
#https://dev-yakuza.github.io/en/django/response-model-to-json/
from django.core import serializers #You can easily use a list to wrap the required object and that's all what django serializers need to correctly serialize it, eg
#https://realpython.com/python-csv/
import csv

#begin setup init
path_data_feeder = ""
#end setup init

base_http = "http://"
data_test = {}
context = {
	'additional_message' : "",
	'base_http' : base_http
}
# Begin Init variable catcher for insert dashboard
data_processed = {}
data_permission_add = False
data_permission_message = ""
checked_connection = False
# End Init variable catcher for insert dashboard

insert_data = {} #init dictionary (array string address) for insert 

limit_data_row_processing = 50000 #setting limit perfeeding
mongo_db_address = "mongodb://localhost:27017/"
database_setting = "DashboardGenerator"

data_cetak_test = {}

# Setup Connection to database without using models

def check_already_login(request):
	if not request.user.is_authenticated:
		return HttpResponseRedirect(str(context["base_http"]) + str(request.get_host()))
		
def index(request):
	if request.is_secure():
		context["base_http"] = 'https'
	if not request.user.is_authenticated:
		return HttpResponseRedirect(str(context["base_http"]) + str(request.get_host()))
	context['username'] = request.user.username
	#limit https://stackoverflow.com/questions/6574003/django-limiting-query-results
	context['data_list_dashboard'] = dashboard.objects.filter(dashboard_owner_id=request.user).exclude(dashboard_disabled=1)[0:10]
	
	# temp_json = serializers.serialize('json', context['data_list_dashboard'])
	# print(temp_json)
	
	template = loader.get_template('backend/index.html')
	return HttpResponse(template.render(context, request))
	
def show_form_insert(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			template = loader.get_template('backend/form_insert.html')
			return HttpResponse(template.render(context, request))
		else:
			return HttpResponse("It's Forbidden to try connect Here :) show_form_insert")
			
def delete_dashboard(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			kode_dashboard = request.POST["kode_dashboard_sending"]
			delete_collection(kode_dashboard)
			dashboard.objects.select_related().filter(dashboard_owner_id=request.user, dashboard_kode = kode_dashboard).update(dashboard_disabled=1)
			return HttpResponse("")
			
def toggle_public_view(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			kode_dashboard = request.POST["kode_dashboard_sending"]
			next_toggle = 1
			if str(request.POST["next_state"]) == "0":
				next_toggle = 0
			dashboard.objects.select_related().filter(dashboard_owner_id=request.user, dashboard_kode = kode_dashboard).update(dashboard_ready=next_toggle)
			return HttpResponse("")

def delete_collection(kode_dashboard):
	data_dashboard = dashboard.objects.filter(dashboard_kode=kode_dashboard, dashboard_tipe_data__lte = 2).exclude(dashboard_disabled=1)[0:1]
	if len(data_dashboard) != 1:
		return True
	data_list_tabel = {}
	for data in data_dashboard:
		data_list_tabel = json.loads(data.dashboard_list_relation_data)
	temporary = ""
	client = MongoClient(mongo_db_address)
	db=client[database_setting]
	for index, data in data_list_tabel.items():
		#https://www.w3schools.com/python/python_mongodb_drop_collection.asp
		mycol = db[data["mongo_db_collection_name"]]
		mycol.drop()
	

def refeeding_data(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			kode_dashboard = request.POST["kode_dashboard_sending"]
			data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=kode_dashboard, dashboard_state = 100, dashboard_tipe_data__lte = 2).exclude(dashboard_disabled=1)[0:1]
			data_list_tabel = {}
			list_tobe_feeded = ""
			data_return_dashboard = ""
			for data in data_dashboard:
				data_list_tabel = json.loads(data.dashboard_list_relation_data)
				data_return_dashboard = data
			for index, data in data_list_tabel.items():
				if (list_tobe_feeded == ""):
					list_tobe_feeded = str(data["id_tabel"])
				else:
					list_tobe_feeded = list_tobe_feeded + "," + str(data["id_tabel"])	
			delete_collection(kode_dashboard)
			dashboard.objects.select_related().filter(dashboard_kode = kode_dashboard, dashboard_state = 100, dashboard_tipe_data__lte = 2).update(dashboard_state=54, dashboard_list_count_tabels=list_tobe_feeded, dashboard_list_count_current_row_tabels=1)
			recalculate_dashboard_process(kode_dashboard, data_return_dashboard)
			return HttpResponse("")
			
def recalculate_dashboard(request, this_dashboard_kode):
	if request.user.is_authenticated:
		data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user, dashboard_kode=this_dashboard_kode, dashboard_state = 100).exclude(dashboard_disabled=1)[0:1]
		for data_dashboard_temporary in data_dashboard:
			recalculate_dashboard_process(this_dashboard_kode, data_dashboard_temporary)
		return HttpResponseRedirect('/backend/')

def recalculate_dashboard_process(this_dashboard_kode, data_dashboard):
	data_design = json.loads(data_dashboard.dashboard_design_json)
	for index1, data1 in data_design.items():
		for index2, data2 in data1.items():
			data_design[index1][index2]["already_processed"] = 0
			data_design[index1][index2]["data_processed"] = {}
			data_design[index1][index2]["additional_script_windows_already_loaded"] = ""
	temporary_dump = json.dumps(data_design, indent=4)
	dashboard.objects.select_related().filter(dashboard_kode = this_dashboard_kode).update(dashboard_design_json=temporary_dump)
	update_last_update(this_dashboard_kode)

def process_new_dashboard(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			insert_data["source_type"] = "database"
			if request.POST['dashboard_name'] == "": #check dashboard name should be filled
				data_permission_message = "Nama Dashboard Harus terisi"
				return HttpResponse(data_permission_message)
			else:
				insert_data["dashboard_name"] = request.POST['dashboard_name']
				
			if request.POST['source_type'] == "others": #check source type source_type default database, else value for others (xlxs and csv)
				insert_data["source_type"] = "others"
			
			if insert_data["source_type"] == "database":
				if "hostname" not in request.POST: #check dashboard name should be filled
					data_permission_message = "Hostname Harus terisi"
					return HttpResponse(data_permission_message)
				else:
					insert_data["hostname"] = request.POST['hostname']
				if "username" not in request.POST: #check dashboard name should be filled
					data_permission_message = "Database Username Harus terisi"
					return HttpResponse(data_permission_message)
				else:
					insert_data["username"] = request.POST['username']
				if "password" not in request.POST: #check dashboard name should be filled
					data_permission_message = "Database Password Harus terisi"
					return HttpResponse(data_permission_message)
				else:
					insert_data["password"] = request.POST['password']
				if "database_name" not in request.POST: #check dashboard name should be filled
					data_permission_message = "Database Name Harus terisi"
					return HttpResponse(data_permission_message)
				else:
					insert_data["database_name"] = request.POST['database_name']
				dashboard_insert = dashboard()
				if request.POST["connection_type"] == "postgresql":
					dashboard_insert.dashboard_tipe_data = 1 #tipe database POSTGRESQL
					if not check_databases_postgresql_connection(insert_data["hostname"], insert_data["database_name"], insert_data["username"], insert_data["password"]):
						data_permission_message = "Database PostgreSQL yang diberikan tidak bisa Terkoneksi"
						return HttpResponse(data_permission_message)
				else:
					dashboard_insert.dashboard_tipe_data = 2 #tipe database MySQL
					if not check_databases_mysql_connection(insert_data["hostname"], insert_data["database_name"], insert_data["username"], insert_data["password"]):
						data_permission_message = "Database MySQL yang diberikan tidak bisa Terkoneksi"
						return HttpResponse(data_permission_message)
				dashboard_insert.dashboard_owner_id = request.user
				dashboard_insert.dashboard_name = insert_data["dashboard_name"]
				dashboard_insert.dashboard_database_address = insert_data["hostname"]
				dashboard_insert.dashboard_database_username = insert_data["username"]
				dashboard_insert.dashboard_database_password = insert_data["password"]
				dashboard_insert.dashboard_database_name = insert_data["database_name"]
				dashboard_insert.dashboard_state = 1
				dashboard_insert.dashboard_ready = 0
				dashboard_insert.dashboard_next_check_connection = 0
				dashboard_insert.dashboard_list_count_current_row_tabels = 0
				#https://stackoverflow.com/questions/12615154/how-to-get-the-currently-logged-in-users-user-id-in-django
				current_user = request.user
				#https://stackoverflow.com/questions/7585307/how-to-correct-typeerror-unicode-objects-must-be-encoded-before-hashing
				current_key = str(str(current_user.id) + str(time.time())).encode('utf-8')
				hasil_hash = hashlib.md5(current_key).hexdigest()
				dashboard_insert.dashboard_kode = hasil_hash
				dashboard_insert.save()
				data_permission_message = "Berhasil"
				#get logged user id request.user.id 
				return HttpResponse(data_permission_message)
			else:
				if "file_receiver" not in request.FILES:
					data_permission_message = "File harus di dipilih"
					return HttpResponse(data_permission_message)
				current_user = request.user
				current_key = str(str(current_user.id) + str(time.time())).encode('utf-8')
				hasil_hash = hashlib.md5(current_key).hexdigest()
				handle_uploaded_file(request.FILES['file_receiver'], hasil_hash)
				dashboard_insert = dashboard()
				dashboard_insert.dashboard_owner_id = request.user
				dashboard_insert.dashboard_name = insert_data["dashboard_name"]
				dashboard_insert.dashboard_tipe_data = 3 #tipe CSV
				dashboard_insert.dashboard_state = 1
				dashboard_insert.dashboard_ready = 0
				dashboard_insert.dashboard_next_check_connection = 0
				dashboard_insert.dashboard_list_count_current_row_tabels = 0
				dashboard_insert.dashboard_kode = hasil_hash
				dashboard_insert.dashboard_excel_path = str(pathlib.Path().absolute()) + "/templates/data_csv/" + hasil_hash + ".csv"
				dashboard_insert.save()
				data_permission_message = "Berhasil"
				return HttpResponse(data_permission_message)
			#get logged user id request.user.id 
			return HttpResponse(data_permission_message)
		else:
			return HttpResponse("It's Forbidden to try connect Here :)")
	return HttpResponse("It's Forbidden to try connect Here :)")
		
def handle_uploaded_file(f, this_kode_dashboard):
	file_path = str(pathlib.Path().absolute()) + "/templates/data_csv/" + this_kode_dashboard + ".csv"
	with open(file_path, 'wb+') as destination:
		for chunk in f.chunks():
			destination.write(chunk)
			

def relation_dashboard(request, this_dashboard_kode):
	if request.is_secure():
		context["base_http"] = 'https'
	if not check_connection(request):
		return HttpResponseRedirect(str(context["base_http"]) + str(request.get_host()))
	data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=this_dashboard_kode).exclude(dashboard_disabled=1)[0:1]
	if len(data_dashboard) != 1:
		temp_redirect = str(context["base_http"]) + str(request.get_host()) + "/backend"
		return HttpResponseRedirect(temp_redirect)
	context["data_dashboard"] = data_dashboard
	context["kode_dashboard"] = this_dashboard_kode
	context["data_table"] = {}
	for data in data_dashboard:
		context["data_table"] = json.loads(data.dashboard_list_tabels)
	
	# for index1, data1 in context["data_table"].items():
		# for index2, data2 in data1["list_column"].items():
			#checkpoint
			# if ""
	
	# print(context["data_table"])
	#cek index tabel
	# for table in context["data_table"]:
		# print(table[0])
	template = loader.get_template('backend/edit_relations.html')
	return HttpResponse(template.render(context, request))
	
def relation_dashboard_others_column(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			kode_dashboard = request.POST['kode_dashboard_sending']
			data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=kode_dashboard).exclude(dashboard_disabled=1)[0:1]
			if len(data_dashboard) != 1:
				return HttpResponse("No Dashboard Selected")
			context["data_dashboard"] = data_dashboard
			context["id_tabel"] = request.POST['id_tabel']
			context["id_column"] = request.POST['id_column']
			context["target_tabel"] = request.POST['target_id_tabel']
			context["data_table"] = {}
			for data in data_dashboard:
				context["data_table"] = json.loads(data.dashboard_list_tabels)
			template = loader.get_template('backend/show_select_list_others_column.html')
			return HttpResponse(template.render(context, request))

def container_design_dashboard(request, this_dashboard_kode):
	if request.is_secure():
		context["base_http"] = 'https'
	if not check_connection(request):
		return HttpResponseRedirect(str(context["base_http"]) + str(request.get_host()))
	data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=this_dashboard_kode, dashboard_state__gt=50).exclude(dashboard_disabled=1)[0:1]
	if len(data_dashboard) != 1:
		temp_redirect = str(context["base_http"]) + str(request.get_host()) + "/backend"
		return HttpResponseRedirect(temp_redirect)
	for data in data_dashboard:
		context["data_dashboard"] = data
	context["kode_dashboard"] = this_dashboard_kode
	template = loader.get_template('backend/edit_design.html')
	return HttpResponse(template.render(context, request))
	
def relation_dashboard_processing(request, this_dashboard_kode):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=this_dashboard_kode).exclude(dashboard_disabled=1)[0:1]
			if len(data_dashboard) != 1:
				return HttpResponse("Tidak Terdaftar")
			context["data_table"] = {}
			for data in data_dashboard:
				type_dashboard = data.dashboard_tipe_data
				context["data_table"] = json.loads(data.dashboard_list_tabels)
			list_split = []
			list_tabel_feeding = ""
			for key_text in request.POST:
				# print(key_text, request.POST[key_text])
				list_split = str(key_text).split("_")
				if (list_split[0] == "table"):
					set_tabel_active(list_split[1])
					if (list_tabel_feeding == ""):
						list_tabel_feeding = str(list_split[1])
						# list_tabel_feeding = context["data_table"][str(list_split[1])]["nama_tabel"]
					else:	
						list_tabel_feeding = list_tabel_feeding + "," + str(list_split[1])
						# data_dashboard.dashboard_list_count_tabels
				elif (list_split[0] == "isprimarykey") and (request.POST[key_text] == "Y"):
					set_primary_tabel(list_split[1], list_split[2])
				elif (list_split[0] == "type"):
					set_type(list_split[2],list_split[3], request.POST[key_text])
				elif (list_split[0] == "relations"):
					# print("-------")
					set_relations_tabel(list_split[1],list_split[2],list_split[3],request.POST[key_text])
			if type_dashboard == 3:
				list_tabel_feeding = "0"
			temporary_dump = json.dumps(context["data_table"], indent=4)
			dashboard.objects.select_related().filter(dashboard_kode = this_dashboard_kode, dashboard_state=2).update(dashboard_list_tabels=temporary_dump, dashboard_state=50, dashboard_list_count_tabels=list_tabel_feeding, dashboard_list_count_current_row_tabels=1)
			return HttpResponse("Berhasil")

def view_dashboard_generated_container(request, this_dashboard_kode):
	if request.user.is_authenticated:
		list_data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=this_dashboard_kode, dashboard_state=100).exclude(dashboard_disabled=1)[0:1]
		if len(list_data_dashboard) != 1:
			return HttpResponse("")
		temporary = 0
		temporary_user = 0
		for data in list_data_dashboard:
			temporary = data.dashboard_date_update_design
			temporary_user = data.dashboard_date_update
		context["last_user_update"] = datetime.utcfromtimestamp(temporary_user).strftime('%d-%m-%Y %H:%M:%S')
		context["last_design_update"] = datetime.utcfromtimestamp(temporary).strftime('%d-%m-%Y %H:%M:%S')
		context["kode_dashboard"] = this_dashboard_kode
		try:
			template = loader.get_template('backend/container_preview.html')
			return HttpResponse(template.render(context, request))
		except ValueError:
			return HttpResponse("")
	else:
		return HttpResponse("")
		
#menampilkan sementara hasil dashboard pada iframe
def view_dashboard_generated(request, this_dashboard_kode):
	if request.user.is_authenticated:
		data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=this_dashboard_kode, dashboard_state=100).exclude(dashboard_disabled=1)[0:1]
		if len(data_dashboard) != 1:
			return HttpResponse("")
		try:
			template = loader.get_template('generated/' + this_dashboard_kode + '.html')
			return HttpResponse(template.render(context, request))
		except ValueError:
			return HttpResponse("")
	else:
		return HttpResponse("")

#menampilkan design dalam template
def generate_design_dashboard(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			this_kode_dashboard = request.POST['kode_dashboard_sending']
			data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=this_kode_dashboard, dashboard_state__gt=50).exclude(dashboard_disabled=1)[0:1]
			if len(data_dashboard) != 1:
				return HttpResponse("")
			for data in data_dashboard:
				context["data_design"] = json.loads(data.dashboard_design_json)
			template = loader.get_template('backend/design_input.html')
			return HttpResponse(template.render(context, request))
			
#Take Input design slide add row
def generate_design_dashboard_add_input(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			this_kode_dashboard = request.POST['kode_dashboard_sending']
			data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=this_kode_dashboard, dashboard_state__gt=50).exclude(dashboard_disabled=1)[0:1]
			if len(data_dashboard) != 1:
				return HttpResponse("")
			template = loader.get_template('backend/design_input_new_row.html')
			return HttpResponse(template.render(context, request))

#menampilkan template-template apa saja yang ada
def generate_design_dashboard_template(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			this_kode_dashboard = request.POST['kode_dashboard_sending']
			context["row_selected"] = request.POST['current_row']
			context["col_selected"] = request.POST['current_col']
			data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=this_kode_dashboard, dashboard_state__gt=50).exclude(dashboard_disabled=1)[0:1]
			if len(data_dashboard) != 1:
				return HttpResponse("")
			template = loader.get_template('backend/design_input_template.html')
			return HttpResponse(template.render(context, request))

#menampilkan owlcarousel untuk edit template
def generate_design_dashboard_edit_template(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			this_kode_dashboard = request.POST['kode_dashboard_sending']
			context['row_selected'] = request.POST['current_row']
			context['col_selected'] = request.POST['current_col']
			data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=this_kode_dashboard, dashboard_state__gt=50).exclude(dashboard_disabled=1)[0:1]
			if len(data_dashboard) != 1:
				return HttpResponse("")
			template = loader.get_template('backend/design_edit_template.html')
			return HttpResponse(template.render(context, request))


#menampilkan inputan modal buat template terisi
def show_template_modal(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			context["kode_dashboard"] = request.POST['kode_dashboard_sending']
			context["row_selected"] = request.POST['current_row']
			context["col_selected"] = request.POST['current_col']
			context["tipe_template"] = str(request.POST['tipe_template'])
			context["list_tabel"] = {}
			context["list_column"] = {} #menampung list data column pada tabel pertama
			count_list_tabel = 0
			count_list_column = 0
			data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=context["kode_dashboard"], dashboard_state__gt=50).exclude(dashboard_disabled=1)[0:1]
			if len(data_dashboard) != 1:
				return HttpResponse("")
			data_list_tabel = {}
			for data in data_dashboard:
				data_list_tabel = json.loads(data.dashboard_list_relation_data)
			for index, data in data_list_tabel.items():
				context["list_tabel"][count_list_tabel] = {}
				context["list_tabel"][count_list_tabel]["id_tabel"] = data["id_tabel"]
				context["list_tabel"][count_list_tabel]["nama_tabel"] = data["nama_tabel"]
				if (index == "0"):
					for index2, data2 in data["list_tabel_feeding"].items():
						context["list_column"][count_list_column] = {}
						context["list_column"][count_list_column]["id"] = index2
						context["list_column"][count_list_column]["nama_column"] = data2["column_name_show"]
						count_list_column += 1
				count_list_tabel += 1
			print(context["tipe_template"])
			if (context["tipe_template"] == "1"):
				template = loader.get_template('backend/template_design/template_1.html')
				return HttpResponse(template.render(context, request))
			elif (context["tipe_template"] == "2"):
				template = loader.get_template('backend/template_design/template_2.html')
				return HttpResponse(template.render(context, request))
			elif (context["tipe_template"] == "3"):
				template = loader.get_template('backend/template_design/template_3.html')
				return HttpResponse(template.render(context, request))
			elif (context["tipe_template"] == "4"):
				template = loader.get_template('backend/template_design/template_4.html')
				return HttpResponse(template.render(context, request))
			elif (context["tipe_template"] == "5"):
				template = loader.get_template('backend/template_design/template_5.html')
				return HttpResponse(template.render(context, request))
			elif (context["tipe_template"] == "6"):
				template = loader.get_template('backend/template_design/template_6.html')
				return HttpResponse(template.render(context, request))
			elif (context["tipe_template"] == "7"):
				template = loader.get_template('backend/template_design/template_7.html')
				return HttpResponse(template.render(context, request))
			elif (context["tipe_template"] == "8"):
				template = loader.get_template('backend/template_design/template_8.html')
				return HttpResponse(template.render(context, request))
			elif (context["tipe_template"] == "9"):
				template = loader.get_template('backend/template_design/template_9.html')
				return HttpResponse(template.render(context, request))
			elif (context["tipe_template"] == "10"):
				template = loader.get_template('backend/template_design/template_10.html')
				return HttpResponse(template.render(context, request))
			elif (context["tipe_template"] == "11"):
				template = loader.get_template('backend/template_design/template_11.html')
				return HttpResponse(template.render(context, request))
			elif (context["tipe_template"] == "12"):
				template = loader.get_template('backend/template_design/template_12.html')
				return HttpResponse(template.render(context, request))
			elif (context["tipe_template"] == "13"):
				template = loader.get_template('backend/template_design/template_13.html')
				return HttpResponse(template.render(context, request))
			elif (context["tipe_template"] == "14"):
				template = loader.get_template('backend/template_design/template_14.html')
				return HttpResponse(template.render(context, request))
			elif (context["tipe_template"] == "15"):
				template = loader.get_template('backend/template_design/template_15.html')
				return HttpResponse(template.render(context, request))
			return HttpResponse("")

#untuk menampilkan list-list data column yang ada
def send_list_column(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			context["kode_dashboard"] = request.POST['kode_dashboard_sending']
			context["id_tabel"] = str(request.POST['target_id_tabel'])
			context["list_column"] = {}
			count_list_column = 0
			data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=context["kode_dashboard"], dashboard_state__gt=50).exclude(dashboard_disabled=1)[0:1]
			if len(data_dashboard) != 1:
				return HttpResponse("")
			for data in data_dashboard:
				data_list_tabel = json.loads(data.dashboard_list_relation_data)
			for index, data in data_list_tabel.items():
				if (data["id_tabel"] == context["id_tabel"]):
					for index2, data2 in data["list_tabel_feeding"].items():
						context["list_column"][count_list_column] = {}
						context["list_column"][count_list_column]["id"] = index2
						context["list_column"][count_list_column]["nama_column"] = data2["column_name_show"]
						count_list_column += 1
			template = loader.get_template('backend/template_design/show_others_column.html')
			return HttpResponse(template.render(context, request))
		
def process_template(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			kode_dashboard = request.POST['kode_dashboard']
			tipe_template = str(request.POST['tipe_template'])
			row_selected = str(request.POST['row_selected'])
			col_selected = str(request.POST['col_selected'])
			data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=kode_dashboard, dashboard_state__gt=50).exclude(dashboard_disabled=1)[0:1]
			if len(data_dashboard) != 1:
				return HttpResponse("")
			update_last_update(kode_dashboard)
			data_design = {}
			data_list_tabel = {}
			for data in data_dashboard:
				data_list_tabel = json.loads(data.dashboard_list_relation_data)
				data_design = json.loads(data.dashboard_design_json)
			current_user = request.user
			current_key = str(str(current_user.id) + str(time.time()) + row_selected + col_selected).encode('utf-8')
			hasil_hash = hashlib.md5(current_key).hexdigest()
			data_design[row_selected][col_selected]["kode_template"] = hasil_hash
			data_border = {}
			data_border["left"] = ""
			data_border["top"] = ""
			data_border["right"] = ""
			data_border["bottom"] = ""
			data_setting = {}
			list_where = {}
			data_design[row_selected][col_selected]["already_processed"] = 0
			data_design[row_selected][col_selected]["data_processed"] = {}
			data_design[row_selected][col_selected]["additional_script_windows_already_loaded"] = ""
			if "add_border" in request.POST:
				data_design[row_selected][col_selected]["add_border"] = 1
				if "border_left" in request.POST:
					data_border["left"] = "border-left"
				if "border_top" in request.POST:
					data_border["top"] = "border-top"
				if "border_right" in request.POST:
					data_border["right"] = "border-right"
				if "border_bottom" in request.POST:
					data_border["bottom"] = "border-bottom"
			data_design[row_selected][col_selected]["data_border"] = data_border
			temporary_string_class_border = ""
			for index, data in data_border.items():
				if data != "":
					if temporary_string_class_border == "":
						temporary_string_class_border = data
					else:
						temporary_string_class_border = temporary_string_class_border + " " + data
			data_design[row_selected][col_selected]["data_border_string"] = temporary_string_class_border
			if (tipe_template == "1"):
				data_design[row_selected][col_selected]["tipe"] = tipe_template
				data_setting["include_text"] = 0
				data_setting["include_data"] = 0
				data_setting["input_text"] = ""
				if "include_text" in request.POST: #user menselect text untuk ditampilkan
					data_setting["include_text"] = 1
					if "input_text" in request.POST:
						data_setting["input_text"] = request.POST['input_text']
				if "include_data" in request.POST:
					data_setting["include_data"] = 1
					data_setting["append_data_before"] = ""
					data_setting["id_selected_tabel"] = request.POST["source_data"]
					data_setting["id_selected_column"] = request.POST["column_data"]
					data_setting["mode_calculation"] = request.POST["tipe_calculation_data"]
					if "append_data_before" in request.POST:
						data_setting["append_data_before"] = request.POST["append_data_before"]
			else:
				data_design[row_selected][col_selected]["tipe"] = tipe_template
				data_setting["include_text"] = 0
				data_setting["input_text"] = ""
				data_setting["include_data"] = 1
				data_setting["include_legend"] = 0
				data_setting["id_selected_tabel"] = request.POST["source_data"]
				data_setting["id_selected_column_header"] = request.POST['column_header']
				data_setting["id_selected_column"] = request.POST['column_data']
				data_setting["mode_calculation"] = request.POST["tipe_calculation_data"]
				data_setting["make_lower_ranking_others"] = 0
				if ("include_legend" in request.POST):
					data_setting["include_legend"] = 1
				if "include_text" in request.POST: #user menselect text untuk ditampilkan
					data_setting["include_text"] = 1
					if "input_text" in request.POST:
						data_setting["input_text"] = request.POST['input_text']
				if (data_setting["id_selected_column_header"] == data_setting["id_selected_column"]):
					return HttpResponse("Kolom Header dan Kolom Data tidak boleh sama");
				#begin Process each pertype template
				if (tipe_template == "2") or (tipe_template == "5") or (tipe_template == "7") or (tipe_template == "9") or (tipe_template == "11"):
					if ("include_others" in request.POST):
						data_setting["make_lower_ranking_others"] = 1
						data_setting["minimum_make_lower_ranking_others"] = 1
						minimum_others = int(request.POST["minimum_others"])
						if (minimum_others > 1):
							data_setting["minimum_make_lower_ranking_others"] = minimum_others
					#for datatables
					data_setting["header_name"] = 1
					data_setting["value_name"] = 1
					if "header_name" in request.POST:
						data_setting["header_name"] = request.POST["header_name"]
					if "value_name" in request.POST:
						data_setting["value_name"] = request.POST["value_name"]
				elif (tipe_template == "6") or (tipe_template == "4") or (tipe_template == "15"):
					data_setting["sort_header"] = 1 #untuk ASC
					if "header_sort" in request.POST:
						if request.POST["header_sort"] == "desc":
							data_setting["sort_header"] = -1
					if (tipe_template == "15"):
						data_setting["is_filled"] = 1
						data_setting["is_line_straight"] = 1
						if "tipe_filled" in request.POST:
							if request.POST["tipe_filled"] == "n":
								data_setting["is_filled"] = 0
						if "tipe_line" in request.POST:
							if request.POST["tipe_line"] == "smooth":
								data_setting["is_line_straight"] = 0
						# temporary_dump = json.dumps(data_design, indent=4)
						# print(temporary_dump)
				elif (tipe_template == "3") or (tipe_template == "8"):
					data_setting["sort_header"] = 0 #untuk ASC
					if "header_sort" in request.POST:
						if request.POST["header_sort"] == "asc":
							data_setting["sort_header"] = 1
						elif request.POST["header_sort"] == "desc":
							data_setting["sort_header"] = -1
				elif (tipe_template == "10") or (tipe_template == "12") or (tipe_template == "13") or (tipe_template == "14"):
					if (tipe_template == "12") or (tipe_template == "14"):
						data_setting["is_filled"] = 1
						data_setting["is_line_straight"] = 1
						if "tipe_filled" in request.POST:
							if request.POST["tipe_filled"] == "n":
								data_setting["is_filled"] = 0
						if "tipe_line" in request.POST:
							if request.POST["tipe_line"] == "smooth":
								data_setting["is_line_straight"] = 0
					data_setting["id_selected_column_dataset"] = request.POST['column_dataset']
					if (data_setting["id_selected_column_dataset"] == data_setting["id_selected_column_header"]):
						return HttpResponse("Kolom Dataset dan Kolom Header tidak boleh sama");
					if (data_setting["id_selected_column_dataset"] == data_setting["id_selected_column"]):
						return HttpResponse("Kolom Dataset dan Kolom Data tidak boleh sama");
					data_setting["sort_dataset"] = 0 #untuk ASC
					data_setting["tipe_stack"] = 0 #for sum others as pembanding
					if "stack_type" in request.POST:
						if request.POST["stack_type"] == "separated":
							data_setting["tipe_stack"] = 1 #for separated
					if "dataset_sort" in request.POST:
						if request.POST["dataset_sort"] == "asc":
							data_setting["sort_dataset"] = 1
						elif request.POST["dataset_sort"] == "desc":
							data_setting["sort_dataset"] = -1
					data_setting["sort_header"] = 0 #untuk ASC
					if "header_sort" in request.POST:
						if request.POST["header_sort"] == "asc":
							data_setting["sort_header"] = 1
						elif request.POST["header_sort"] == "desc":
							data_setting["sort_header"] = -1
					data_setting["sort_data"] = 0 #untuk ASC
					if "data_sort" in request.POST:
						if request.POST["data_sort"] == "asc":
							data_setting["sort_data"] = 1
						elif request.POST["data_sort"] == "desc":
							data_setting["sort_data"] = -1
			#inisialisasi where
			data_setting["include_where"] = 0
			if "include_where" in request.POST:
				data_setting["include_where"] = 1
			data_design[row_selected][col_selected]["data_setting"] = data_setting
			#process Where
			if (data_setting["include_where"] == 1) and (data_setting["include_data"] == 1):
				temporary_split = []
				for index, data in request.POST.items():
					temporary_split = str(index).split("_")
					if temporary_split[0] == "selectwhereidcol":
						if temporary_split[1] not in list_where:
							list_where[temporary_split[1]] = {}
							list_where[temporary_split[1]]["selected_column"] = ""
						list_where[temporary_split[1]]["selected_column"] = data
						list_where[temporary_split[1]]["selected_column_name"] = get_target_column_in_collection(data_list_tabel, data_setting["id_selected_tabel"], data)
					elif temporary_split[0] == "optionwhere":
						if temporary_split[1] not in list_where:
							list_where[temporary_split[1]] = {}
						list_where[temporary_split[1]]["optionwhere"] = data
					elif temporary_split[0] == "characterfilter":
						if temporary_split[1] not in list_where:
							list_where[temporary_split[1]] = {}
						list_where[temporary_split[1]]["characterfilter"] = data
			data_where = {}
			count_data_where = 0
			for index, data in list_where.items():
				if (("selected_column" in data) and ("optionwhere" in data) and ("characterfilter" in data)):
					data_where[count_data_where] = data
					count_data_where += 1
			data_design[row_selected][col_selected]["data_where"] = data_where
			temporary_dump = json.dumps(data_design, indent=4)
			dashboard.objects.select_related().filter(dashboard_kode = kode_dashboard).update(dashboard_design_json=temporary_dump)
			# data_hasil_pipeline = get_data_group_none(list_where, data_setting["id_selected_tabel"], data_setting["id_selected_column"], data_list_tabel, data_setting["mode_calculation"])
			# data_hasil_pipeline = get_data_group(list_where, data_setting["id_selected_tabel"], data_setting["id_selected_column"], data_list_tabel, data_setting["mode_calculation"], 1, 1, 1)
			# for data in data_hasil_pipeline:
				# print(data)
				
			# temporary_dump1 = json.dumps(data_design, indent=4)
			# print(temporary_dump1)
			# return HttpResponse("Testing");
			return HttpResponse("Berhasil");

def get_data_double_group(data_where, id_tabel, id_column, data_relations, calculation, grouped_column, additional_group, data_group = 0, dataset_group = 0, header_data_group = 0): #sort 1 = ASC -1 = DESC, 0 no sort
	# untuk data datatable https://stackoverflow.com/questions/16662405/mongo-group-query-how-to-keep-fields tidak bisa count
	myclient = MongoClient(mongo_db_address)
	mydb = myclient[database_setting]
	print ("target_pipeline : " + get_target_collection(data_relations, id_tabel))
	my_collection = mydb[get_target_collection(data_relations, id_tabel)]
	query = []
	query.append(generate_pipeline_project(data_where, id_tabel, id_column, data_relations, grouped_column, additional_group))
	if (len(data_where) > 0):
		query.append(generate_pipeline_match(data_where, data_relations, id_tabel))
	query.append(generate_pipeline_group(id_tabel, id_column, data_relations, calculation, grouped_column, additional_group))
	dict_sort = {}
	if (data_group + dataset_group + header_data_group) != 0:
		dict_sort["$sort"] = {}
		if (dataset_group != 0):
			dict_sort["$sort"]["_id._id"] = dataset_group
		if (header_data_group != 0):
			dict_sort["$sort"]["_id.additional"] = header_data_group
		if (data_group != 0):
			dict_sort["$sort"]["total"] = data_group
		query.append(dict_sort)
	print("pipeline:")
	print(query)
	print("----------------")
	return my_collection.aggregate(query)

def get_data_group(data_where, id_tabel, id_column, data_relations, calculation, grouped_column, is_sort_active, tipe_sort = 1, sort = 1): #tipe_sort = 1 value pembanding sisanya hasil value, sort 1 = ASC -1 = DESC
	# untuk data datatable https://stackoverflow.com/questions/16662405/mongo-group-query-how-to-keep-fields tidak bisa count
	myclient = MongoClient(mongo_db_address)
	mydb = myclient[database_setting]
	print ("target_pipeline : " + get_target_collection(data_relations, id_tabel))
	my_collection = mydb[get_target_collection(data_relations, id_tabel)]
	
	query = []
	#untuk langsung sum https://stackoverflow.com/questions/26465846/mongodb-aggregate-group-sum-query-translated-to-pymongo-query
	#multiple group by https://stackoverflow.com/questions/22932364/mongodb-group-values-by-multiple-fields
	query.append(generate_pipeline_project(data_where, id_tabel, id_column, data_relations, grouped_column))
	if (len(data_where) > 0):
		query.append(generate_pipeline_match(data_where, data_relations, id_tabel))
	query.append(generate_pipeline_group(id_tabel, id_column, data_relations, calculation, grouped_column))
	#https://docs.mongodb.com/manual/reference/operator/aggregation/sort/
	dict_sort = {}
	if (is_sort_active):
		dict_sort["$sort"] = {}
		if (tipe_sort == 1): #non calculated value
			dict_sort["$sort"]["_id"] = sort
		else:
			dict_sort["$sort"]["total"] = sort
		query.append(dict_sort)
	print("pipeline:")
	print(query)
	print("----------------")
	return my_collection.aggregate(query)
	
def get_data_group_none(data_where, id_tabel, id_column, data_relations, calculation):
	myclient = MongoClient(mongo_db_address)
	mydb = myclient[database_setting]
	my_collection = mydb[get_target_collection(data_relations, id_tabel)]
	print ("target_pipeline : " + get_target_collection(data_relations, id_tabel))
	query = []
	query.append(generate_pipeline_project(data_where, id_tabel, id_column, data_relations))
	if (len(data_where) > 0):
		query.append(generate_pipeline_match(data_where, data_relations, id_tabel))
	query.append(generate_pipeline_group(id_tabel, id_column, data_relations, calculation))
	print("pipeline:")
	print(query)
	print("----------------")
	return my_collection.aggregate(query)

def generate_pipeline_project(data_where, id_tabel, id_column, data_relations, grouped_column = -1, additional_group = -1):
	target_column = get_target_column_in_collection(data_relations, id_tabel, id_column)
	dict_project = {}
	dict_project["_id"] = 0
	dict_project[target_column] = 1
	if (grouped_column != -1):
		target_column = get_target_column_in_collection(data_relations, id_tabel, grouped_column)
		dict_project[target_column] = 1
	if (additional_group != -1):
		target_column = get_target_column_in_collection(data_relations, id_tabel, additional_group)
		dict_project[target_column] = 1
	for index, data in data_where.items():
		dict_project[data["selected_column_name"]] = 1
	data_return = {}
	data_return["$project"] = dict_project
	return data_return
	
def generate_pipeline_match(data_where, data_relations, id_tabel):
	dict_match = {}
	dict_match["$match"] = {}
	hasil_where = generate_where_for_aggregate(data_where, data_relations, id_tabel)
	if (len(hasil_where) > 1):
		dict_match["$match"]["$and"] = hasil_where
	else:
		dict_match["$match"] = hasil_where
	return dict_match

def generate_pipeline_group(id_tabel, id_column, data_relations, calculation, grouped_column = -1, additional_group = -1):
	target_column = get_target_column_in_collection(data_relations, id_tabel, id_column)
	dict_mode = {}
	dict_mode["$group"] = {}
	if (grouped_column != -1):
		if (additional_group != -1):
			dict_mode["$group"]["_id"] = {}
			dict_mode["$group"]["_id"]["_id"] = "$" + get_target_column_in_collection(data_relations, id_tabel, grouped_column)
			dict_mode["$group"]["_id"]["additional"] = "$" + get_target_column_in_collection(data_relations, id_tabel, additional_group)
		else:
			dict_mode["$group"]["_id"] = "$" + get_target_column_in_collection(data_relations, id_tabel, grouped_column)
	else:
		dict_mode["$group"]["_id"] = ""
	if (calculation != "count"):
		dict_mode["$group"]["total"] = {}
		dict_mode["$group"]["total"]["$" + str(calculation)] = "$" + target_column
	else:
		dict_mode["$group"]["total"] = {}
		dict_mode["$group"]["total"]["$" + "sum"] = 1
	return dict_mode
			
def get_target_collection(this_data_relation, this_target_id_tabel):
	target_id_tabel = str(this_target_id_tabel)
	for index, data in this_data_relation.items():
		# print(index)
		if (data["id_tabel"] == target_id_tabel):
			return str(data["mongo_db_collection_name"]);
	return ""
	
def get_target_column_in_collection(this_data_relation, this_target_id_tabel, this_target_id_column):
	target_id_tabel = str(this_target_id_tabel)
	# return this_data_relation[str(target_id_tabel)][str(this_target_id_column)]["column_name_tabel_data"]
	for index, data in this_data_relation.items():
		if (data["id_tabel"] == target_id_tabel):
			target_id_column = str(this_target_id_column)
			return str(data["list_tabel_feeding"][target_id_column]["column_name_tabel_data"])
					
def generate_where_for_aggregate(this_data_where, data_relations, id_tabel):
	generate_data_regex = {}
	generate_data_where_non_regex = {}
	size_regex = 0
	data_regex = ""
	processed_filter = ""
	processed_data = ""
	add_new_column_filter = True
	non_regex = True
	final = []
	list_type = get_column_type_from_relation(data_relations, str(id_tabel))
	for index, data in this_data_where.items():
		non_regex = True
		add_new_column_filter = True
		#https://stackoverflow.com/questions/20175122/how-can-i-use-not-like-operator-in-mongodb
		if (data["optionwhere"] == "like"):
			non_regex = False
			processed_filter = "$regex"
			processed_data = re.escape(data["characterfilter"])
		elif (data["optionwhere"] == "begin"):
			non_regex = False
			processed_filter = "$regex"
			processed_data = "^" + re.escape(str(data["characterfilter"]))
		elif (data["optionwhere"] == "end"):
			non_regex = False
			processed_filter = "$regex"
			processed_data = re.escape(str(data["characterfilter"])) + "$"
		elif (data["optionwhere"] == "not_like"):
			non_regex = False
			processed_filter = "$regex"
			processed_data = "^((?!" + re.escape(str(data["characterfilter"])) + ").)*$"
		#https://docs.mongodb.com/manual/meta/aggregation-quick-reference/#aggregation-expressions
		else:
			processed_filter = "$" + str(data["optionwhere"])
			# print()
			# print(str(data["selected_column_name"]) + " type : " + str(list_type[int(data["selected_column"])]))
			if (list_type[int(data["selected_column"])] == 0):
				processed_data = str(data["characterfilter"])
			else:
				try:
					processed_data = int(data["characterfilter"])
				except ValueError:
					processed_data = str(data["characterfilter"])
			
		if (non_regex):
			for index1,data1 in generate_data_where_non_regex.items():
				if (data["selected_column_name"] == index1):
					add_new_column_filter = False
			if (add_new_column_filter):
				generate_data_where_non_regex[data["selected_column_name"]] = {}
			generate_data_where_non_regex[data["selected_column_name"]][processed_filter] = processed_data
		else:
			size = len(generate_data_regex)
			generate_data_regex[size] = {}
			generate_data_regex[size][data["selected_column_name"]] = {}
			generate_data_regex[size][data["selected_column_name"]][processed_filter] = processed_data
			generate_data_regex[size][data["selected_column_name"]]["$options"] = "i"
	
	
	temporary_dict = {}
	for index, data in generate_data_where_non_regex.items():
		temporary_dict = {}
		temporary_dict[index] = data
		final.append(temporary_dict)
	for index, data in generate_data_regex.items():
		temporary_dict = {}
		temporary_dict[index] = data
		final.append(data)
		
	if len(final) > 1:
		return final
	else:
		for data in final:
			return data
			
#reset selected template to 0
def generate_design_dashboard_reset_template(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			this_kode_dashboard = request.POST['kode_dashboard_sending']
			current_row = request.POST['current_row']
			current_col = request.POST['current_col']
			data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=this_kode_dashboard, dashboard_state__gt=50).exclude(dashboard_disabled=1)[0:1]
			if len(data_dashboard) != 1:
				return HttpResponse("")
			for data in data_dashboard:
				data_design = json.loads(data.dashboard_design_json)
			data_design[current_row][current_col]["tipe"] = 0
			data_design[current_row][current_col]["include_text"] = 0
			data_design[current_row][current_col]["input_text"] = ""
			data_design[current_row][current_col]["already_processed"] = 0
			data_design[current_row][current_col]["data_processed"] = {}
			data_design[current_row][current_col]["additional_script_windows_already_loaded"] = ""
			data_design[current_row][current_col]["data_border_string"] = ""
			temporary_dump = json.dumps(data_design, indent=4)
			dashboard.objects.select_related().filter(dashboard_kode = this_kode_dashboard).update(dashboard_design_json=temporary_dump)
			generate_template(this_kode_dashboard)
			return HttpResponse("")

#Menambahkan Row
def generate_design_dashboard_add_row(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			this_kode_dashboard = request.POST['kode_dashboard_sending']
			total_column = int(request.POST['many_column'])
			data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=this_kode_dashboard, dashboard_state__gt=50).exclude(dashboard_disabled=1)[0:1]
			if len(data_dashboard) != 1:
				return HttpResponse("")
			for data in data_dashboard:
				data_design = json.loads(data.dashboard_design_json)
			total_row = len(data_design)
			data_dict = {}
			size_col = 1
			if (total_column > 0):
				size_col = int(12 / total_column)
			for x in range(total_column):
				data_dict[x] = {}
				data_dict[x]["tipe"] = 0
				data_dict[x]["kode_template"] = ""
				data_dict[x]["tipe_col"] = "col-" + str(size_col)
				data_dict[x]["add_border"] = 0
				data_dict[x]["already_processed"] = 0
				data_dict[x]["data_processed"] = {}
				data_dict[x]["additional_script_windows_already_loaded"] = ""
			if (len(data_dict) > 0):
				data_design[total_row] = data_dict
			temporary_dump = json.dumps(data_design, indent=4)
			dashboard.objects.select_related().filter(dashboard_kode = this_kode_dashboard).update(dashboard_design_json=temporary_dump)
			update_last_update(this_kode_dashboard)
			return HttpResponse("")
		
#generate row untuk filter where
def generate_row_filter_where(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			context["kode_dashboard"] = request.POST['kode_dashboard_sending']
			context["id_tabel"] = str(request.POST['selected_id_tabel'])
			context["row_count"] = str(request.POST['count_row'])
			context["list_column"] = {}
			count_list_column = 0
			data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=context["kode_dashboard"], dashboard_state__gt=50).exclude(dashboard_disabled=1)[0:1]
			if len(data_dashboard) != 1:
				return HttpResponse("")
			for data in data_dashboard:
				data_list_tabel = json.loads(data.dashboard_list_relation_data)
			for index, data in data_list_tabel.items():
				if (str(data["id_tabel"]) == context["id_tabel"]):
					for index2, data2 in data["list_tabel_feeding"].items():
						context["list_column"][count_list_column] = {}
						context["list_column"][count_list_column]["id"] = index2
						context["list_column"][count_list_column]["nama_column"] = data2["column_name_show"]
						count_list_column += 1
			template = loader.get_template('backend/template_design/template_filter_where.html')
			return HttpResponse(template.render(context, request))
			
#delete row
def generate_design_dashboard_delete_row(request):
	if request.user.is_authenticated:
		if HttpRequest.is_ajax(request):
			this_kode_dashboard = request.POST['kode_dashboard_sending']
			current_row = str(request.POST['current_row'])
			data_dashboard = dashboard.objects.filter(dashboard_owner_id=request.user,dashboard_kode=this_kode_dashboard, dashboard_state__gt=50).exclude(dashboard_disabled=1)[0:1]
			if len(data_dashboard) != 1:
				return HttpResponse("")
			data_design_temp = {}
			count_data_design_temp = 0
			for data in data_dashboard:
				data_design = json.loads(data.dashboard_design_json)
			
			for index, data in data_design.items():
				if (str(index) != current_row):
					data_design_temp[count_data_design_temp] = data
					count_data_design_temp += 1
			temporary_dump = json.dumps(data_design_temp, indent=4)
			dashboard.objects.select_related().filter(dashboard_kode = this_kode_dashboard).update(dashboard_design_json=temporary_dump)
			update_last_update(this_kode_dashboard)
			return HttpResponse("")

#begin set list function bantuan untuk data relation
def set_tabel_active(id_tabel):
	context["data_table"][str(id_tabel)]["is_selected"] = 1

def set_primary_tabel(id_tabel, id_column):
	context["data_table"][str(id_tabel)]["list_column"][id_column]["is_primary"] = 1
	
def set_relations_tabel(id_tabel, id_column, fk_id_tabel, fk_id_column):
	context["data_table"][str(id_tabel)]["list_column"][id_column]["is_have_parent"] = 1
	context["data_table"][str(id_tabel)]["list_column"][id_column]["parent_tabel_id"] = fk_id_tabel
	context["data_table"][str(id_tabel)]["list_column"][id_column]["parent_tabel_id_column"] = fk_id_column
	
def set_type(id_tabel, id_column, type_column):
	if (type_column == "number"):
		context["data_table"][str(id_tabel)]["list_column"][id_column]["type_data"] = 1
	elif (type_column == "decimal"):
		context["data_table"][str(id_tabel)]["list_column"][id_column]["type_data"] = 2
	else:
		context["data_table"][str(id_tabel)]["list_column"][id_column]["type_data"] = 0
#end set list function bantuan untuk data relation

def update_last_update(this_kode_dashboard_current):
	dashboard.objects.select_related().filter(dashboard_kode = this_kode_dashboard_current).update(dashboard_date_update=time.time())

def update_last_design_update(this_kode_dashboard_current):
	dashboard.objects.select_related().filter(dashboard_kode = this_kode_dashboard_current).update(dashboard_date_update_design=time.time())

def generate_query(data_tabel, id_tabel_processing, page):
	# "__--__" = .
	# --__--" = pemisah nama tabel dengan nama column ex a.b = a--_--b
	limit = limit_data_row_processing
	count_list_tabel = 1
	list_tabel_feed = {}
	list_tabel_feed[0]= {}
	list_tabel_feed[0]["id_tabel"] = id_tabel_processing
	list_tabel_feed[0]["already_feeding"] = 0
	count_select = 0
	select_dict_list = {}
	count_join = 0
	join_dict_list = {}
	count_primary = 0
	list_primary = {}
	nama_tabel = ""
	nama_column = ""
	alias_column = ""
	
	done = False
	id_tabel = 0
	nav_dict_list_tabel = 0
	while(not done):
		done = True
		for key, data in list_tabel_feed.items():
			if (data["already_feeding"] == 0):
				done = False
				nav_dict_list_tabel = key
				id_tabel = list_tabel_feed[key]["id_tabel"]
				continue
		if (not done):
			for key1, value1 in data_tabel[id_tabel]["list_column"].items():
				nama_tabel = '"' + str(data_tabel[id_tabel]["nama_tabel"]) + '"'
				nama_column = '"' + str(value1["nama_column"]) + '"'
				alias_tabel = '"' + str(data_tabel[id_tabel]["nama_tabel"]) + "--__--" + str(value1["nama_column"]) + '"'
				select_dict_list[count_select] = nama_tabel + "." + nama_column + " AS " + alias_tabel
				count_select += 1
				if (value1["is_primary"] == 1) and (id_tabel == id_tabel_processing):
					list_primary[count_primary] = '"' + str(data_tabel[id_tabel]["nama_tabel"]) + '"."' + str(value1["nama_column"]) + '"'
					count_primary += 1
				if (value1["is_have_parent"] == 1):
					list_tabel_feed[count_list_tabel] = {}
					list_tabel_feed[count_list_tabel]["id_tabel"] = value1["parent_tabel_id"]
					list_tabel_feed[count_list_tabel]["already_feeding"] = 0
					count_list_tabel += 1
					join_dict_list[count_join] = {}
					join_dict_list[count_join]["left_tabel"] = '"' + str(data_tabel[id_tabel]["nama_tabel"]) + '"'
					join_dict_list[count_join]["left_column"] = '"' + str(value1["nama_column"]) + '"'
					join_dict_list[count_join]["right_tabel"] = '"' + str(data_tabel[value1["parent_tabel_id"]]["nama_tabel"]) + '"'
					join_dict_list[count_join]["right_column"] = '"' + str(data_tabel[value1["parent_tabel_id"]]["list_column"][value1["parent_tabel_id_column"]]["nama_column"]) + '"'
					count_join += 1
			list_tabel_feed[nav_dict_list_tabel]["already_feeding"] = 1
	select_query = ""
	from_query = ""
	join_query = ""
	order_query = ""
	limit_query = ""
	
	#begin building query
	#selectbuild
	for index, select_data in select_dict_list.items():
		if (index == 0):
			select_query = "SELECT " + select_data
		else:
			select_query = select_query + ", " + select_data
			
	#building from
	nama_tabel = '"' + str(data_tabel[id_tabel_processing]["nama_tabel"]) + '"'
	from_query = " FROM " + nama_tabel + " "
	
	#building Left Join
	temporary_join = ""
	for index, data in join_dict_list.items():
		if (index == 0):
			join_query = "JOIN %s ON %s.%s = %s.%s " % (data["right_tabel"],data["left_tabel"],data["left_column"],data["right_tabel"],data["right_column"])
		else:
			temporary_join = "JOIN %s ON %s.%s = %s.%s " % (data["right_tabel"],data["left_tabel"],data["left_column"],data["right_tabel"],data["right_column"])
			join_query = join_query + temporary_join
	
	#building order
	for index, primary_data in list_primary.items():
		nama_tabel = str(primary_data) + ' ASC '
		if (index == 0):
			order_query = "ORDER BY " + nama_tabel
		else:
			order_query = order_query + ", " + nama_tabel
	#limit
	offset = (page - 1) * limit
	limit_query = "LIMIT %s OFFSET %s" % (str(limit), str(offset))
	query_final = select_query + from_query + join_query + order_query + limit_query
	return query_final
	#end building query
	
def generate_query_mysql(data_tabel, id_tabel_processing, page):
	# "__--__" = .
	# --__--" = pemisah nama tabel dengan nama column ex a.b = a--_--b
	limit = limit_data_row_processing
	count_list_tabel = 1
	list_tabel_feed = {}
	list_tabel_feed[0]= {}
	list_tabel_feed[0]["id_tabel"] = id_tabel_processing
	list_tabel_feed[0]["already_feeding"] = 0
	count_select = 0
	select_dict_list = {}
	count_join = 0
	join_dict_list = {}
	count_primary = 0
	list_primary = {}
	nama_tabel = ""
	nama_column = ""
	alias_column = ""
	
	done = False
	id_tabel = 0
	nav_dict_list_tabel = 0
	while(not done):
		done = True
		for key, data in list_tabel_feed.items():
			if (data["already_feeding"] == 0):
				done = False
				nav_dict_list_tabel = key
				id_tabel = list_tabel_feed[key]["id_tabel"]
				continue
		if (not done):
			for key1, value1 in data_tabel[id_tabel]["list_column"].items():
				nama_tabel = str(data_tabel[id_tabel]["nama_tabel"])
				nama_column = str(value1["nama_column"])
				alias_tabel = "'" + str(data_tabel[id_tabel]["nama_tabel"]) + "--__--" + str(value1["nama_column"]) + "'"
				select_dict_list[count_select] = nama_tabel + "." + nama_column + " AS " + alias_tabel
				count_select += 1
				if (value1["is_primary"] == 1) and (id_tabel == id_tabel_processing):
					list_primary[count_primary] = str(data_tabel[id_tabel]["nama_tabel"]) + '.' + str(value1["nama_column"])
					count_primary += 1
				if (value1["is_have_parent"] == 1):
					list_tabel_feed[count_list_tabel] = {}
					list_tabel_feed[count_list_tabel]["id_tabel"] = value1["parent_tabel_id"]
					list_tabel_feed[count_list_tabel]["already_feeding"] = 0
					count_list_tabel += 1
					join_dict_list[count_join] = {}
					join_dict_list[count_join]["left_tabel"] = str(data_tabel[id_tabel]["nama_tabel"])
					join_dict_list[count_join]["left_column"] = str(value1["nama_column"])
					join_dict_list[count_join]["right_tabel"] = str(data_tabel[value1["parent_tabel_id"]]["nama_tabel"])
					join_dict_list[count_join]["right_column"] = str(data_tabel[value1["parent_tabel_id"]]["list_column"][value1["parent_tabel_id_column"]]["nama_column"])
					count_join += 1
			list_tabel_feed[nav_dict_list_tabel]["already_feeding"] = 1
	select_query = ""
	from_query = ""
	join_query = ""
	order_query = ""
	limit_query = ""
	
	#begin building query
	#selectbuild
	for index, select_data in select_dict_list.items():
		if (index == 0):
			select_query = "SELECT " + select_data
		else:
			select_query = select_query + ", " + select_data
			
	#building from
	nama_tabel = str(data_tabel[id_tabel_processing]["nama_tabel"])
	from_query = " FROM " + nama_tabel + " "
	
	#building Left Join
	temporary_join = ""
	for index, data in join_dict_list.items():
		if (index == 0):
			join_query = "LEFT JOIN %s ON %s.%s = %s.%s " % (data["right_tabel"],data["left_tabel"],data["left_column"],data["right_tabel"],data["right_column"])
		else:
			temporary_join = "LEFT JOIN %s ON %s.%s = %s.%s " % (data["right_tabel"],data["left_tabel"],data["left_column"],data["right_tabel"],data["right_column"])
			join_query = join_query + temporary_join
	
	#building order
	for index, primary_data in list_primary.items():
		nama_tabel = str(primary_data) + ' ASC '
		if (index == 0):
			order_query = "ORDER BY " + nama_tabel
		else:
			order_query = order_query + ", " + nama_tabel
	#limit
	offset = (page - 1) * limit
	limit_query = "LIMIT %s OFFSET %s" % (str(limit), str(offset))
	query_final = select_query + from_query + join_query + order_query + limit_query
	return query_final
	#end building query
	
def build_structural_tabel_query(data_tabel, id_tabel_processing):
	count_list_tabel = 1
	list_tabel_feed = {}
	list_tabel_feed[0]= {}
	list_tabel_feed[0]["id_tabel"] = id_tabel_processing
	list_tabel_feed[0]["already_feeding"] = 0
	count_select = 0
	select_dict_list = {}
	alias_dict_list = {}
	list_primary = {}
	column_type = {}
	count_join = 0
	join_dict_list = {}
	nama_tabel = ""
	nama_column = ""
	alias_column = ""
	
	done = False
	id_tabel = 0
	nav_dict_list_tabel = 0
	while(not done):
		done = True
		for key, data in list_tabel_feed.items():
			if (data["already_feeding"] == 0):
				done = False
				nav_dict_list_tabel = key
				id_tabel = list_tabel_feed[key]["id_tabel"]
				continue
		if (not done):
			for key1, value1 in data_tabel[id_tabel]["list_column"].items():
				nama_tabel = str(data_tabel[id_tabel]["nama_tabel"])
				nama_column = str(value1["nama_column"])
				alias_tabel = str(data_tabel[id_tabel]["nama_tabel"]) + "--__--" + str(value1["nama_column"])
				alias_dict_list[count_select] = alias_tabel
				select_dict_list[count_select] = nama_tabel + "." + nama_column
				if (value1["is_primary"] == 1):
					list_primary[count_select] = 1
				else:
					list_primary[count_select] = 0
				column_type[count_select] = value1["type_data"]
				if (value1["is_have_parent"] == 1):
					list_tabel_feed[count_list_tabel] = {}
					list_tabel_feed[count_list_tabel]["id_tabel"] = value1["parent_tabel_id"]
					list_tabel_feed[count_list_tabel]["already_feeding"] = 0
					count_list_tabel += 1
				count_select += 1
			list_tabel_feed[nav_dict_list_tabel]["already_feeding"] = 1
	dict_return = {}
	for x in range(count_select):
		dict_return[x] = {}
		dict_return[x]["column_name_show"] = select_dict_list[x]
		dict_return[x]["column_name_tabel_data"] = alias_dict_list[x]
		dict_return[x]["is_primary"] = list_primary[x]
		dict_return[x]["column_type"] = column_type[x]
	return dict_return
	
def check_connection(request):
	if request.user.is_authenticated:
		return True
	else:
		return False


def check_databases_postgresql_connection(this_host, this_database, this_user, this_password):
	try:
		conn = psycopg2.connect(
			host = this_host,
			database = this_database,
			user = this_user,
			password = this_password)
		cur = conn.cursor()
		# print('PostgreSQL database version:')
		cur.execute('SELECT version()')
		db_version = cur.fetchone()
		# print(db_version)
		cur.close()
		return True
	except (Exception, psycopg2.DatabaseError) as error:
		print(error)
		return False
		
def check_databases_mysql_connection(this_host, this_database, this_user, this_password):
	try:
		connection = mysql.connector.connect(host=this_host, database=this_database, user=this_user, password=this_password)
		if connection.is_connected():
			return True
	except Error as e:
		return False

def generate_template(this_kode_dashboard):
	list_dashboard = dashboard.objects.filter(dashboard_kode=this_kode_dashboard)[0:1]
	data_dashboard = ""
	for data in list_dashboard:
		data_dashboard = data
		data_design = json.loads(data.dashboard_design_json)
	file_path = str(pathlib.Path().absolute()) + "/templates/generated/" + this_kode_dashboard + ".html"
	context['data_design'] = data_design
	context['kode_dashboard'] = this_kode_dashboard
	context['height_chart'] = 460 #def 370
	content	= render_to_string('backend/template_generator.html', context)
	with open(file_path, 'w') as filetowrite:
		filetowrite.write(content)
	print("generate template html")

@background(queue='front_end list')
def scheduller_front_end_making(message):
	list_dashboard = dashboard.objects.filter(dashboard_state=100).exclude(dashboard_disabled=1)
	is_present = False
	for data_dashboard_temporary in list_dashboard:
		if (data_dashboard_temporary.dashboard_date_update >= data_dashboard_temporary.dashboard_date_update_design):
			data_dashboard = data_dashboard_temporary
			is_present = True
	is_processing = False
	if is_present:
		kode_dashboard = data_dashboard.dashboard_kode
		print("--Front-end Scheduller--")
		data_list_tabel = json.loads(data_dashboard.dashboard_list_relation_data)
		data_design = json.loads(data_dashboard.dashboard_design_json)
		for index1, data1 in data_design.items():
			for index2, data2 in data1.items():
				if is_processing:
					break
				if (data2["tipe"] != 0) and (data2["already_processed"] == 0):
					is_processing = True
					kode_template = data2["kode_template"]
					data_processed = {}
					print("Start Mongo Pipeline :" + str(time.time()))
					if (data2["tipe"] == "1"):
						if (data2["data_setting"]["include_data"] == 1):
							data_query = get_data_group_none(data2["data_where"], data2["data_setting"]["id_selected_tabel"], data2["data_setting"]["id_selected_column"], data_list_tabel, data2["data_setting"]["mode_calculation"])
							value_processing = 0
							for data in data_query:
								#https://stackoverflow.com/questions/41308044/mongodb-numberdecimal-unsupported-operand-types-for-decimal128-and-deci
								value_processing = data["total"] #hasil return dengan type <class 'bson.decimal128.Decimal128'>
								print("tipe Data : " + str(type(data["total"])))
								if (str(type(data["total"])) == "<class 'bson.decimal128.Decimal128'>"):
									value_processing = (data["total"]).to_decimal()
								else:
									value_processing = data["total"]
							print(type(value_processing))
							data_processed = value_processing
							if (not isinstance(value_processing,int)):
								data_processed = int(round(value_processing,0))
							data_processed = (f"{data_processed:,}").replace(',', '.')
							print(data_processed)
							update_data_template_design(kode_dashboard, kode_template, data_processed, "")
							generate_template(kode_dashboard)
						else:
							update_data_template_design(kode_dashboard, kode_template, data_processed, "")
							generate_template(kode_dashboard)
					elif (data2["tipe"] == "2") or (data2["tipe"] == "5") or (data2["tipe"] == "7") or (data2["tipe"] == "9") or (data2["tipe"] == "11"):
						data_query = get_data_group(data2["data_where"], data2["data_setting"]["id_selected_tabel"], data2["data_setting"]["id_selected_column"], data_list_tabel, data2["data_setting"]["mode_calculation"], data2["data_setting"]["id_selected_column_header"], 1, 2, -1) # 1 = sort active, 2 = sort by value, 3 = sort desc
						list_data = {}
						index_data = 0
						#make_lower_ranking_others, minimum_make_lower_ranking_others
						data_hasil_total = 0
						data_temp = 0
						data_header_temp = ""
						for data in data_query:
							data_header_temp = str(data["_id"])
							if (str(type(data["total"])) == "<class 'bson.decimal128.Decimal128'>"):
								data_temp = (data["total"]).to_decimal()
								data_hasil_total = int(round(data_temp, 0))
							else:
								data_hasil_total = data["total"]
							if (data2["data_setting"]["make_lower_ranking_others"] == 1):
								if (index_data == data2["data_setting"]["minimum_make_lower_ranking_others"]):
									list_data[index_data] = {}
									list_data[index_data]["header"] = "others"
									list_data[index_data]["total"] = data_hasil_total
								elif (index_data > data2["data_setting"]["minimum_make_lower_ranking_others"]):
									list_data[data2["data_setting"]["minimum_make_lower_ranking_others"]]["total"] += data["total"]
								else:
									list_data[index_data] = {}
									#simpan dalam byte
									#https://stackoverflow.com/questions/41107871/how-to-automatically-escape-control-characters-in-a-python-string
									#simpan dalam string
									#https://stackoverflow.com/questions/18935754/how-to-escape-special-characters-of-a-string-with-single-backslashes/18935765
									data_header_temp = re.escape(data_header_temp)
									list_data[index_data]["header"] = data_header_temp
									list_data[index_data]["total"] = data_hasil_total
							else:
								list_data[index_data] = {}
								data_header_temp = re.escape(data_header_temp)
								list_data[index_data]["header"] = data_header_temp
								list_data[index_data]["total"] = data_hasil_total
							index_data += 1
						data_processed = list_data
						additional_script_final = ""
						if data2["tipe"] == "2":
							additional_script_load = "var variab_%s = document.getElementById('%s').getContext('2d');" % (data2["kode_template"],data2["kode_template"])
							additional_script_load_temp = "var chart_%s = new Chart(variab_%s, { type: 'pie', data: data_%s, options: options_%s});" % (data2["kode_template"],data2["kode_template"],data2["kode_template"],data2["kode_template"])
							additional_script_final = additional_script_load + additional_script_load_temp
						elif data2["tipe"] == "5":
							additional_script_load = "var variab_%s = document.getElementById('%s').getContext('2d');" % (data2["kode_template"],data2["kode_template"])
							additional_script_load_temp = "var chart_%s = new Chart(variab_%s, { type: 'doughnut', data: data_%s, options: options_%s});" % (data2["kode_template"],data2["kode_template"],data2["kode_template"],data2["kode_template"])
							additional_script_final = additional_script_load + additional_script_load_temp
						elif data2["tipe"] == "7":
							additional_script_final = "var chart_%s = new CanvasJS.Chart('%s', config_%s);chart_%s.render();" % (data2["kode_template"],data2["kode_template"],data2["kode_template"],data2["kode_template"])
						elif data2["tipe"] == "9":
							additional_script_final = "$('#table_%s').DataTable();" % (data2["kode_template"])
						elif data2["tipe"] == "11":
							additional_script_load = "var variab_%s = echarts.init(document.getElementById('%s'));" % (data2["kode_template"],data2["kode_template"])
							additional_script_load_temp = "variab_%s.setOption(option_%s);" % (data2["kode_template"],data2["kode_template"])
							additional_script_final = additional_script_load + additional_script_load_temp
						update_data_template_design(kode_dashboard, kode_template, data_processed, additional_script_final)
						generate_template(kode_dashboard)
					elif (data2["tipe"] == "3") or (data2["tipe"] == "8"):
						if data2["data_setting"]["sort_header"] == 0:
							data_query = get_data_group(data2["data_where"], data2["data_setting"]["id_selected_tabel"], data2["data_setting"]["id_selected_column"], data_list_tabel, data2["data_setting"]["mode_calculation"], data2["data_setting"]["id_selected_column_header"], 0) # 1 = sort active, 2 = sort by value, 3 = sort desc
						else:
							data_query = get_data_group(data2["data_where"], data2["data_setting"]["id_selected_tabel"], data2["data_setting"]["id_selected_column"], data_list_tabel, data2["data_setting"]["mode_calculation"], data2["data_setting"]["id_selected_column_header"], 1, 1, data2["data_setting"]["sort_header"])
						list_data = {}
						index_data = 0
						#make_lower_ranking_others, minimum_make_lower_ranking_others
						data_hasil_total = 0
						data_temp = 0
						data_header_temp = ""
						for data in data_query:
							data_header_temp = str(data["_id"])
							if (str(type(data["total"])) == "<class 'bson.decimal128.Decimal128'>"):
								data_temp = (data["total"]).to_decimal()
								data_hasil_total = int(round(data_temp, 0))
							else:
								data_hasil_total = data["total"]
							list_data[index_data] = {}
							data_header_temp = re.escape(data_header_temp)
							list_data[index_data]["header"] = data_header_temp
							list_data[index_data]["total"] = data_hasil_total
							index_data += 1
						data_processed = list_data
						additional_script_final = ""
						if data2["tipe"] == "3":
							additional_script_load = "var variab_%s = document.getElementById('%s').getContext('2d');" % (data2["kode_template"],data2["kode_template"])
							additional_script_load_temp = "var chart_%s = new Chart(variab_%s, { type: 'bar', data: data_%s, options: options_%s});" % (data2["kode_template"],data2["kode_template"],data2["kode_template"],data2["kode_template"])
							additional_script_final = additional_script_load + additional_script_load_temp
						elif data2["tipe"] == "8":
							additional_script_final = "var chart_%s = new CanvasJS.Chart('%s', config_%s);chart_%s.render();" % (data2["kode_template"],data2["kode_template"],data2["kode_template"],data2["kode_template"])
						update_data_template_design(kode_dashboard, kode_template, data_processed, additional_script_final)
						generate_template(kode_dashboard)	
					elif (data2["tipe"] == "6") or (data2["tipe"] == "4") or (data2["tipe"] == "15"):
						list_data = {}
						index_data = 0
						data_query = get_data_group(data2["data_where"], data2["data_setting"]["id_selected_tabel"], data2["data_setting"]["id_selected_column"], data_list_tabel, data2["data_setting"]["mode_calculation"], data2["data_setting"]["id_selected_column_header"], 1, 1, data2["data_setting"]["sort_header"]) # 1 = sort active, 2 = sort by value, 3 = sort desc
						data_hasil_total = 0
						data_temp = 0
						data_header_temp = ""
						for data in data_query:
							data_header_temp = str(data["_id"])
							if (str(type(data["total"])) == "<class 'bson.decimal128.Decimal128'>"):
								data_temp = (data["total"]).to_decimal()
								data_hasil_total = int(round(data_temp, 0))
							else:
								data_hasil_total = data["total"]
							list_data[index_data] = {}
							data_header_temp = re.escape(data_header_temp)
							list_data[index_data]["header"] = data_header_temp
							list_data[index_data]["total"] = data_hasil_total
							index_data += 1
						data_processed = list_data
						if data2["tipe"] == "6":
							additional_script_load = "var variab_%s = document.getElementById('%s').getContext('2d');" % (data2["kode_template"],data2["kode_template"])
							additional_script_load_temp = "var chart_%s = new Chart(variab_%s, { type: 'line', data: data_%s, options: options_%s});" % (data2["kode_template"],data2["kode_template"],data2["kode_template"],data2["kode_template"])
							additional_script_final = additional_script_load + additional_script_load_temp
						elif data2["tipe"] == "4":
							additional_script_final = "var chart_%s = new CanvasJS.Chart('%s', config_%s);chart_%s.render();" % (data2["kode_template"],data2["kode_template"],data2["kode_template"],data2["kode_template"])
						elif data2["tipe"] == "15":
							additional_script_load = "var variab_%s = echarts.init(document.getElementById('%s'));" % (data2["kode_template"],data2["kode_template"])
							additional_script_load_temp = "variab_%s.setOption(option_%s);" % (data2["kode_template"],data2["kode_template"])
							additional_script_final = additional_script_load + additional_script_load_temp
						update_data_template_design(kode_dashboard, kode_template, data_processed, additional_script_final)
						generate_template(kode_dashboard)
					elif (data2["tipe"] == "10") or (data2["tipe"] == "12") or (data2["tipe"] == "13") or (data2["tipe"] == "14"):
						list_data = {}
						#(data_where, id_tabel, id_column, data_relations, calculation, grouped_column, additional_group, data_group = 0, dataset_group = 0, header_data_group = 0)
						data_query = get_data_double_group(data2["data_where"], data2["data_setting"]["id_selected_tabel"], data2["data_setting"]["id_selected_column"], data_list_tabel, data2["data_setting"]["mode_calculation"], data2["data_setting"]["id_selected_column_dataset"], data2["data_setting"]["id_selected_column_header"], data2["data_setting"]["sort_data"], data2["data_setting"]["sort_dataset"], 0)#data2["data_setting"]["sort_header"] # 1 = sort active, 2 = sort by value, 3 = sort desc
						data_hasil_total = 0
						data_temp = 0
						data_header_temp = ""
						data_dataset_temp = ""
						data_first_process = True
						list_data["data"] = {}
						list_data["header"] = {}
						for data in data_query:
							data_dataset_temp = str(data["_id"]["_id"])
							data_dataset_temp = re.escape(data_dataset_temp)
							if (data_first_process):
								list_data["data"][data_dataset_temp] = {}
								data_first_process = False
							else:
								if not (data_dataset_temp in list_data["data"]):
									list_data["data"][data_dataset_temp] = {}
							data_header_temp = str(data["_id"]["additional"])
							data_header_temp = re.escape(data_header_temp)
							if (str(type(data["total"])) == "<class 'bson.decimal128.Decimal128'>"):
								data_temp = (data["total"]).to_decimal()
								data_hasil_total = int(round(data_temp, 0))
							else:
								data_hasil_total = data["total"]
							list_data["data"][data_dataset_temp][data_header_temp] = data_hasil_total
							list_data["header"][data_header_temp] = 0
						#begin building structural header
						temp_structural_header = list_data["header"]
						if (data2["data_setting"]["sort_header"] == 1):
							structural_header = sorted(temp_structural_header.keys())
						elif (data2["data_setting"]["sort_header"] == -1):
							structural_header = sorted(temp_structural_header.keys(), reverse=True)
						else:
							structural_header = temp_structural_header
						#end building structural header
						list_data_pre_final = {}
						for index_processing, data_processing in list_data["data"].items():
							list_data_pre_final[index_processing] = {}
							for data_header in structural_header:
								list_data_pre_final[index_processing][data_header] = 0
							for index_processing1, data_processing1 in data_processing.items():
								list_data_pre_final[index_processing][index_processing1] = data_processing1
						list_data_final = {}
						dataset_index = 0
						index_data = 0
						for index_processing, data_processing in list_data_pre_final.items():
							dataset_index = len(list_data_final)
							list_data_final[dataset_index] = {}
							list_data_final[dataset_index]["dataset_name"] = index_processing
							list_data_final[dataset_index]["data"] = {}
							for index_processing1, data_processing1 in data_processing.items():
								index_data = len(list_data_final[dataset_index]["data"])
								list_data_final[dataset_index]["data"][index_data] = {}
								list_data_final[dataset_index]["data"][index_data]["header"] = index_processing1
								list_data_final[dataset_index]["data"][index_data]["total"] = data_processing1
						data_processed = list_data_final
						additional_script_final = ""
						if data2["tipe"] == "10":
							additional_script_load = "var variab_%s = document.getElementById('%s').getContext('2d');" % (data2["kode_template"],data2["kode_template"])
							additional_script_load_temp = "var chart_%s = new Chart(variab_%s, { type: 'bar', data: data_%s, options: options_%s});" % (data2["kode_template"],data2["kode_template"],data2["kode_template"],data2["kode_template"])
							additional_script_final = additional_script_load + additional_script_load_temp
						elif data2["tipe"] == "12":
							additional_script_load = "var variab_%s = document.getElementById('%s').getContext('2d');" % (data2["kode_template"],data2["kode_template"])
							additional_script_load_temp = "var chart_%s = new Chart(variab_%s, { type: 'line', data: data_%s, options: options_%s});" % (data2["kode_template"],data2["kode_template"],data2["kode_template"],data2["kode_template"])
							additional_script_final = additional_script_load + additional_script_load_temp
						elif data2["tipe"] == "13":
							additional_script_final = "var chart_%s = new CanvasJS.Chart('%s', config_%s);chart_%s.render();" % (data2["kode_template"],data2["kode_template"],data2["kode_template"],data2["kode_template"])
						elif data2["tipe"] == "14":
							additional_script_load = "var variab_%s = echarts.init(document.getElementById('%s'));" % (data2["kode_template"],data2["kode_template"])
							additional_script_load_temp = "variab_%s.setOption(option_%s);" % (data2["kode_template"],data2["kode_template"])
							additional_script_final = additional_script_load + additional_script_load_temp
						# additional_script_final = ""
						update_data_template_design(kode_dashboard, kode_template, data_processed, additional_script_final)
						generate_template(kode_dashboard)
					print("End Mongo Pipeline :" + str(time.time()))
			if is_processing:
				break
		if not is_processing:
			update_last_design_update(data_dashboard.dashboard_kode)
			generate_template(kode_dashboard)
		else:
			print("update kode template : " + kode_template)
		# clean_log_background_task()
		print("--End Front-end Scheduller--")
	

#untuk memasukkan data ke dalam dashboard
def update_data_template_design(kode_dashboard, kode_template, data_processed, additional_script):
	list_dashboard = dashboard.objects.filter(dashboard_kode=kode_dashboard)[0:1]
	for data in list_dashboard:
		data_design = json.loads(data.dashboard_design_json)
	done = False;
	for index1, data1 in data_design.items():
		if done:
			break;
		for index2, data2 in data1.items():
			if (data2["kode_template"] == kode_template):
				data_design[index1][index2]["data_processed"] = data_processed
				data_design[index1][index2]["already_processed"] = 1
				data_design[index1][index2]["additional_script_windows_already_loaded"] = additional_script
				temporary_dump = json.dumps(data_design, indent=4)
				dashboard.objects.select_related().filter(dashboard_kode = kode_dashboard).update(dashboard_design_json=temporary_dump)
				break;
	
@background(queue='feeding list')
def scheduller_feeding(message):
	# print(message)
	#https://docs.djangoproject.com/en/3.1/ref/models/querysets/#django.db.models.query.QuerySet
	list_dashboard = dashboard.objects.filter(dashboard_state=1, dashboard_next_check_connection__lte=time.time()).exclude(dashboard_disabled=1)[0:1]
	if (len(list_dashboard) == 1):
		for data_dashboard in list_dashboard:
			print("process feeding list tabel :" + str(data_dashboard.dashboard_kode))
			if (data_dashboard.dashboard_tipe_data == 1):
				if not check_databases_postgresql_connection(data_dashboard.dashboard_database_address, data_dashboard.dashboard_database_name, data_dashboard.dashboard_database_username, data_dashboard.dashboard_database_password):
					dashboard.objects.select_related().filter(dashboard_kode = data_dashboard.dashboard_kode).update(dashboard_next_check_connection=time.time()+500)
					print("Gagal Koneksi")
					return True
				#Begin konesi database
				conn = psycopg2.connect(
					host=data_dashboard.dashboard_database_address,
					database=data_dashboard.dashboard_database_name,
					user=data_dashboard.dashboard_database_username,
					password=data_dashboard.dashboard_database_password)
				cur = conn.cursor()
				cur.execute("""SELECT table_name
		FROM information_schema.tables
		WHERE table_schema = 'public'
		ORDER BY table_name;""")
				list_table = cur.fetchall()
				list_column = {}
				counting_helper = 0
				counting_column_helper = 0
				dict_list_table = {}
				temporary_query_get_column = ""
				for row in list_table:
					# print(row[0])
					#https://www.pythonforbeginners.com/concatenation/string-concatenation-and-formatting-in-python
					temporary_query_get_column = "SELECT column_name, data_type FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '%s'" % (row[0])
					cur.execute(temporary_query_get_column)
					list_column = cur.fetchall()
					counting_column_helper = 0
					dict_list_table[counting_helper] = {}
					dict_list_table[counting_helper]["nama_tabel"] = row[0]
					dict_list_table[counting_helper]["is_selected"] = 0
					dict_list_table[counting_helper]["list_column"] = {}
					for row1 in list_column:
						dict_list_table[counting_helper]["list_column"][counting_column_helper]={}
						dict_list_table[counting_helper]["list_column"][counting_column_helper]["nama_column"]=row1[0]
						dict_list_table[counting_helper]["list_column"][counting_column_helper]["is_primary"]=0
						dict_list_table[counting_helper]["list_column"][counting_column_helper]["is_have_parent"]=0
						dict_list_table[counting_helper]["list_column"][counting_column_helper]["type_data"]=0 #0 = text, 1 = number, 2 = date
						dict_list_table[counting_helper]["list_column"][counting_column_helper]["type_data_from_source"]=row1[1]
						dict_list_table[counting_helper]["list_column"][counting_column_helper]["parent_tabel_id"]=0
						dict_list_table[counting_helper]["list_column"][counting_column_helper]["parent_tabel_id_column"]=0
						counting_column_helper+= 1
					counting_helper += 1
				#https://www.kite.com/python/examples/329/json-encode-a-%60dict%60-to-a-json-string
				temporary_dump = json.dumps(dict_list_table, indent=4)
				dashboard.objects.select_related().filter(dashboard_kode = data_dashboard.dashboard_kode).update(dashboard_list_tabels=temporary_dump, dashboard_next_check_connection=0,dashboard_state=2)
				cur.close()
				#End konesi database
			elif (data_dashboard.dashboard_tipe_data == 2): #process bila tipe data MySQL
				if not check_databases_mysql_connection(data_dashboard.dashboard_database_address, data_dashboard.dashboard_database_name, data_dashboard.dashboard_database_username, data_dashboard.dashboard_database_password):
					dashboard.objects.select_related().filter(dashboard_kode = data_dashboard.dashboard_kode).update(dashboard_next_check_connection=time.time()+500)
					print("Gagal Koneksi")
					return True
				conn = mysql.connector.connect(
					host=data_dashboard.dashboard_database_address,
					database=data_dashboard.dashboard_database_name,
					user=data_dashboard.dashboard_database_username,
					password=data_dashboard.dashboard_database_password)
				cur = conn.cursor()
				query = "SELECT table_name FROM information_schema.tables WHERE table_schema = '" + data_dashboard.dashboard_database_name + "';"
				cur.execute(query)
				list_table = cur.fetchall()
				list_column = {}
				counting_helper = 0
				counting_column_helper = 0
				dict_list_table = {}
				temporary_query_get_column = ""
				for data in list_table:
					query = "SELECT COLUMN_NAME FROM information_schema.columns WHERE table_schema='" + data_dashboard.dashboard_database_name + "' AND table_name='" + data[0] + "' "
					cur.execute(query)
					list_column = cur.fetchall()
					counting_column_helper = 0
					dict_list_table[counting_helper] = {}
					dict_list_table[counting_helper]["nama_tabel"] = data[0]
					dict_list_table[counting_helper]["is_selected"] = 0
					dict_list_table[counting_helper]["list_column"] = {}
					for data_col in list_column:
						dict_list_table[counting_helper]["list_column"][counting_column_helper]={}
						dict_list_table[counting_helper]["list_column"][counting_column_helper]["nama_column"]=data_col[0]
						dict_list_table[counting_helper]["list_column"][counting_column_helper]["is_primary"]=0
						dict_list_table[counting_helper]["list_column"][counting_column_helper]["is_have_parent"]=0
						dict_list_table[counting_helper]["list_column"][counting_column_helper]["type_data"]=0 #0 = text, 1 = number, 2 = date
						dict_list_table[counting_helper]["list_column"][counting_column_helper]["parent_tabel_id"]=0
						dict_list_table[counting_helper]["list_column"][counting_column_helper]["parent_tabel_id_column"]=0
						counting_column_helper+= 1
					counting_helper += 1
					temporary_dump = json.dumps(dict_list_table, indent=4)
					dashboard.objects.select_related().filter(dashboard_kode = data_dashboard.dashboard_kode).update(dashboard_list_tabels=temporary_dump, dashboard_next_check_connection=0,dashboard_state=2)
			elif (data_dashboard.dashboard_tipe_data == 3): #process bila tipe data CSV
				# list_tabel_name = []
				file_path = data_dashboard.dashboard_excel_path
				dict_list_table = {}
				dict_list_table[0] = {}
				dict_list_table[0]["nama_tabel"] = "CSV"
				dict_list_table[0]["is_selected"] = 1
				dict_list_table[0]["list_column"] = {}
				counting_column_helper = 0
				with open(file_path, 'r', encoding='utf-8-sig') as csv_file:
					csv_reader = csv.reader(csv_file, delimiter=';')
					for row in csv_reader:
						for data in row:
							dict_list_table[0]["list_column"][counting_column_helper]={}
							dict_list_table[0]["list_column"][counting_column_helper]["nama_column"]=data
							dict_list_table[0]["list_column"][counting_column_helper]["is_primary"]=0
							dict_list_table[0]["list_column"][counting_column_helper]["is_have_parent"]=0
							dict_list_table[0]["list_column"][counting_column_helper]["type_data"]=0 #0 = text, 1 = number, 2 = date
							dict_list_table[0]["list_column"][counting_column_helper]["parent_tabel_id"]=0
							dict_list_table[0]["list_column"][counting_column_helper]["parent_tabel_id_column"]=0
							counting_column_helper+= 1
							# list_tabel_name.append(data)
						break
				print("done Process Header CSV")
				temporary_dump = json.dumps(dict_list_table, indent=4)
				dashboard.objects.select_related().filter(dashboard_kode = data_dashboard.dashboard_kode).update(dashboard_list_tabels=temporary_dump, dashboard_next_check_connection=0,dashboard_state=2)
					
	#building relation for design database
	list_dashboard = dashboard.objects.filter(dashboard_state=50, dashboard_next_check_connection__lte=time.time()).exclude(dashboard_disabled=1)[0:1]
	for data_dashboard in list_dashboard:
		print("process create relation list tabel :" + str(data_dashboard.dashboard_kode))
		list_split = str(data_dashboard.dashboard_list_count_tabels).split(",")
		tabel_list = {}
		data_list = {}
		count_dict = 0
		print("create relation for design")
		for data in list_split:
			data_list[count_dict] = {}
			tabel_list = json.loads(data_dashboard.dashboard_list_tabels)
			data_list[count_dict]["id_tabel"] = data
			data_list[count_dict]["mongo_db_collection_name"] = data_dashboard.dashboard_kode + "_" + str(data)
			data_list[count_dict]["nama_tabel"] = tabel_list[data]["nama_tabel"]
			data_list[count_dict]["list_tabel_feeding"] = build_structural_tabel_query(tabel_list, data)
			count_dict += 1
		data_dashboard_list_relation_data = json.dumps(data_list, indent=4)
		dashboard.objects.select_related().filter(dashboard_kode = data_dashboard.dashboard_kode).update(dashboard_state=54, dashboard_list_relation_data = data_dashboard_list_relation_data)
	#feeding data
	list_dashboard = dashboard.objects.filter(dashboard_state=54, dashboard_next_check_connection__lte=time.time()).exclude(dashboard_disabled=1)[0:1]
	for data_dashboard in list_dashboard:
		print("process feeding data :" + str(data_dashboard.dashboard_kode))
		print("data_list_feeding : " + str(data_dashboard.dashboard_list_count_tabels))
		print("Current Page : " + str(data_dashboard.dashboard_list_count_current_row_tabels))
		print("Start Process :" + str(time.time()))
		if (data_dashboard.dashboard_tipe_data == 1):
			if (len(data_dashboard.dashboard_list_count_tabels) != 0):
				if not check_databases_postgresql_connection(data_dashboard.dashboard_database_address, data_dashboard.dashboard_database_name, data_dashboard.dashboard_database_username, data_dashboard.dashboard_database_password):
					dashboard.objects.select_related().filter(dashboard_kode = data_dashboard.dashboard_kode).update(dashboard_next_check_connection=time.time()+500)
					print("Gagal Koneksi")
					return True
				limit = limit_data_row_processing
				data_tabel = json.loads(data_dashboard.dashboard_list_tabels)
				list_split = str(data_dashboard.dashboard_list_count_tabels).split(",")
				data_list_relation = json.loads(data_dashboard.dashboard_list_relation_data)
				query = generate_query(data_tabel, list_split[0], int(data_dashboard.dashboard_list_count_current_row_tabels))
				print("mulai feeding data")
				conn = psycopg2.connect(
					host=data_dashboard.dashboard_database_address,
					database=data_dashboard.dashboard_database_name,
					user=data_dashboard.dashboard_database_username,
					password=data_dashboard.dashboard_database_password)
				cur = conn.cursor()
				cur.execute(query)
				hasil_query = cur.fetchall()				
				helper_count = 0
				client = MongoClient(mongo_db_address)
				db=client[database_setting]
				#https://stackoverflow.com/questions/24799988/is-it-possible-to-use-variable-for-collection-name-using-pymongo
				target_mongo_tabel = data_dashboard.dashboard_kode + "_" + str(list_split[0])
				data_type = ""
				relation_data_type = get_column_type_from_relation(data_list_relation, list_split[0])
				
				print("Done Ambil data from source :" + str(time.time()))
				for row in hasil_query:
					data_insert = {}
					helper_count = 0
					for data in row:
						#https://stackoverflow.com/questions/17143132/python-psycopg2-postgres-select-columns-including-field-names/45050139
						nama_column = str(cur.description[helper_count][0])
						temporary = str(nama_column) + ":" + str(type(data))
						# print(temporary)
						data_type = str(type(data))
						if (data_type == "<class 'dict'>"):
							data_insert[nama_column] = json.dumps(data, indent=4)
						elif (data_type == "<class 'list'>"):
							data_insert[nama_column] = json.dumps(data, indent=4)
						elif (data_type == "<class 'NoneType'>"):
							data = ""
							data_insert[nama_column] = ""
						else:
							data_insert[nama_column] = data
						if (relation_data_type[helper_count] == 0):#bila data type string
							data_insert[nama_column] = str(data_insert[nama_column])
						elif (relation_data_type[helper_count] == 2): #process kalau decimal
							#https://github.com/MongoEngine/mongoengine/issues/707
							#https://stackoverflow.com/questions/17039018/how-to-use-a-variable-as-a-field-name-in-mongodb-native-findone
							if (data_type == "<class 'decimal.Decimal'>"):
								data_insert[nama_column] = Decimal128(data)
							else:
								try:
									data_insert[nama_column] = Decimal128(data)
								except ValueError:
									data_insert[nama_column] = str(data)
						else:
							try:
								data_insert[nama_column] = int(data)
							except ValueError:
								try:
									data_insert[nama_column] = int(float(data))
								except ValueError:
									data_insert[nama_column] = str(data_insert[nama_column])
						helper_count += 1
					result = db[target_mongo_tabel].insert_one(data_insert)
				cur.close()
				print("Done Input to database :" + str(time.time()))
				if (len(hasil_query) < limit): # == 0
					list_tabel = ""
					for data in list_split:
						if (data != list_split[0]):
							if (list_tabel == ""):
								list_tabel = str(data)
							else:
								list_tabel = list_tabel + "," + str(data)
					dashboard.objects.select_related().filter(dashboard_kode = data_dashboard.dashboard_kode).update(dashboard_list_count_current_row_tabels = 1, dashboard_list_count_tabels=list_tabel)
				else:
					next_page = int(data_dashboard.dashboard_list_count_current_row_tabels) + 1
					dashboard.objects.select_related().filter(dashboard_kode = data_dashboard.dashboard_kode).update(dashboard_list_count_current_row_tabels = next_page)
			else:
				print("Done feeding data :" + str(data_dashboard.dashboard_kode))
				dashboard.objects.select_related().filter(dashboard_kode = data_dashboard.dashboard_kode).update(dashboard_state=100)
				update_last_update(data_dashboard.dashboard_kode)
		elif (data_dashboard.dashboard_tipe_data == 2):
			if (len(data_dashboard.dashboard_list_count_tabels) != 0):
				if not check_databases_mysql_connection(data_dashboard.dashboard_database_address, data_dashboard.dashboard_database_name, data_dashboard.dashboard_database_username, data_dashboard.dashboard_database_password):
					dashboard.objects.select_related().filter(dashboard_kode = data_dashboard.dashboard_kode).update(dashboard_next_check_connection=time.time()+500)
					print("Gagal Koneksi")
					return True
				limit = limit_data_row_processing
				data_tabel = json.loads(data_dashboard.dashboard_list_tabels)
				list_split = str(data_dashboard.dashboard_list_count_tabels).split(",")
				data_list_relation = json.loads(data_dashboard.dashboard_list_relation_data)
				query = generate_query_mysql(data_tabel, list_split[0], int(data_dashboard.dashboard_list_count_current_row_tabels))
				print("mulai feeding data")
				conn = mysql.connector.connect(
					host=data_dashboard.dashboard_database_address,
					database=data_dashboard.dashboard_database_name,
					user=data_dashboard.dashboard_database_username,
					password=data_dashboard.dashboard_database_password)
				cur = conn.cursor()
				cur.execute(query)
				hasil_query = cur.fetchall()
				helper_count = 0
				client = MongoClient(mongo_db_address)
				db=client[database_setting]
				#https://stackoverflow.com/questions/24799988/is-it-possible-to-use-variable-for-collection-name-using-pymongo
				target_mongo_tabel = data_dashboard.dashboard_kode + "_" + str(list_split[0])
				data_type = ""
				relation_data_type = get_column_type_from_relation(data_list_relation, list_split[0])
				print("Done Ambil data from source :" + str(time.time()))
				for row in hasil_query:
					data_insert = {}
					helper_count = 0
					for data in row:
						#https://stackoverflow.com/questions/17143132/python-psycopg2-postgres-select-columns-including-field-names/45050139
						nama_column = str(cur.description[helper_count][0])
						temporary = str(nama_column) + ":" + str(type(data))
						# print(temporary)
						data_type = str(type(data))
						if (data_type == "<class 'dict'>"):
							data_insert[nama_column] = json.dumps(data, indent=4)
						elif (data_type == "<class 'list'>"):
							data_insert[nama_column] = json.dumps(data, indent=4)
						elif (data_type == "<class 'NoneType'>"):
							data = ""
							data_insert[nama_column] = ""
						else:
							data_insert[nama_column] = data
						if (relation_data_type[helper_count] == 0):#bila data type string
							data_insert[nama_column] = str(data_insert[nama_column])
						elif (relation_data_type[helper_count] == 2): #process kalau decimal
							#https://github.com/MongoEngine/mongoengine/issues/707
							#https://stackoverflow.com/questions/17039018/how-to-use-a-variable-as-a-field-name-in-mongodb-native-findone
							if (data_type == "<class 'decimal.Decimal'>"):
								data_insert[nama_column] = Decimal128(data)
							else:
								try:
									data_insert[nama_column] = Decimal128(data)
								except ValueError:
									data_insert[nama_column] = str(data)
						else:
							try:
								data_insert[nama_column] = int(data)
							except ValueError:
								try:
									data_insert[nama_column] = int(float(data))
								except ValueError:
									data_insert[nama_column] = str(data_insert[nama_column])
						helper_count += 1
					result = db[target_mongo_tabel].insert_one(data_insert)
				cur.close()
				print("Done Input to database :" + str(time.time()))
				# if (len(hasil_query) < limit) and (len(hasil_query) != 0):
					# print(query)
					# print("-----------------------------------")
					# print("total row feeded : " + str(len(hasil_query)))
					# print("-----------------------------------")
				if (len(hasil_query) < limit): 
					list_tabel = ""
					for data in list_split:
						if (data != list_split[0]):
							if (list_tabel == ""):
								list_tabel = str(data)
							else:
								list_tabel = list_tabel + "," + str(data)
					dashboard.objects.select_related().filter(dashboard_kode = data_dashboard.dashboard_kode).update(dashboard_list_count_current_row_tabels = 1, dashboard_list_count_tabels=list_tabel)
				else:
					next_page = int(data_dashboard.dashboard_list_count_current_row_tabels) + 1
					dashboard.objects.select_related().filter(dashboard_kode = data_dashboard.dashboard_kode).update(dashboard_list_count_current_row_tabels = next_page)
		elif (data_dashboard.dashboard_tipe_data == 3):
			client = MongoClient(mongo_db_address)
			db=client[database_setting]
			target_mongo_tabel = data_dashboard.dashboard_kode + "_0"
			db[target_mongo_tabel].remove()
			data_list_relation = json.loads(data_dashboard.dashboard_list_relation_data)
			list_nama_column = []
			for index, data in data_list_relation["0"]["list_tabel_feeding"].items():
				list_nama_column.append(data["column_name_tabel_data"])
			data_insert = {}
			relation_data_type = get_column_type_from_relation(data_list_relation, 0)
			nama_column = ""
			with open(data_dashboard.dashboard_excel_path) as csv_file:
				csv_reader = csv.reader(csv_file, delimiter=';')
				line_count = 0
				column_count = 0
				for row in csv_reader:
					column_count = 0
					data_insert = {}
					if line_count > 0:
						for data in row:
							nama_column = list_nama_column[column_count]
							if (relation_data_type[column_count] == 0):#bila data type string
								data_insert[nama_column] = str(data)
							elif (relation_data_type[column_count] == 2): #process kalau decimal
								try:
									data_insert[nama_column] = Decimal128(data)
								except ValueError:
									data_insert[nama_column] = str(data)
							else:
								try:
									data_insert[nama_column] = int(data)
								except ValueError:
									try:
										data_insert[nama_column] = int(float(data))
									except ValueError:
										data_insert[nama_column] = str(data)
							column_count += 1
						result = db[target_mongo_tabel].insert_one(data_insert)
					else:
						line_count += 1
			dashboard.objects.select_related().filter(dashboard_kode = data_dashboard.dashboard_kode).update(dashboard_state=100)
		print("End Process :" + str(time.time()))

def get_column_type_from_relation(data_relations, this_id_tabel):
	id_tabel = str(this_id_tabel)
	list_type_column = []
	for index1, data1 in data_relations.items():
		if (id_tabel == data1["id_tabel"]):
			for index2, data2 in data1["list_tabel_feeding"].items():
				list_type_column.append(data2["column_type"])
	return list_type_column
			

def start_scheduler(request):
	myclient = MongoClient(mongo_db_address)
	mydb = myclient[database_setting]
	my_collection = mydb["background_task"]
	my_collection.remove()
	clean_log_background_task()
	scheduller_feeding("jalan", repeat=1)
	scheduller_front_end_making("jalan", repeat=1)
	return HttpResponse("Scheduller Dijalankan")

def clean_log_background_task():
	myclient = MongoClient(mongo_db_address)
	mydb = myclient[database_setting]
	my_collection = mydb["background_task_completedtask"]
	my_collection.remove()

def testing_array(request):
	list_dashboard = dashboard.objects.filter(dashboard_state=100, dashboard_date_update__lt=F("dashboard_date_update_design")).exclude(dashboard_disabled=1)
	for data in list_dashboard:
		print(data)
	return HttpResponse("masuk")
	