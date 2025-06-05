import os,re,json,traceback,copy,random,string,time,redis,ast,requests,codecs
from django.shortcuts import render
from django.shortcuts import render
from django.http import StreamingHttpResponse
from django.db.models import Q
from django.http import HttpResponse,HttpResponseRedirect,JsonResponse
from django.template.context_processors import csrf
from urllib.parse import urlparse
from django.core.cache import cache
from django.conf import settings
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import os
import django
django.setup()
from .models import *
from .views_jmeterjmx import generate_jmx,body_request,body_request2,body_testplan,body_result,body_thread,body_thread2,body_head,body_cookie,generate_jmx2
from rest_framework import status
from urllib import parse
import urllib
import xml.etree.cElementTree as ET
from django.db import connection


from .util.parseHar import har_analyze
from .util.parseFile import upload_file
from .util.parseFile import download_file
from .util.fiddler2jmeter.FiddlerCharles2Jmeter import run
from optparse import OptionParser

from Autotestplat.celery import app
from .util.jmeter.csv import AggregateGraphReport
from djcelery.models import PeriodicTask, CrontabSchedule, IntervalSchedule
from .util.WeWork_Send_Msg import WeWork_Send_Msg

current_dir = os.getcwd()
jmxfile = os.path.join(current_dir, 'apache-jmeter-5.1.1/bin', 'apitest.jmx')
logfile = os.path.join(current_dir, 'autotest', 'test_out.log')
codefile= os.path.join(current_dir, 'autotest', 'code.jpg')
session = requests.Session()

@login_required
def apijmeter(request):
    username = request.session.get('user', '')
    if AuthUser.objects.filter(username=username).first().is_superuser == 1:
        interfaces = AutotestplatJmeterHistory.objects.filter().order_by('-id').all()
        product_all = AutotestplatProduct.objects.filter(delete_flag='N')
        product_name = ''
    else:
        user_product_id = AuthUser.objects.filter(username=username).first().last_name
        try:
            interfaces = AutotestplatJmeterHistory.objects.filter(product_id=user_product_id).order_by('-id').all()
        except:
            interfaces = AutotestplatJmeterHistory.objects.filter().order_by('-id').all()
        product_id = AuthUser.objects.filter(username=username).first().last_name
        product_name = AutotestplatProduct.objects.filter(id=product_id).first().product_name
        product_all = AutotestplatProduct.objects.filter(delete_flag='N')
    for i in interfaces:
        tmp_ids = AutotestplatProduct.objects.all().values_list().order_by('id')
        tmp = []
        for tmp_id in tmp_ids:
            tmp.append(tmp_id[0])
        if (i.product_id == None):
            count = 0
        else:
            count = tmp.count(int(i.product_id))
        if count > 0:
            product_name_tmp = AutotestplatProduct.objects.filter(id=int(i.product_id)).first().product_name
            i.product_id = product_name_tmp
    progress = AutotestplatInterfacePerformance.objects.filter(id=1).first().progress
    progress_total = AutotestplatInterfacePerformance.objects.filter(id=1).first().progress_total
    paginator = Paginator(interfaces, 10)
    num = len(interfaces)
    interval = IntervalSchedule.objects.all().order_by('-id')
    page = request.GET.get('page', 1)
    try:
        page_list = paginator.page(page)
    except PageNotAnInteger:
        page_list = paginator.page(1)
    except EmptyPage:
        page_list = paginator.page(paginator.num_pages)
    c = csrf(request)
    c.update({'page_list': page_list, 'interfaces': interfaces, 'type': type,'num':num,"product_name":product_name,"product_alls":product_all,"progress":progress,"progress_total":progress_total,'intervals':interval})
    return render(request, "interface_jmeter.html", c)

def report(request):
    return render(request,"output/index.html")

def searchjmeterInterface(request):
    if request.method == "POST":
        raw_data = request.body
        raw_data = json.loads(raw_data)
        key_words_name = raw_data['key_words_name']
        key_words_url = raw_data['key_words_url']
        interface_list1 = AutotestplatJmeterHistory.objects.filter(Q(newname__icontains=key_words_name),Q(type__icontains=key_words_url))
        id_list = []
        name_list = []
        url_list = []
        charger_list = []
        create_time_list = []
        run_time_list = []
        for rec in interface_list1:
            id_list.append(rec.id)
            name_list.append(rec.newname)
            url_list.append(rec.type)
            create_time_list.append(rec.create_time)
            run_time_list.append(rec.run_time)
            charger_list.append(rec.charger)
        interface_list2 = {'id_list': id_list,
                         'name_list': name_list,
                         'url_list': url_list,
                         'create_time_list': create_time_list,
                         'run_time_list': run_time_list,
                         'charger_list': charger_list,}
        return HttpResponse(json.dumps(interface_list2), content_type='application/json')

