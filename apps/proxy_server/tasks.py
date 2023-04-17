from apps import celery_app
from apps.proxy_server.models import Cidr, CidrGeo
# import pycountry
import ipaddress
import requests
from django.conf import settings


def get_ip_geo(ip):
    """
    获取IP地理位置
    :param ip:
    :return:
    """
    data = {}
    url = 'http://ipwho.is/{}'.format(ip)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            resp = response.json()
            data['ip'] = ip
            data['country'] = resp['country']
            data['country_code'] = resp['country_code']
            data['region'] = resp['region']
            data['region_code'] = resp['region_code']
            data['city'] = resp['city']
            data['post_code'] = resp['postal']
            return data
        else:
            return {}
    except Exception as e:
        print(e)
        return {}


@celery_app.task
def gen_geofeed_csv():
    '''
    生成geo csv 每日任务
    :return:
    '''
    cidrs = Cidr.objects.all()
    for cidr_i in cidrs:
        if not CidrGeo.objects.filter(cidr=cidr_i.cidr).exists():
            random_ip = ipaddress.IPv4Network(cidr_i.cidr).hosts().__next__()
            ip_info = get_ip_geo(random_ip)
            if ip_info:
                CidrGeo.objects.create(cidr=cidr_i.cidr, country=ip_info['country'],
                                       country_code=ip_info['country_code'], region=ip_info['region'],
                                       region_code=ip_info['region_code'], city=ip_info['city'], post_code=ip_info['post_code'])
    # 生成geo csv
    cidr_geos = CidrGeo.objects.all()
    settings.STATIC_ROOT
    csv_path = settings.STATIC_ROOT + '/geofeed.csv'
    with open(csv_path, 'w') as f:
        for cidr_geo in cidr_geos:
            f.write(cidr_geo.cidr + ',' + cidr_geo.country_code + ',' + cidr_geo.region_code +
                    ',' + cidr_geo.city + ',' + cidr_geo.post_code + '\n')
