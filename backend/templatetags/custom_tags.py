#https://github.com/telminov/sw-django-utils/blob/master/djutils/templatetags/djutils.py
import json

from django import template
import sqlparse
import djutils

register = template.Library()

@register.filter('to_int')
def to_int(value):
	return int(value)
	
@register.filter('length_minus_one_to_string')
def length_minus_one_to_string(array_temp):
	return str(len(array_temp) - 1)

@register.filter('iso_to_date')
def iso_to_date(date_iso):
	return date_utils.iso_to_date(date_iso)


@register.filter('pretty_sql')
def pretty_sql(sql):
	try:
		sql = sqlparse.format(sql, reindent=True, keyword_case='upper')
		return sql
	except Exception:
		return sql


@register.filter('pretty_json')
def pretty_json(json_text):
	try:
		pretty_json_text = json.dumps(json_text, indent=4)
		return pretty_json_text
	except Exception:
		return json_text


@register.filter('get_value_from_dict')
def get_value_from_dict(dict_data, key):
	"""
	usage example {{ your_dict|get_value_from_dict:your_key }}
	"""
	if key:
		return dict_data.get(key)


@register.inclusion_tag('djutils/sort_th.html', takes_context=True)
def sort_th(context, sort_param_name, label):
	return {
		'is_current': context['sort_params'][sort_param_name]['is_current'],
		'is_reversed': context['sort_params'][sort_param_name]['is_reversed'],
		'url': context['sort_params'][sort_param_name]['url'],
		'label': label,
	}