def generateJmeterFile(request):
    try:
        raw_data = request.body
        raw_data = json.loads(raw_data)
        id_list_login = raw_data['id_list_login']
        id_list_not_login = raw_data['id_list_not_login']
        num_bf = raw_data['num_bf']
        num_xh = raw_data['num_xh']
        num_sj = raw_data['num_sj']
        num_sj = str(int(num_sj)*60)
        mode = raw_data['mode']
        deal_cookie = raw_data['deal_cookie']
        public_list = AutotestplatParameter.objects.filter()
        keyword_list = ["{" + rec.keywords + "}" for rec in public_list]
        public_list1 = AutotestplatParameter.objects.filter(Q(type='con'))
        keyword_list1 = ["{" + rec.keywords + "}" for rec in public_list1]
        public_dict1 = {}
        for rec in public_list1:
            public_dict1[rec.keywords] = rec.value
        public_list2 = AutotestplatParameter.objects.filter(type='res').exclude(type='testplan')
        keyword_list2 = ["{" + rec.keywords + "}" for rec in public_list2]
        public_dict2 = {}
        for rec in public_list2:
            public_dict2[rec.keywords] = str((rec.left, rec.right, rec.index))
        public_list3 = AutotestplatParameter.objects.filter(Q(type='auth'))
        keyword_list3 = ["{" + rec.keywords + "}" for rec in public_list3]
        public_dict3 = {}
        for rec in public_list3:
            public_dict3[rec.keywords] = rec.value
        public_list4 = AutotestplatParameter.objects.filter(Q(type='env'))
        keyword_list4 = ["{" + rec.keywords + "}" for rec in public_list4]
        public_dict4 = {}
        for rec in public_list4:
            public_dict4[rec.keywords] = rec.value
        public_list5 = AutotestplatParameter.objects.filter(Q(type='var'))
        keyword_list5 = ["{" + rec.keywords + "}" for rec in public_list5]
        public_dict5 = {}
        for rec in public_list5:
            public_dict5[rec.keywords] = rec.value
        public_dict = {}
        public_dict.update(public_dict1)
        public_dict.update(public_dict2)
        public_dict.update(public_dict3)
        public_dict.update(public_dict4)
        public_dict.update(public_dict5)
        body_list = []
        id=''
        name=''
        for id in id_list_login:
            interface_list = AutotestplatInterfaceTestcase.objects.filter(id=str(id))
            for rec in interface_list:
                id = rec.id
                url = rec.url
                url2= url.replace('?','//%')
                parabody = rec.body
                parsed_uri = urlparse(url2)
                name = rec.name
                head = rec.head
                assertkey = rec.assert_keywords_old
                url_host = rec.url_host
                try:
                    if ("{" in url_host and "}" in url_host):
                        end_index = url_host.find("}")
                        key_url_host = url_host[:end_index + 1]
                        url_host = url_host.replace(key_url_host, public_dict[key_url_host.replace('{', '').replace('}', '').replace(' ', '')])
                except:
                    return HttpResponse('【ERROR】：url_host参数 ' + url_host + ' 有误，请重新修改 ')

                scheme = '{uri.scheme}'.format(uri=parsed_uri)
                # domain = '{uri.netloc}'.format(uri=parsed_uri)
                domain = url_host
                path = '{uri.path}'.format(uri=parsed_uri)
                path2 = path.replace('//%','?')
                if url_host.startswith('http://') or url_host.startswith('https://'):
                    host = domain.split(':')[1].replace('//', '')
                    if len(domain.split(':')) > 2:
                        port = domain.split(':')[2]
                    else:
                        port = ''
                else:
                    host = domain.split(':')[0]
                    if len(domain.split(':')) > 1:
                        port = domain.split(':')[1]
                    else:
                        port = ''
                head1 = eval(head)
                head_list1 = []
                for item, value in head1.items():
                    item1 = item
                    value1 = value
                    head1 = body_head(item1, value1)
                    head_list1.append(head1)
                head1 = ''.join(head_list1)
                body1 = body_request(str(id),name,host, port, path2, scheme, parabody,head1,assertkey,)
                body_list.append(body1)
                islogin = True
                start_interface_login(id)
                update_cookie = rec.update_cookie
                update_cookie = update_cookie.replace('{', '').replace('}', '')
        body1 = ''.join(body_list)
        body_thread1=''
        try:
            body_thread1 = body_thread(id,'1','1')
        except Exception:
            pass
        cookie=''
        body_list2 = []
        for id2 in id_list_not_login:
            interface_list2 = AutotestplatInterfaceTestcase.objects.filter(id=str(id2))
            for rec in interface_list2:
                id2 = rec.id
                url_host = rec.url_host
                try:
                    if ("{" in url_host and "}" in url_host):
                        end_index = url_host.find("}")
                        key_url_host = url_host[:end_index + 1]
                        url_host = url_host.replace(key_url_host, public_dict[key_url_host.replace('{', '').replace('}', '').replace(' ', '')])
                except:
                    return HttpResponse('【ERROR】：url_host参数 ' + url_host + ' 有误，请重新修改 ')
                url = rec.url
                url2 = url.replace('?', '//%')
                if ("{" in url and "}" in url):
                    end_index = url.find("}")
                    key_url = url[:end_index + 1]
                    url = url.replace(key_url, public_dict[key_url.replace('{', '').replace('}', '')])
                body = eval(rec.body)
                for bodykey in body.keys():
                    if(isinstance(body[bodykey],str) or isinstance(body[bodykey],list) or isinstance(body[bodykey],dict)):
                        for rec1 in keyword_list1:
                            if (rec1 in body[bodykey]):
                                if ('captcha' not in rec1):
                                    body[bodykey] = body[bodykey].replace(rec1, public_dict[
                                        rec1.replace('{', '').replace('}', '')])
                                else:
                                    is_login_api = True
                                    yanzheng_url = public_dict[rec1.replace('{', '').replace('}', '')]
                                    haha = request_get(yanzheng_url, {}, {}, 0)
                                    with open(codefile, 'wb') as f:
                                        f.write(haha.content)
                                    yanzheng = getcaptcha()
                                    body[bodykey] = yanzheng
                                    print_detail('【验证码】：', ','), print_detail(yanzheng)
                        for rec5 in keyword_list5:
                            if (rec5 in str(body[bodykey])):
                                try:
                                    var_name = public_dict[rec5.replace('{', '').replace('}', '')]
                                    var_value = str(eval(var_name))
                                    body = str(body).replace(rec5, var_name)
                                    body = str(body).replace(var_name, var_value)
                                    body = ast.literal_eval(body)
                                except Exception:
                                    error_info = traceback.format_exc()
                                    print(error_info)
                                    return HttpResponse(
                                        '【ERROR】：参数 ' + rec5 + ' 没有参数值，请确认系统参数设置是否正确，是否已执行返回 ' + rec5 + ' 的前置接口，以及确认Redis是否已启动')
                        for rec2 in keyword_list2:
                            if (rec2 in body[bodykey]):
                                try:
                                    body[bodykey] = body[bodykey].replace(rec2, cache.get(
                                        rec2.replace('{', '').replace('}', '')))
                                except Exception:
                                    error_info = traceback.format_exc()
                                    print(error_info)
                                    return HttpResponse('【ERROR】：参数 ' + rec2 + ' 没有参数值，请确认是否已执行返回 ' + rec2 + ' 的接口')
                        for rec3 in keyword_list3:
                            if (rec3 in body[bodykey]):
                                try:
                                    body[bodykey] = body[bodykey].replace(rec3, cache.get(
                                        rec3.replace('{', '').replace('}', '')).decode('utf-8'))
                                except Exception:
                                    error_info = traceback.format_exc()
                                    print(error_info)
                                    return HttpResponse(
                                        '【ERROR】：参数 ' + rec3 + ' 没有参数值，请确认系统参数设置是否正确，是否已执行返回 ' + rec3 + ' 的前置接口，以及确认Redis是否已启动')
                        if ('select' in body[bodykey]):
                            try:
                                sql = body[bodykey]
                                cursor = connection.cursor()
                                cursor.execute(sql)
                                data = cursor.fetchall()
                                print(u'查询的结果为： ', data[0][0])
                                body[bodykey] = str(data[0][0])
                            except Exception:
                                body[bodykey] = '【ERROR】：查询结果为空！'
                parabody = str(body)
                parsed_uri = urlparse(url2)
                name = rec.name
                head = rec.head
                assertkey = rec.assert_keywords_old
                scheme = '{uri.scheme}'.format(uri=parsed_uri)
                domain = url_host
                path = '{uri.path}'.format(uri=parsed_uri)
                path2 = path.replace('//%', '?')
                if url_host.startswith('http://') or url_host.startswith('https://'):
                    host = domain.split(':')[1].replace('//', '')
                    if len(domain.split(':')) > 2:
                        port = domain.split(':')[2]
                    else:
                        port = ''
                else:
                    host = domain.split(':')[0]
                    if len(domain.split(':')) > 1:
                        port = domain.split(':')[1]
                    else:
                        port = ''
                head2 = eval(head)
                head_list2 = []
                for item,value in head2.items():
                    item2 = item
                    value2 = value
                    if value2 == "{autotestplat}":
                        head2 = body_head(item2,str(cookie))
                    else:
                        head2 = body_head(item2, value2)
                    head_list2.append(head2)
                head2 = ''.join(head_list2)
                if(cookie):
                    cookie = eval(cookie)
                    cookie_list = []
                    cookie1 = body_cookie(cookie[1][0],cookie[1][1])
                    cookie_list.append(cookie1)
                    cookie2 = body_cookie(cookie[2][0], cookie[2][1])
                    cookie_list.append(cookie2)
                    cookie3 = body_cookie(cookie[3][0], cookie[3][1])
                    cookie_list.append(cookie3)
                    for item, value in cookie[0].items():
                        item2 = item
                        value2 = value
                        cookie = body_cookie(item2,value2)
                        cookie_list.append(cookie)
                    cookie = ''.join(cookie_list)
                else:
                    cookie = ''
                body2 = body_request2(str(id2), name,host, port, path2, scheme, parabody, cookie,head2,assertkey)
                body_list2.append(body2)
                islogin = False
        body2 = ''.join(body_list2)
        body_thread22=''
        if num_xh == '0':
            num_xh = '-1'
        else:
            num_xh = num_xh
        try:
            body_thread22 = body_thread2(id2,num_bf,num_xh,num_sj)
        except Exception:
            pass
        body3 = body_thread1 + str(body1) + '</hashTree>\n' + body_thread22 + str(body2)
        body4 = body_thread22 + str(body1) + str(body2)
        if mode=='多用户':
            generate_jmx(name,host, port, path2, scheme, body4,)
        else:
            generate_jmx2(name,host, port, path2, scheme, body3,)
        return HttpResponse("success")
    except Exception:
        traceback.print_exc()
        return HttpResponse("failed")

def prepareJmeter(request):
    try:
        bin_file = "cd "+current_dir+"/autotest/apache-jmeter-5.1.1/bin"
        rm_report_file = "rmdir /s/q "+current_dir.replace('/','\\')+"\\autotest\\static\\output\\ "
        os.system(bin_file)
        # os.system(rm_report_file)
        return HttpResponse("success")
    except Exception:
        traceback.print_exc()
        return HttpResponse("failed")


def getFileName1(path, suffix):
    # 获取指定目录下的所有指定后缀的文件名
    input_template_All = []
    try:
        f_list = os.listdir(path)  # 返回文件名
        for i in f_list:
            # os.path.splitext():分离文件名与扩展名
            if os.path.splitext(i)[1] == suffix:
                input_template_All.append(i)
                # print(i)
    except:
        # path_str =
        aa = os.path.split(path)
        input_template_All=aa[1].split(',')
        # print(aa[1])

    return input_template_All

