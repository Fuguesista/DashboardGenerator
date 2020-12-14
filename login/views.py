from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
# from django.db import models
# from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.template import loader
import json

# import os

base_http = "http://"
context = {
	'additional_message' : "",
	'base_http' : base_http
}
	

def index(request):
	if request.user.is_authenticated:
		return HttpResponseRedirect('/backend/')
	# OSPATH = os.path.realpath('.')
	if 'submit' in request.POST:
		if 'username' not in request.POST:
			context['additional_message'] = "Username Must Be Filled"
		elif 'password' not in request.POST:
			context['additional_message'] = "Password Must Be Filled"
		else :
			user_check = authenticate(username=request.POST['username'], password=request.POST['password'])
			if user_check is not None:
				if user_check.is_active:
					login(request, user_check)
					return HttpResponseRedirect('/backend/')
			else:
				context['additional_message'] = "Username Or Password is Wrong"
	if 'username' in request.POST:
		context['username'] = request.POST['username'];
	else :
		context['username'] = "";
		
	if 'password' in request.POST:
		context['password'] = request.POST['password'];
	else :
		context['password'] = "";
		
	template = loader.get_template('login/index.html')
	return HttpResponse(template.render(context, request))
	# if request.user.is_authenticated:
		# return HttpResponse("Masuk")
	# else:
		# return HttpResponse("Keluar")
		
		
def do_logout(request):
	if request.user.is_authenticated:
		logout(request)
	return HttpResponseRedirect(base_http + request.META['HTTP_HOST'])