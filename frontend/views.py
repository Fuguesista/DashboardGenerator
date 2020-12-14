from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from backend.models import dashboard
from django.template import loader

base_http = "http://"
context = {
	'additional_message' : "",
	'base_http' : base_http
}

def index(request, this_dashboard_kode = ""):
	list_data_dashboard = dashboard.objects.filter(dashboard_kode=this_dashboard_kode, dashboard_state = 100).exclude(dashboard_disabled=1)[0:1]
	if len(list_data_dashboard) == 0:
		return HttpResponse("<div style='margin:auto'><h1>Dashboard Tidak Diketemukan</h1></div>")
	for data in list_data_dashboard:
		data_dashboard = data
	if request.user.is_authenticated:
		if request.user == data_dashboard.dashboard_owner_id:
			try:
				print("pemilik")
				template = loader.get_template('generated/' + this_dashboard_kode + '.html')
				return HttpResponse(template.render(context, request))
			except ValueError:
				return HttpResponse("")
	if data_dashboard.dashboard_ready == 1:
		try:
			template = loader.get_template('generated/' + this_dashboard_kode + '.html')
			return HttpResponse(template.render(context, request))
		except ValueError:
			return HttpResponse("")
	return HttpResponse("<div style='margin:auto'><h1>Dashboard Tidak Diketemukan</h1></div>")
	
def add_viewer(this_dashboard_kode):
	list_data_dashboard = dashboard.objects.filter(dashboard_kode=this_dashboard_kode).exclude(dashboard_disabled=1)[0:1]
	for data in list_data_dashboard:
		dashboard.objects.select_related().filter(dashboard_kode = this_dashboard_kode).update(dashboard_total_hit=data.dashboard_total_hit + 1)