def runJmeter(request):
    from celery.result import AsyncResult
    username = request.session.get('user', '')
    contents = json.loads(request.body.decode()).get('contents', 0)
    # get方式 contents = urllib.parse.unquote(request.GET.get('contents'))
    type = json.loads(request.body.decode()).get('type', 0)
    ip = json.loads(request.body.decode()).get('ip', 0)
    # get方式 type = urllib.parse.unquote(request.GET.get('type'))
    id_list = json.loads(request.body.decode()).get('id_list', 0)
    # runtask = 'startTestJmeter'+'('+str(username)+','+str(contents)+','+str(type)+','+str(ip)+','+str(id_list)+')'
    # eval(runtask)

    # runtask = startTestJmeter.delay(username, contents, type, ip, id_list)
    # return JsonResponse(runtask.result, safe=False)

    runtask = startTestJmeter.delay(username, contents, type, ip, id_list)

    # 异步获取任务返回值
    # for i in range(9999)://没用
    # while True: //无限循环
    #     time.sleep(1)
    #     async_task = AsyncResult(id=runtask.id ,app=app)
    #     print("async_task.id" ,async_task.id)
    #     # 判断异步任务是否执行成功
    #     if async_task.successful():
    #         # 获取异步任务的返回值
    #         result = async_task.get()
    #         print(result)
    #         print("执行成功")
    #         break
    #     else:
    #         print("任务还未执行完成")



    result = {"status": status.HTTP_200_OK, "runtask_id": runtask.id}
    return JsonResponse(result, safe=False)

    # runtask = startTestJmeter(username, contents, type, ip, id_list)
    # return HttpResponse(200)

@app.task
def startTestJmeter(username,contents,type,ip,id_list):
    # print(id_list)
    #import platform
    # import shutil
    try:
        test_time = time.strftime("%Y-%m-%d %H:%M:%S")
        # path = current_dir+"/apache-jmeter-5.1.1/data/"+contents+"/"
        path1 = current_dir+"/data/"+contents
        path = os.path.split(path1)[0] + '/'
        suffix = ".jmx"
        # if not os.path.exists(path):  # 判断所在目录下是否有该文件名的文件夹
        #     os.mkdir(path)  # 创建多级目录用mkdirs，单击目录mkdir
        # else:
        #     print('the file exists')
        report_id_list=[]
        for file in getFileName1(path1, suffix):
            time.sleep(600) #固定定时器影响取样数
            report_id = str(datetime.now().strftime("%Y%m%d%H%M%S%f"))
            # print("file:"+file)
            # jmx_file = file
          #  "jmeter -n -q user-csx.properties -R 10.72.56.87:1099,10.17.18.162:1099 -t D:\PY\Autotest1\apache-jmeter-5.1.1\data\乘车bom\bom.jmx -l D:\PY\Autotest1\apache-jmeter-5.1.1\data\test.jtl"

            # print(report_file)
        #    report_result_file = "d: && cd  "+current_dir+"/autotest/static/data/ && java -jar AggregateReport-2.0.jar "+report_id+".jtl 1 "+report_id
            if type == "csv":
                report_file = current_dir + "/apache-jmeter-5.1.1/bin/jmeter -n -R " + ip +":1099 -q " + current_dir + "/apache-jmeter-5.1.1/bin/user-" + type + ".properties   -t " + path + file + " -l " + current_dir + "/autotest/static/data/" + report_id + ".jtl && java -jar " + current_dir + "/autotest/static/data/Report-2.0.jar " + current_dir + "/autotest/static/data/" + report_id + ".jtl 1 " + current_dir + "/autotest/static/data/" + report_id
            elif type == "csv-w":
                import socket

                ip_address_list = ['10.3.204.222', '10.3.210.116', '10.43.138.30','10.43.119.221','10.43.119.61']

                def is_port_open(ip_address_list, port):
                    ip_address_ok = ""
                    for ip_address in ip_address_list:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        result = sock.connect_ex((ip_address, port))
                        if result == 0:
                            # print(ip_address + 'Port 1099 is open!')
                            ip_address_ok += ip_address + ':1099' + ','
                        else:
                            print(ip_address + 'Port 1099 is closed!')
                        sock.close()
                    return ip_address_ok

                def read_jmeter_properties(file_path):
                    """读取 jmeter.properties 文件"""
                    properties = {}
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith('#'):
                                continue  # 忽略空行和注释行
                            key, value = line.split('=', 1)
                            properties[key.strip()] = value.strip()
                    return properties

                def write_jmeter_properties(file_path, properties):
                    """将修改后的 properties 写回文件"""
                    with open(file_path, 'w', encoding='utf-8') as f:
                        for key, value in properties.items():
                            f.write(f"{key}={value}\n")

                # 示例：读取、修改、写回
                jmeter_properties_path = "/code/apache-jmeter-5.1.1/bin/user-csv-w.properties"

                # 读取配置
                props = read_jmeter_properties(jmeter_properties_path)
                # print("当前配置：", props['remote_hosts'])

                # 修改某个参数
                props['remote_hosts'] = is_port_open(ip_address_list, 1099)

                # 写回文件
                write_jmeter_properties(jmeter_properties_path, props)
                # print("配置已修改！")

                report_file = current_dir + "/apache-jmeter-5.1.1/bin/jmeter -n -r -q " + current_dir + "/apache-jmeter-5.1.1/bin/user-" + type + ".properties   -t " + path + file + " -l " + current_dir + "/autotest/static/data/" + report_id + ".jtl && java -jar " + current_dir + "/autotest/static/data/Report-2.0.jar " + current_dir + "/autotest/static/data/" + report_id + ".jtl 1 " + current_dir + "/autotest/static/data/" + report_id
            else:
                report_file = current_dir + "/apache-jmeter-5.1.1/bin/jmeter -n -R " + ip +":1099 -q " + current_dir + "/apache-jmeter-5.1.1/bin/user-xml.properties  -t " + path + file + " -l " + current_dir + "/autotest/static/data/" + report_id + ".jtl"
            print(report_file)
            time.sleep(60)
            os.system(report_file)
            #AggregateGraphReport.AggregateGraphReport.main([current_dir + "/autotest/static/data/" + report_id2 + ".jtl", "1", current_dir + "/autotest/static/data/" + report_id2])
            if type == 'csv':
                user_product_id = AuthUser.objects.filter(username=username).first().last_name
                # product_name = AutotestplatProduct.objects.filter(id=user_product_id).first().product_name
                result_info = AutotestplatTestplanjmeterResult(report_id=report_id,
                                                              product_id=user_product_id,
                                                              product_name=contents,
                                                              suit_id=report_id,
                                                              suit_name=report_id,
                                                              jmx_name=file,
                                                              suit_interface_id=report_id,
                                                              result='true',
                                                              date_time=test_time
                                                               )

                result_info.save()
                sql = "select t2.interface_name,t2.suit_id,t2.suit_name,t2.mode,t2.url,t2.body,t2.assert_keywords_old from autotestplat_testplan_jmeter_result t2  where t2.suit_id=" + str(
                    report_id) + " order by t2.product_id"
                cursor = connection.cursor()
                aa = cursor.execute(sql)
                interface_list = cursor.fetchmany(aa)
                interfacepass = AutotestplatTestplanjmeterResult.objects.filter(report_id=report_id).filter(
                    result="true").count()
                interfaceall = len(interface_list)
                testcase_pass_pers = '{:.0%}'.format(interfacepass / interfaceall)
                AutotestplatTestplanjmeterResult.objects.filter(report_id=report_id).update(
                    pass_pers=testcase_pass_pers)
                report_id_list.append(report_id)
            else:
                tree = ET.parse(current_dir+"/autotest/static/data/"+report_id+".jtl")
                root = tree.getroot()
                result_list = readxml(root, "httpSample", 1, 1, 1)
                for result in result_list:
                    user_product_id = AuthUser.objects.filter(username=username).first().last_name
                    result_info = AutotestplatTestplanjmeterResult(report_id=report_id,
                                                                      product_id=user_product_id,
                                                                      product_name=contents,
                                                                      suit_id=report_id,
                                                                      suit_name=report_id,
                                                                      jmx_name=file,
                                                                      suit_interface_id=report_id,
                                                                      interface_name=result[0],
                                                                      url=result[1],
                                                                      body=result[4],
                                                                      mode=result[2],
                                                                      assert_keywords_old=result[7],
                                                                      response_time=result[9],
                                                                      task_mode="定时任务",
                                                                      response=result[5],
                                                                      result=result[8],
                                                                      date_time=test_time)
                    result_info.save()
                sql = "select t2.interface_name,t2.suit_id,t2.suit_name,t2.mode,t2.url,t2.body,t2.assert_keywords_old from autotestplat_testplan_jmeter_result t2  where t2.suit_id=" + str(
                    report_id) + " order by t2.product_id"
                cursor = connection.cursor()
                aa = cursor.execute(sql)
                interface_list = cursor.fetchmany(aa)
                interfacepass = AutotestplatTestplanjmeterResult.objects.filter(report_id=report_id).filter(
                    result="true").count()
                interfaceall = len(interface_list)
                testcase_pass_pers = '{:.0%}'.format(interfacepass / interfaceall)
                AutotestplatTestplanjmeterResult.objects.filter(report_id=report_id).update(
                    pass_pers=testcase_pass_pers)
                report_id_list.append(report_id)

            # return HttpResponse("success")
        result = {"status": status.HTTP_200_OK, "report_id": report_id_list}
        # return JsonResponse(result, safe=False)
        WeWork_Send_Msg().send_txt(json.dumps(report_id_list,ensure_ascii=False), "9d334184-6b20-45d0-80dd-d5587ac0635e")
        return result
    except Exception:
        traceback.print_exc()
        return HttpResponse("failed")


