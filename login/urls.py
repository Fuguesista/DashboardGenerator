from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
	path('logout', views.do_logout, name='do_logout'),
]