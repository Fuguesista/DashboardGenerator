from django.urls import path

from . import views

urlpatterns = [
    path('<str:this_dashboard_kode>', views.index, name='index'),
	path('', views.index, name='index'),
]