def showProgress(request):
    if request.method == "POST":
        raw_data = request.body
        raw_data = json.loads(raw_data)
        instance = AutotestplatInterfacePerformance.objects.filter(id=1)
        if instance:
            progress = raw_data['progress']
            progress_total = raw_data['progress_total']
        else:
            progress = 1
            progress_total = 1
        AutotestplatInterfacePerformance.objects.filter(id=1).update(progress=progress,progress_total=progress_total)
    return HttpResponse("success")


def start_interface_login(id1):
    public_list = AutotestplatParameter.objects.all()
    keyword_list = ["{"+rec.keywords+"}" for rec in public_list]
    public_list1 = AutotestplatParameter.objects.filter(Q(type='con'))
    keyword_list1 = ["{"+rec.keywords+"}" for rec in public_list1]
    public_dict1 = {}
    for rec in public_list1:
        public_dict1[rec.keywords] = rec.value
    public_list2 = AutotestplatParameter.objects.exclude(type='res').exclude(type='testplan')
    keyword_list2 = ["{"+rec.keywords+"}" for rec in public_list2]
    public_dict2 = {}
    for rec in public_list2:
        public_dict2[rec.keywords] = str((rec.left,rec.right,rec.index))
    public_list3 = AutotestplatParameter.objects.filter(Q(type='auth'))
    keyword_list3 = ["{"+rec.keywords+"}" for rec in public_list3]
    public_dict3 = {}
    for rec in public_list3:
        public_dict3[rec.keywords] = rec.value
    public_list4 = AutotestplatParameter.objects.filter(Q(type='env'))
    keyword_list4 = ["{" + rec.keywords + "}" for rec in public_list4]
    public_dict4 = {}
    for rec in public_list4:
        public_dict4[rec.keywords] = rec.value
    public_list5 = AutotestplatParameter.objects.filter(Q(type='var'))
    keyword_list5 = ["{" + rec.keywords + "}" for rec in public_list5]
    public_dict5 = {}
    for rec in public_list5:
        public_dict5[rec.keywords] = rec.value
    public_dict = {}
    public_dict.update(public_dict1)
    public_dict.update(public_dict2)
    public_dict.update(public_dict5)
    public_dict.update(public_dict4)
    f_handler = open(logfile, 'w')
    f_handler.truncate()
    f_handler.close()
    interfaces = AutotestplatInterfaceTestcase.objects.filter(id=id1)[0]
    url_host = interfaces.url_host
    try:
        if ("{" in url_host and "}" in url_host):
            end_index = url_host.find("}")
            key_url_host = url_host[:end_index + 1]
            url_host = url_host.replace(key_url_host,public_dict[key_url_host.replace('{', '').replace('}', '').replace(' ', '')])
    except:
        return HttpResponse('【ERROR】：url_host参数 ' + url_host + ' 有误，请重新修改 ')
    url = interfaces.url
    if("{" in url and "}" in url):
        end_index = url.find("}")
        key_url = url[:end_index+1]
        url = url.replace(key_url,public_dict[key_url.replace('{','').replace('}','')])
    url = url_host+url
    head = eval(interfaces.head)
    for rec in head.keys():
        if(head[rec] in keyword_list1):
            head[rec] = public_dict[head[rec].replace('{','').replace('}','')]
        elif(head[rec] in keyword_list2):
            try:
                head[rec] = cache.get(head[rec].replace('{','').replace('}',''))
            except Exception:
                error_info = traceback.format_exc()
                print(error_info)
                return HttpResponse('【ERROR】：参数 '+head[rec]+' 没有参数值，请确认是否已执行返回 '+head[rec]+' 的接口')
    is_login_api = False
    n = 0
    while (n < 5):
        body = eval(interfaces.body)
        for rec in body.keys():
            if(isinstance(body[rec],str)):
                for rec1 in keyword_list1:
                    if(rec1 in body[rec]):
                        if('captcha' not in rec1):
                            body[rec] = body[rec].replace(rec1, public_dict[rec1.replace('{','').replace('}','')])
                        else:
                            is_login_api = True
                            yanzheng_url = public_dict[rec1.replace('{','').replace('}','')]
                            haha = request_get(yanzheng_url,{},{},0)
                            with open(logfile,'wb') as f:
                                f.write(haha.content)
                            yanzheng = getcaptcha()
                            body[rec] = yanzheng
                            print_detail('【验证码】：',','),print_detail(yanzheng)
                for rec5 in keyword_list5:
                    if (rec5 in str(body[rec])):
                        try:
                            var_name = public_dict[rec5.replace('{', '').replace('}', '')]
                            var_value = str(eval(var_name))
                            body = str(body).replace(rec5, var_name)
                            body = str(body).replace(var_name, var_value)
                            body = ast.literal_eval(body)
                        except Exception:
                            error_info = traceback.format_exc()
                            print(error_info)
                            return HttpResponse('【ERROR】：参数 ' + rec5 + ' 没有参数值，请确认系统参数设置是否正确，是否已执行返回 ' + rec5 + ' 的前置接口，以及确认Redis是否已启动')
                for rec2 in keyword_list2:
                    if(rec2 in body[rec]):
                        try:
                            body[rec] = body[rec].replace(rec2, cache.get(rec2.replace('{','').replace('}','')))
                        except Exception:
                            error_info = traceback.format_exc()
                            print(error_info)
                            return HttpResponse('【ERROR】：参数 '+rec2+' 没有参数值，请确认是否已执行返回 '+rec2+' 的接口')
                for rec3 in keyword_list3:
                    if(rec3 in body[rec]):
                        pass
                if('select' in body[rec]):
                    try:
                        sql = body[rec]
                        cursor = connection.cursor()
                        cursor.execute(sql)
                        data = cursor.fetchall()
                        print(u'查询的结果为： ',data[0][0])
                        body[rec] = data[0][0]
                    except Exception:
                        body[rec] = '【ERROR】：查询结果为空！'
        mode = interfaces.mode
        body_format = interfaces.body_format
        response,cookie = interface_test_start(url,body,head,mode,body_format,True)
        update_cookie = interfaces.update_cookie
        if('{' in update_cookie and '}' in update_cookie):
            for rec in keyword_list1:
                if(rec == update_cookie):
                    cookie_status1 = public_para1.objects.filter(keywords=rec.replace('{','').replace('}','')).update(value=cookie)
                    print(cookie_status1, ' update success!')
                    break
        public_resp = AutotestplatParameter.objects.filter(module_id=int(id1)).exclude(type='testplan')
        if(str(public_resp) != '[]'):
            for rec in public_resp:
                left = rec.left
                right = rec.right
                index = int(rec.index)
                reg = left+'.+?'+right
                result_all = re.findall(reg,response)
                try:
                    result_tmp = result_all[index]
                    start = len(left)
                    end = len(result_tmp) - len(right)
                    result = result_tmp[start:end]
                    print(rec.keywords,'匹配结果为：',result)
                    cache.set(rec.keywords, result, timeout=3600)
                    print_detail('\n接口返回关键字： '+rec.keywords+'，匹配第'+str(index+1)+'个        '+left+right+'       ，值为：'+result)
                except Exception:
                    error_info = traceback.format_exc()
                    print(error_info)
                    print((rec.keywords,left,right,index),' 在返回结果中未匹配到')
        is_new = interfaces.assert_use_new
        if(is_new == '1'):
            assert_body = eval(interfaces.assert_body)
            for rec in assert_body.keys():
                if(isinstance(assert_body[rec],str)):
                    for rec1 in keyword_list1:
                        if(rec1 in assert_body[rec]):
                            assert_body[rec] = assert_body[rec].replace(rec1, public_dict[rec1.replace('{','').replace('}','')])
                    for rec2 in keyword_list2:
                        if(rec2 in assert_body[rec]):
                            try:
                                assert_body[rec] = assert_body[rec].replace(rec2, cache.get(rec2.replace('{','').replace('}','')))
                            except Exception:
                                error_info = traceback.format_exc()
                                print(error_info)
                                return HttpResponse('【ERROR】：参数 '+rec2+' 没有参数值，请确认是否已执行返回 '+rec2+' 的接口')
                    for rec3 in keyword_list3:
                        if(rec3 in assert_body[rec]):
                            pass
                    if('select' in assert_body[rec]):
                        try:
                            sql = assert_body[rec]
                            cursor = connection.cursor()
                            cursor.execute(sql)
                            data = cursor.fetchall()
                            print(u'查询的结果为： ',data[0][0])
                            assert_body[rec] = data[0][0]
                        except Exception:
                            assert_body[rec] = '【ERROR】：查询结果为空！'
            assert_keywords = interfaces.assert_keywords
            for rec1 in keyword_list1:
                if(rec1 in assert_keywords):
                    assert_keywords = assert_keywords.replace(rec1, public_dict[rec1.replace('{','').replace('}','')])
            for rec2 in keyword_list2:
                if(rec2 in assert_keywords):
                    try:
                        assert_keywords = assert_keywords.replace(rec2, cache.get(rec2.replace('{','').replace('}','')))
                    except Exception:
                        error_info = traceback.format_exc()
                        print(error_info)
                        return HttpResponse('【ERROR】：参数 '+rec2+' 没有参数值，请确认是否已执行返回 '+rec2+' 的接口')
            if('select' in assert_keywords):
                sql = assert_keywords
                cursor = connection.cursor()
                cursor.execute(sql)
                data = cursor.fetchall()
                print(u'查询的结果为： ',data[0][0])
                assert_keywords = data[0][0]
            is_contain = interfaces.assert_keywords_is_contain
            assert_result = assert_test(assert_keywords,is_contain,assert_body_format,True)
        else:
            assert_keywords_old = interfaces.assert_keywords_old
            for rec1 in keyword_list1:
                if(rec1 in assert_keywords_old):
                    assert_keywords_old = assert_keywords_old.replace(rec1, public_dict[rec1.replace('{','').replace('}','')])
            for rec2 in keyword_list2:
                if(rec2 in assert_keywords_old):
                    try:
                        assert_keywords_old = assert_keywords_old.replace(rec2, cache.get(rec2.replace('{','').replace('}','')))
                    except Exception:
                        error_info = traceback.format_exc()
                        print(error_info)
                        return HttpResponse('【ERROR】：参数 '+rec2+' 没有参数值，请确认是否已执行返回 '+rec2+' 的接口')
            if('select' in assert_keywords_old):
                sql = assert_keywords_old
                cursor = connection.cursor()
                cursor.execute(sql)
                data = cursor.fetchall()
                print(u'查询的结果为： ',data[0][0])
                assert_keywords_old = data[0][0]
            assert_result = assert_test_old(response,assert_keywords_old,True)
        if(is_login_api == True):
            if(assert_result != 0):
                n += 1
            elif(assert_result == 0):
                break
        else:
            break
    File = logfile
    File1 = open(File,'r',encoding='utf-8')
    test_log = File1.readlines()
    test_log = str(test_log)
    test_log = test_log.replace('<','[').replace('>',"]")
    test_log = eval(test_log)
    return HttpResponse(test_log)

