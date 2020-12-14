from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
	# path('check_connection', views.check_connection, name='check_connection'),
	path('show_form_insert', views.show_form_insert, name='show_form_insert'),
	path('delete_dashboard', views.delete_dashboard, name='delete_dashboard'),
	path('refeeding_data', views.refeeding_data, name='refeeding_data'),
	path('process_new_dashboard', views.process_new_dashboard, name='process_new_dashboard'),
	path('view_dashboard_generated/<str:this_dashboard_kode>', views.view_dashboard_generated, name='view_dashboard_generated'),
	path('view_dashboard_generated_container/<str:this_dashboard_kode>', views.view_dashboard_generated_container, name='view_dashboard_generated_container'),
	path('recalculate_dashboard/<str:this_dashboard_kode>', views.recalculate_dashboard, name='recalculate_dashboard'),
	path('toggle_public_view', views.toggle_public_view, name='toggle_public_view'),

	path('start_scheduler', views.start_scheduler, name='start_scheduler'),
	#https://docs.djangoproject.com/en/2.1/topics/http/urls/
	path('relation_dashboard/<str:this_dashboard_kode>', views.relation_dashboard, name='relation_dashboard'),
	path('relation_dashboard_others_column', views.relation_dashboard_others_column, name='relation_dashboard_others_column'),
	path('relation_dashboard_processing/<str:this_dashboard_kode>', views.relation_dashboard_processing, name='relation_dashboard_processing'),
	path('container_design_dashboard/<str:this_dashboard_kode>', views.container_design_dashboard, name='container_design_dashboard'),
	path('generate_design_dashboard', views.generate_design_dashboard, name='generate_design_dashboard'),
	path('generate_design_dashboard_add_row', views.generate_design_dashboard_add_row, name='generate_design_dashboard_add_row'),
	path('generate_design_dashboard_delete_row', views.generate_design_dashboard_delete_row, name='generate_design_dashboard_delete_row'),
	path('generate_design_dashboard_add_input', views.generate_design_dashboard_add_input, name='generate_design_dashboard_add_input'),
	path('generate_design_dashboard_template', views.generate_design_dashboard_template, name='generate_design_dashboard_template'),
	path('generate_design_dashboard_edit_template', views.generate_design_dashboard_edit_template, name='generate_design_dashboard_edit_template'),
	path('generate_design_dashboard_reset_template', views.generate_design_dashboard_reset_template, name='generate_design_dashboard_reset_template'),
	path('show_template_modal', views.show_template_modal, name='show_template_modal'),
	path('generate_row_filter_where', views.generate_row_filter_where, name='generate_row_filter_where'),
	
	path('process_template', views.process_template, name='process_template'),
	path('send_list_column', views.send_list_column, name='send_list_column'),
	
	path('testing_array', views.testing_array, name='testing_array')
	
]