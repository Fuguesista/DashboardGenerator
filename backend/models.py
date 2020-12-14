from django.conf import settings
from django.db import models
from django.db import connection
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

def get_sentinel_user():
	return get_user_model().objects.get_or_create(username='deleted')[0]

#Truncate https://stackoverflow.com/questions/2988997/how-to-truncate-table-using-djangos-orm


# Create your models here.
#https://stackoverflow.com/questions/56268626/is-there-any-way-to-set-default-value-in-charfield-of-django-model/56268689
class dashboard(models.Model):
	# https://stackoverflow.com/questions/34305805/django-foreignkeyuser-in-models
	dashboard_owner_id = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET(get_sentinel_user),)
	# https://www.it-swarm.dev/id/python/bagaimana-cara-membuat-bidang-integer-kenaikan-otomatis-di-django/1043801067/
	dashboard_id = models.AutoField(primary_key=True)
	dashboard_kode = models.CharField(unique=True,max_length=200)
	dashboard_name = models.CharField(max_length=200)
	dashboard_tipe_data = models.IntegerField() #1 = database postgre, 2 Mysql, 3 excel / csv
	dashboard_state = models.IntegerField()
	dashboard_next_check_connection = models.IntegerField()
	dashboard_ready = models.IntegerField() #is dashboard ready from temporary viewitems
	dashboard_last_seen = models.DateTimeField(auto_now_add=True) #last open dashboard 
	dashboard_total_hit = models.IntegerField(default=0) #total access to dashboard
	dashboard_disabled = models.IntegerField(default=0)
	dashboard_list_tabels = models.TextField(default='') #menampung juga list column tabel yang ada
	dashboard_list_count_tabels = models.TextField() #Untuk list id tabel yang dipisahkan ,
	dashboard_list_count_current_row_tabels = models.IntegerField(default=1) #Untuk menampung sedang pada page berapa, akan reset 1 setiap ganti tabel
	dashboard_can_be_viewed = models.IntegerField(default=0)
	dashboard_design_json = models.TextField(default='{}')
	dashboard_date_creation = models.DateTimeField(auto_now_add=True)
	dashboard_date_update = models.IntegerField(default=0)
	dashboard_date_update_design = models.IntegerField(default=0)
	# dashboard_date_update_design_is_finised = models.IntegerField(default=1)
	# dashboard_last_update_design_last = models.TextField(default='{}')
	# dashboard_last_update_coordinate = models.TextField(default='0,0')
	dashboard_database_address = models.TextField(default='000.000.000.000')
	dashboard_database_username = models.TextField(default='')
	dashboard_database_password = models.TextField(default='')
	dashboard_database_name = models.TextField(default='none')
	dashboard_excel_path = models.TextField(default='')
	dashboard_list_relation_data = models.TextField(default='{}')
	
	
	# def __str__(self):
		# return self.dashboard_id
	# def dashboard_id(self):
		# return self.dashboard_id
		
class test_scheduller(models.Model):
	scheduller_id = models.AutoField(primary_key=True)
	scheduller_datetime = models.IntegerField()
	
	def __str__(self):
		return self.scheduller_id
	
	def truncate(cls):
		with connection.cursor() as cursor:
			cursor.execute('TRUNCATE TABLE {} CASCADE'.format(cls._meta.db_table))