def interface_test_start(url,body,head,mode,body_format,is_out):
    try:
        if(mode == 'POST' or mode == 'post'):
            response,cookie = Method_POST(url,body,head,body_format,is_out)
        elif(mode == 'GET' or mode == 'get'):
            response,cookie = Method_GET(url,body,head,body_format,is_out)
        elif(mode == 'PUT' or mode == 'put'):
            response,cookie = Method_PUT(url,body,head,body_format,is_out)
        elif (mode == 'DELETE' or mode == 'delete'):
            response, cookie = Method_DELETE(url, body, head, body_format, is_out)
        elif (mode == 'PATCH' or mode == 'patch'):
            response, cookie = Method_PATCH(url, body, head, body_format, is_out)
        elif (mode == 'HEAD' or mode == 'head'):
            response, cookie = Method_HEAD(url, body, head, body_format, is_out)
        elif (mode == 'OPTIONS' or mode == 'options'):
            response, cookie = Method_OPTIONS(url, body, head, body_format, is_out)
        print_log('')
        return response,cookie
    except Exception:
        error_info = traceback.format_exc()
        print_log(error_info)
        return 1

def request_post(url, body, head, body_format):
    if (body_format == 'JSON'):
         body = json.dumps(body)
    else:
        keys = body.keys()
        for rec in keys:
            if ('[{' in str(body[rec]) and '}]' in str(body[rec])):
                body = json.dumps(body)
                break
    r = session.post(url, body, headers=head)
    return r

def request_get(url, body, head, body_format):
    if (body_format == 'JSON'):
        body = json.dumps(body)
    r = session.get(url, params=body, headers=head)
    return r

def request_put(url, body, head, body_format):
    if (body_format == 'JSON'):
        body = json.dumps(body)
    r = session.put(url, params=body, headers=head)
    return r

def request_delete(url, body, head, body_format):
    if (body_format == 'JSON'):
        body = json.dumps(body)
    r = session.delete(url, json=body, headers=head)
    return r

def request_patch(url, body, head, body_format):
    if (body_format == 'JSON'):
        body = json.dumps(body)
    r = session.patch(url, json=body, headers=head)
    return r

def request_head(url, body, head, body_format):
    if (body_format == 'JSON'):
        body = json.dumps(body)
    r = session.head(url, json=body, headers=head)
    return r

def request_options(url, body, head, body_format):
    if (body_format == 'JSON'):
        body = json.dumps(body)
    r = session.options(url, json=body, headers=head)
    return r

def Method_POST(url, body, head, body_format, is_out=True):
    starttime = datetime.now()
    r = request_post(url, body, head, body_format)
    endtime = datetime.now()
    response_time = (endtime - starttime).total_seconds()
    if (is_out == True):
        print_log('【请求URL】：', ','), print_log(r.url)
        print_log('【请求head】：', ','), print_log(
            json.dumps(head, sort_keys=True).encode().decode('raw_unicode_escape'))
        print_log('【请求参数】：', ','), print_log(body)
    response = r.text
    cookie = '; '.join(['='.join(rec) for rec in session.cookies.items()])
    print_log('【Cookies】：', ','), print_log(cookie)
    if (is_out == True):
        print_log('\n【响应状态码】：', ','), print_log(str(r.status_code), ','), print_log('    ' + str(r.reason))
        print_log('【响应数据】：', ','), print_log(str(response))
        print_log('【响应时间】：', ','), print_log(str(response_time) + " 秒", ',')
    return response, cookie

def Method_GET(url, body, head, body_format, is_out=True):
    starttime = datetime.now()
    r = request_get(url, body, head, body_format)
    endtime = datetime.now()
    response_time = (endtime - starttime).total_seconds()
    if (is_out == True):
        print_log('【请求URL】：', ','), print_log(r.url)
        print_log('【请求head】：', ','), print_log(
            json.dumps(head, sort_keys=True).encode().decode('raw_unicode_escape'))
        print_log('【请求参数】：', ','), print_log(body)
    response = r.text
    cookie = '; '.join(['='.join(rec) for rec in session.cookies.items()])
    print_log('【Cookies】：', ','), print_log(cookie)
    if (is_out == True):
        print_log('\n【响应状态码】：', ','), print_log(str(r.status_code), ','), print_log('    ' + str(r.reason))
        print_log('【响应数据】：', ','), print_log(response)
        print_log('【响应时间】：', ','), print_log(str(response_time) + " 秒", ',')
    return response, cookie

def Method_PUT(url, body, head, body_format, is_out=True):
    starttime = datetime.now()
    r = request_put(url, body, head, body_format)
    endtime = datetime.now()
    response_time = (endtime - starttime).total_seconds()
    if (is_out == True):
        print_log('【请求URL】：', ','), print_log(r.url)
        print_log('【请求head】：', ','), print_log(json.dumps(head, sort_keys=True).encode().decode('raw_unicode_escape'))
        print_log('【请求参数】：', ','), print_log(body)
    response = r.text
    cookie = '; '.join(['='.join(rec) for rec in session.cookies.items()])
    print_log('【Cookies】：', ','), print_log(cookie)
    if (is_out == True):
        print_log('\n【响应状态码】：', ','), print_log(str(r.status_code), ','), print_log('    ' + str(r.reason))
        print_log('【响应数据】：', ','), print_log(response)
        print_log('【响应时间】：', ','), print_log(str(response_time) + " 秒")
    return response, cookie

def Method_DELETE(url, body, head, body_format, is_out=True):
    starttime = datetime.now()
    r = request_delete(url, body, head, body_format)
    endtime = datetime.now()
    response_time = (endtime - starttime).total_seconds()
    if (is_out == True):
        print_log('【请求URL】：', ','), print_log(r.url)
        print_log('【请求head】：', ','), print_log(json.dumps(head, sort_keys=True).encode().decode('raw_unicode_escape'))
        print_log('【请求参数】：', ','), print_log(body)
    response = r.text
    cookie = '; '.join(['='.join(rec) for rec in session.cookies.items()])
    print_log('【Cookies】：', ','), print_log(cookie)
    if (is_out == True):
        print_log('\n【响应状态码】：', ','), print_log(str(r.status_code), ','), print_log('    ' + str(r.reason))
        print_log('【响应数据】：', ','), print_log(response)
        print_log('【响应时间】：', ','), print_log(str(response_time) + " 秒")
    return response, cookie

def Method_PATCH(url, body, head, body_format, is_out=True):
    starttime = datetime.now()
    r = request_patch(url, body, head, body_format)
    endtime = datetime.now()
    response_time = (endtime - starttime).total_seconds()
    if (is_out == True):
        print_log('【请求URL】：', ','), print_log(r.url)
        print_log('【请求head】：', ','), print_log(json.dumps(head, sort_keys=True).encode().decode('raw_unicode_escape'))
        print_log('【请求参数】：', ','), print_log(body)
    response = r.text
    cookie = '; '.join(['='.join(rec) for rec in session.cookies.items()])
    print_log('【Cookies】：', ','), print_log(cookie)
    if (is_out == True):
        print_log('\n【响应状态码】：', ','), print_log(str(r.status_code), ','), print_log('    ' + str(r.reason))
        print_log('【响应数据】：', ','), print_log(response)
        print_log('【响应时间】：', ','), print_log(str(response_time) + " 秒")
    return response, cookie

def Method_HEAD(url, body, head, body_format, is_out=True):
    starttime = datetime.now()
    r = request_head(url, body, head, body_format)
    endtime = datetime.now()
    response_time = (endtime - starttime).total_seconds()
    if (is_out == True):
        print_log('【请求URL】：', ','), print_log(r.url)
        print_log('【请求head】：', ','), print_log(json.dumps(head, sort_keys=True).encode().decode('raw_unicode_escape'))
        print_log('【请求参数】：', ','), print_log(body)
    response = r.text
    cookie = '; '.join(['='.join(rec) for rec in session.cookies.items()])
    print_log('【Cookies】：', ','), print_log(cookie)
    if (is_out == True):
        print_log('\n【响应状态码】：', ','), print_log(str(r.status_code), ','), print_log('    ' + str(r.reason))
        print_log('【响应数据】：', ','), print_log(response)
        print_log('【响应时间】：', ','), print_log(str(response_time) + " 秒")
    return response, cookie

def Method_OPTIONS(url, body, head, body_format, is_out=True):
    starttime = datetime.now()
    r = request_options(url, body, head, body_format)
    endtime = datetime.now()
    response_time = (endtime - starttime).total_seconds()
    if (is_out == True):
        print_log('【请求URL】：', ','), print_log(r.url)
        print_log('【请求head】：', ','), print_log(json.dumps(head, sort_keys=True).encode().decode('raw_unicode_escape'))
        print_log('【请求参数】：', ','), print_log(body)
    response = r.text
    cookie = '; '.join(['='.join(rec) for rec in session.cookies.items()])
    print_log('【Cookies】：', ','), print_log(cookie)
    if (is_out == True):
        print_log('\n【响应状态码】：', ','), print_log(str(r.status_code), ','), print_log('    ' + str(r.reason))
        print_log('【响应数据】：', ','), print_log(response)
        print_log('【响应时间】：', ','), print_log(str(response_time) + " 秒")
    return response, cookie


def assert_is_success(result,assert_keywords,is_contain,is_out = True):
    if(is_contain == '1'):
        print_log('\n【断言】： ' + assert_keywords)
        if(assert_keywords in result):
            if(is_out == True):
                print_log('【测试结果】： 测试通过')
            else:
                print_log('测试结果： 测试通过')
            return 0
        else:
            if(is_out == True):
                print_log('【测试结果】： 测试失败，断言不匹配')
            else:
                print_log('测试结果： 测试失败，断言不匹配')
            return 1
    elif(is_contain == '0'):
        print_log('\n【断言】： ' + assert_keywords)
        if(assert_keywords not in result):
            if(is_out == True):
                print_log('【测试结果】： 测试通过')
            else:
                print_log('测试结果： 测试通过')
            return 0
        else:
            if(is_out == True):
                print_log('【测试结果】： 测试失败，断言不匹配')
            else:
                print_log('测试结果： 测试失败，断言不匹配')
            return 1

def assert_test_old(response,assert_keywords_old,is_out):
    try:
        assert_keywords = assert_keywords_old.replace(' ','').replace('\n','').replace('\t','').replace('\r','')
        result = response.replace(' ','').replace('\n','').replace('\t','').replace('\r','')
        assert_result = assert_is_success(result,assert_keywords,'1',is_out)
        print_log('')
        return assert_result
    except Exception:
        error_info = traceback.format_exc()
        print_log(error_info)
        return 2

def print_log(var1, HH=True):
    File = logfile
    File1 = open(File, 'a', encoding='utf-8')
    if (HH == ','):
        print(var1, )
        File1.write(var1)
    else:
        print(var1)
        File1.write(str(var1) + '\n')
    File1.close()
    pass


def websocket(port):
    import socket
    from struct import unpack

    sockServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockServer.bind(('', int(port)))
    sockServer.listen(1)
    conn,addr = sockServer.accept()
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
    conn.ioctl(socket.SIO_KEEPALIVE_VALS,
               (1,  # 开启保活机制
                1 * 1000,  # 1分钟后如果对方还没有反应，开始探测连接是否存在
                1 * 1000)  # 60秒钟探测一次，默认探测10次，失败则断开
               )
    while True:
        data_length = conn.recv(4)
        if not data_length:
            break
        data_length = unpack('i', data_length)[0]
        data = conn.recv(data_length).decode()
        print(data)


def readxml(xmlObject, checkString, num, featureIndex, storyIndex):
    result_list = []
    for children in xmlObject:
        result = {}
        try:
            if num == 1 and children.attrib['sby'] != "0":
                featureIndexStr = '#' + str(featureIndex) + " " if featureIndex >= 10 else '#0' + str(
                    featureIndex) + " "
                result["feature"] = featureIndexStr + children.attrib['lb']
                featureIndex += 1
            if num >= 2 and children.tag == "sample":
                storyIndexStr = '#' + str(storyIndex) + " " if storyIndex >= 10 else '#0' + str(
                    storyIndex) + " "
                result["story"] = storyIndexStr + children.attrib['lb']
                storyIndex += 1
        except:
            pass
        if children.tag == checkString:
            result['case_name'] = children.attrib['lb']
            result['result'] = children.attrib['s']
            result['response_time'] = children.attrib['t']
            for httpSampleChildren in children:
                result[httpSampleChildren.tag] = httpSampleChildren.text
                if httpSampleChildren.tag == 'assertionResult':
                    for assertionResultChildren in httpSampleChildren:
                        result[assertionResultChildren.tag] = assertionResultChildren.text
            feature = result['feature'] if "feature" in result else None
            story = result['story'] if 'story' in result else None
            case_name = result['case_name'] if 'case_name' in result else None
            URL = result['java.net.URL'] if 'java.net.URL' in result else None
            method = result['method'] if 'method' in result else None
            requestHeader = result['requestHeader'] if 'requestHeader' in result else None
            queryString = result['queryString'] if 'queryString' in result else None
            responseData = result['responseData'] if 'responseData' in result else None
            failureMessage = result['failureMessage'] if 'failureMessage' in result else None
            failure = result['failure'] if 'failure' in result else None
            # print(feature, story, case_name, failureMessage, URL)
            storyString = result['story'] if 'story' in result else ''
            pyString = ''
            result1 = result['result']
            response_time = result['response_time']
        result3 = [case_name, URL, method, requestHeader, queryString, responseData, failureMessage, failure, result1,response_time]
        result_list.append(result3)

    return result_list


def convertedfile(request):
    if request.is_ajax():
        username = request.session.get('user', '')
        import_url_host = request.POST.get('import_url_host', '')
        test_time = time.strftime("%Y-%m-%d %H:%M:%S")
        result1 = upload_file(request)
        paths = result1[0]
        ids = result1[1]
        names = result1[2]
        type = result1[3]

        # cmd run
        optParser = OptionParser(
            usage="Generate JMeter script command example:\n\n\tFiddlerCharles2Jmeter.py -n -i fiddler/charles_file_path -o jmeter_script_file_path --filter-host-name='' --filter_url='' --distinct")

        optParser.add_option("-n",
                             "--no_gui",
                             action='store_true',
                             default=False,
                             dest='no_gui',
                             help="no gui model"
                             )
        optParser.add_option("-i",
                             "--input_file_path",
                             action='store',
                             type='string',
                             dest='input_file_path',
                             help="fiddler/charles_file_path"
                             )
        optParser.add_option("-o",
                             "--output_file_path",
                             action='store',
                             type='string',
                             dest='output_jmxScript',
                             help="jmeter_script_file_path "
                             )
        optParser.add_option("-u",
                             "--filter_url",
                             action='store',
                             type='string',
                             dest='filter_url',
                             default="\n" + R"/(.*)\.(css|ico|jpg|png|gif|bmp|wav|js|jpe)(\?.*)?$",
                             help="filter_url regex default=%default%"
                             )
        optParser.add_option("-f",
                             "--filter-host-name",
                             action='store',
                             type='string',
                             dest='host_name',
                             default=R"^.*$",
                             help="filter-host-name regex default=%default"
                             )
        optParser.add_option("-d",
                             "--distinct",
                             action='store_false',
                             dest='distinct',
                             default=False,
                             help="distinct: Filter duplicate requests , default=%default"
                             )
        # is fiddler4 client run
        optParser.add_option("-s",
                             "--is-fiddler-script-model",
                             action='store_true',
                             default=False,
                             dest='fiddler_script_model',
                             help="fiddler script model :default=%default"
                             )
        (option, args) = optParser.parse_args()

        input_file_path = paths
        host_name = option.host_name
        filter_url = import_url_host
        distinct = option.distinct
        for i in range(0,len(paths)):
            output_jmxScript = current_dir + "/data/upload/" + type + "/" + ids[i] + names[i] + ".jmx"
            run(input_file_path[i] + ids[i] + names[i], filter_url, host_name, output_jmxScript, distinct, args)

            # print(result_list)
            user_product_id = AuthUser.objects.filter(username=username).first().last_name
            result_info = AutotestplatJmeterHistory(product_id=user_product_id,
                                                           name=names[i],
                                                           url_host=import_url_host,
                                                           oldname =names[i],
                                                           newname =ids[i]+names[i]+".jmx",
                                                           DownloadLink=input_file_path[i],
                                                           charger=username,
                                                           type = type,
                                                           create_time = test_time)
                                                           # fd = 1)
            result_info.save()
        return HttpResponse('Good')


def showImportWindow(request,menu_module_id):
    username = request.session.get('user', '')
    public_list = AutotestplatParameter.objects.all()
    menu_module_name = request.POST.get('menu_module_name', '')
    menu_module_tmp = AutotestplatMockModule.objects.filter(module_name=menu_module_name).first()
    if menu_module_tmp:
        menu_module_id = menu_module_tmp.id
    else:
        menu_module_id = 0
    if AuthUser.objects.filter(username=username).first().is_superuser == 1:
        product_all = AutotestplatProduct.objects.all()
        env_para = AutotestplatParameter.objects.filter(type="env")
        auth_para = AutotestplatParameter.objects.filter(type="auth")
        module_all = AutotestplatMockModule.objects.filter(type='api')
    else:
        product_id = AuthUser.objects.filter(username=username).first().last_name
        product_all = AutotestplatProduct.objects.filter(id=product_id).all()
        env_para = AutotestplatParameter.objects.filter(product_id=product_id, type="env")
        auth_para = AutotestplatParameter.objects.filter(product_id=product_id,type="auth")
        module_all = AutotestplatMockModule.objects.filter(product_id=product_id,type='api')

    if AuthUser.objects.filter(username=username).first().is_superuser == 1:
        interfaces = AutotestplatJmeterHistory.objects.filter().order_by('-id').all()
        product_name = ''
    else:
        user_product_id = AuthUser.objects.filter(username=username).first().last_name
        try:
            interfaces = AutotestplatJmeterHistory.objects.filter(product_id=user_product_id).order_by('-id').all()
        except:
            interfaces = AutotestplatJmeterHistory.objects.filter().order_by('-id').all()
        product_id = AuthUser.objects.filter(username=username).first().last_name
        product_name = AutotestplatProduct.objects.filter(id=product_id).first().product_name
        product_all = AutotestplatProduct.objects.filter(delete_flag='N')
    for i in interfaces:
        tmp_ids = AutotestplatProduct.objects.all().values_list().order_by('id')
        tmp = []
        for tmp_id in tmp_ids:
            tmp.append(tmp_id[0])
        if (i.product_id == None):
            count = 0
        else:
            count = tmp.count(int(i.product_id))
        if count > 0:
            product_name_tmp = AutotestplatProduct.objects.filter(id=int(i.product_id)).first().product_name
            i.product_id = product_name_tmp
    progress = AutotestplatInterfacePerformance.objects.filter(id=1).first().progress
    progress_total = AutotestplatInterfacePerformance.objects.filter(id=1).first().progress_total
    paginator = Paginator(interfaces, 10)
    num = len(interfaces)
    page = request.GET.get('page', 1)
    try:
        page_list = paginator.page(page)
    except PageNotAnInteger:
        page_list = paginator.page(1)
    except EmptyPage:
        page_list = paginator.page(paginator.num_pages)
    c = csrf(request)
    c.update({'page_list': page_list, 'interfaces': interfaces, 'type': type,'num':num,"product_name":product_name,"product_alls":product_all,"progress":progress,"progress_total":progress_total,'public_list': public_list,"env_paras":env_para,"auth_paras":auth_para,"product_alls":product_all,'module_all':module_all,'menu_module_id':menu_module_id})
    return render(request, "jmeter_converted.html", c)


def downloadjmx(request):
    return download_file(request)

def uploadjmx(request):
    if request.is_ajax():
        username = request.session.get('user', '')
        import_url_host = request.POST.get('import_url_host', '')
        test_time = time.strftime("%Y-%m-%d %H:%M:%S")
        result1 = upload_file(request)
        paths = result1[0]
        ids = result1[1]
        names = result1[2]
        type = result1[3]
        for i in range(0,len(paths)):
            # print(result_list)
            user_product_id = AuthUser.objects.filter(username=username).first().last_name
            result_info = AutotestplatJmeterHistory(product_id=user_product_id,
                                                           name=names[i],
                                                           url_host=import_url_host,
                                                           oldname =names[i],
                                                           newname =ids[i]+names[i],
                                                           DownloadLink=paths[i],
                                                           charger=username,
                                                           type = type,
                                                           create_time = test_time)
                                                           # fd = 1)
            result_info.save()
    return HttpResponse('Good')


def modifyjmx(request):
    contents = json.loads(request.body.decode()).get('contents', 0)
    threads = json.loads(request.body.decode()).get('threads', 0)
    duration = json.loads(request.body.decode()).get('duration', 0)
    loops =  json.loads(request.body.decode()).get('loops', 0)
    path = current_dir + "/data/" + contents + "/"
    name_list = []
    suffix = ".jmx"
    if not os.path.exists(path):  # 判断所在目录下是否有该文件名的文件夹
        os.mkdir(path)  # 创建多级目录用mkdirs，单击目录mkdir
    else:
        print('the file exists')
    id_list = json.loads(request.body.decode()).get('id_list', 0)
    for id in id_list:
        name = list(AutotestplatJmeterHistory.objects.filter(id=id).values_list('newname', flat=True))[0]
        name_list.append(name)
    report_id_list = []
    for filename in name_list:
        values = ''
        with open(path+filename, 'r', encoding='utf-8') as fp_src:
            values = fp_src.readlines()

        file_name = os.path.split(path+filename)[-1].split('.jmx')[0]
        # for i, thread in enumerate(threads):
        dst = os.path.join(path, f'{file_name}.jmx')
        with open(dst, 'w', encoding='utf-8') as fp_dst:
            for value in values:
                if "ThreadGroup.num_threads" in value:
                    fp_dst.write(f'        <stringProp name="ThreadGroup.num_threads">{threads}</stringProp>\n')
                elif "ThreadGroup.scheduler" in value:
                    fp_dst.write(f'        <boolProp name="ThreadGroup.scheduler">true</boolProp>\n')
                elif "ThreadGroup.duration" in value:
                    fp_dst.write(f'        <stringProp name="ThreadGroup.duration">{duration}</stringProp>\n')
                elif "LoopController.loops" in value:
                    fp_dst.write(f'          <intProp name="LoopController.loops">{loops}</intProp>\n')
                # elif "ThreadGroup.ramp_time" in value:
                #     fp_dst.write(f'        <stringProp name="ThreadGroup.ramp_time">1</stringProp>\n')
                # elif "ThreadGroup.on_sample_error" in value:
                #     fp_dst.write(f'        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>\n')
                # elif "LoopController.continue_forever" in value:
                #     fp_dst.write(f'          <boolProp name="LoopController.continue_forever">false</boolProp>\n')
                # elif "LoopController.loops" in value:
                #     fp_dst.write(f'          <intProp name="LoopController.loops">1</intProp>\n')
                # elif "ThreadGroup.scheduler" in value:
                #     fp_dst.write(f'        <boolProp name="ThreadGroup.scheduler">false</boolProp>\n')
                # elif "ThreadGroup.duration" in value:
                #     fp_dst.write(f'        <stringProp name="ThreadGroup.duration">{duration}</stringProp>\n')
                # elif "ThreadGroup.delay" in value:
                #     fp_dst.write(f'        <stringProp name="ThreadGroup.delay">0</stringProp>\n')
                else:
                    fp_dst.write(value)

    return HttpResponse('success')

def deljmx(request):
    from djcelery.models import PeriodicTask, CrontabSchedule, IntervalSchedule
    if request.method == "POST":
        raw_data = request.body
        raw_data = json.loads(raw_data)
        id_list = raw_data['id_list']
        for id1 in id_list:
            task = AutotestplatJmeterHistory.objects.filter(id=id1)
            if task:
                task_id = AutotestplatJmeterHistory.objects.filter(id=id1).first().task_id
                PeriodicTask.objects.filter(id=task_id).delete()
            crontab = PeriodicTask.objects.filter(id=task_id)
            if crontab:
                crontab_id = PeriodicTask.objects.filter(id=task_id).first().crontab_id
                CrontabSchedule.objects.filter(id=crontab_id).delete()
            AutotestplatJmeterHistory.objects.filter(id=id1).delete()
        return HttpResponse('delete success!')

def addCrnjmx(request):
    if request.method == "POST":
        username = request.session.get('user', '')
        contents = json.loads(request.body.decode()).get('contents', 0)
        type = json.loads(request.body.decode()).get('type', 0)
        ip = json.loads(request.body.decode()).get('ip', 0)
        add_run_time = json.loads(request.body.decode()).get('add_run_time', 0)
        add_run_interval = json.loads(request.body.decode()).get('add_run_interval', 0)
        id_list = json.loads(request.body.decode()).get('id_list', 0)
        crontab = add_run_time
        interval = add_run_interval
        try:
            min = crontab.split(':')[1]
        except:
            pass
        for id in id_list:
            newname = list(AutotestplatJmeterHistory.objects.filter(id=id).values_list('newname', flat=True))[0]
            task = 'autotest.views_jmeter.startTestJmeter'

            # task_id = AutotestplatJmeterHistory.objects.filter(id=id).first().task_id
            # crontab_exist = PeriodicTask.objects.filter(id=task_id).first()

            if crontab !=None and crontab!='':
                year = crontab.split('-')[0]
                month = crontab.split('-')[1]
                day = crontab.split('-')[2].split(' ')[0]
                hour = crontab.split(':')[0].split(' ')[1]
                min = str(int(min) + 1)
                try:
                    task_id = AutotestplatJmeterHistory.objects.filter(id=id).first().task_id
                    PeriodicTask.objects.filter(id=task_id).delete()
                except:
                    pass
              #  CrontabSchedule.objects.create(month_of_year=month, day_of_month=day, hour=hour, minute=min, day_of_week='*')
                CrontabSchedule.objects.create(month_of_year='*', day_of_month='*', hour=hour, minute=min, day_of_week='*')
                crontab_id = CrontabSchedule.objects.order_by('-id').first().id
                # runtask = startTestJmeter.delay(username, contents, type, ip, id_list)
                # args = '[' + str(id) + ']'
                args = json.dumps([username, contents, type, ip, [id]])
                # kwargs = json.dumps({'be_careful': True, }),
                description = request.session.get('user', '')
                enabled = '1'
                PeriodicTask.objects.update_or_create(name=newname, task=task, args=args, crontab_id=crontab_id, interval_id=None,
                                            enabled=enabled, description=description)
                max_task_id = PeriodicTask.objects.order_by('-id')[0].id     #定时任务
                AutotestplatJmeterHistory.objects.filter(id=id).update(run_time=add_run_time,task_id=max_task_id) #更新时间
            elif interval != None and interval != '':
                try:
                    task_id = AutotestplatJmeterHistory.objects.filter(id=id).first().task_id
                    PeriodicTask.objects.filter(id=task_id).delete()
                except:
                    pass
                if interval == "每分钟1次":
                    interval_id = '5'
                elif interval == "每小时6次":
                    interval_id = '4'
                elif interval == "每天1次":
                    interval_id = '3'
                elif interval == "每天10次":
                    interval_id = '2'
                elif interval == "每天4次":
                    interval_id = '1'
                # args = '['+str(id)+']'
                args = json.dumps([username, contents, type, ip, [id]])
                description = request.session.get('user', '')
                enabled = '1'
                PeriodicTask.objects.update_or_create(name=newname, task=task, args=args, crontab_id=None, interval_id=interval_id,
                                        enabled=enabled, description=description)
                max_task_id = PeriodicTask.objects.order_by('-id')[0].id
                AutotestplatJmeterHistory.objects.filter(id=id).update(run_time=add_run_interval,task_id=max_task_id)
            else:
                max_task_id=None
                AutotestplatJmeterHistory.objects.filter(id=id).update(task_id=max_task_id)

        return HttpResponse('insert success!')