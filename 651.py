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
from .models import *

from rest_framework import status

import xml.etree.cElementTree as ET

from django.db import connection
import subprocess
import psutil
import socket
current_dir = os.getcwd()
jmxfile = os.path.join(current_dir, 'apache-jmeter-5.1.1/bin', 'apitest.jmx')
logfile = os.path.join(current_dir, 'autotest', 'test_out.log')
codefile= os.path.join(current_dir, 'autotest', 'code.jpg')
session = requests.Session()


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

def decode_error(stderr):
    for encoding in ['utf-8', 'cp1252', 'latin1', 'gbk']:
        try:
            return f"编码: {encoding}\n{stderr.decode(encoding, errors='ignore')}"
        except Exception as e:
            continue
    return "无法解码错误信息"


def terminate_process(process):
    try:
        parent = psutil.Process(process.pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
        parent.wait(timeout=10)
        print(f"JMeter进程 {process.pid} 及其子进程已终止")
    except psutil.NoSuchProcess:
        print(f"JMeter进程 {process.pid} 不再存在")
    except psutil.TimeoutExpired:
        print(f"JMeter进程 {process.pid} 仍未响应，尝试使用更强制的方式终止")
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()
        parent.wait(timeout=5)
        print(f"JMeter进程 {process.pid} 及其子进程已强制终止")
    except Exception as e:
        print(f"终止JMeter进程时出错: {e}")

def run_command(command,time):
    try:
        # 临时添加路径到PATH环境变量
        env = os.environ.copy()
        env['PATH'] = f"/apache-jmeter-5.1.1/bin:{env['PATH']}"
        env["JAVA_HOME"] = "/usr/local/java/jdk"  # 替换为你的Java安装路径
        env["PATH"] = env["JAVA_HOME"] + r"\bin;" + env["PATH"]
        env["JAVA_OPTS"] = "-Djava.rmi.server.hostname=10.17.18.162"


        # 异步执行JMeter命令
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env  # 传递修改后的环境变量
        )

        # 等待命令完成
        stdout, stderr = process.communicate(timeout=time)  # 设置超时时间为300秒

        # 检查命令状态
        if process.returncode == 0:
            print("JMeter测试成功执行")
            print("标准输出:")
            print(stdout.decode('utf-8', errors='ignore'))
        else:
            print("JMeter测试失败")
            print("标准输出:")
            print(stdout.decode('utf-8', errors='ignore'))
            print("标准错误:")
            print(decode_error(stderr))

    except subprocess.TimeoutExpired:
        print("JMeter测试超时")
        terminate_process(process)

def run_jmeter_test(jmx_properties,jmx_file_path,report_id, log_file_path,time):
    output_file_path = current_dir + "/autotest/static/data/" +  report_id  + ".jtl"
    # 确保路径正确并且命令是可执行的
    jmeter_command = [
        current_dir + "/apache-jmeter-5.1.1/bin/jmeter",  # 使用绝对路径
        "-n",  # 非GUI模式
        "-r",  # 非GUI模式
        "-q",  # 非GUI模式
        jmx_properties,
        "-t",  # 测试计划文件
        jmx_file_path,
        "-l",  # 日志文件（结果文件）
        output_file_path,
        "-j",  # 日志文件
        log_file_path
    ]

    print(f"正在执行JMeter测试: {jmx_file_path}")
    print(f"JMeter命令路径: {jmeter_command[0]}")

    # 构建Java命令
    java_command = [
        "java", "-jar", "{current_dir}/autotest/static/data/Report-2.0.jar", "{current_dir}/autotest/static/data/{report_id}.jtl", "1", "{current_dir}/autotest/static/data/{report_id}"
    ]

    # 执行JMeter命令
    run_command(jmeter_command,time)

    # 执行Java命令
    run_command(java_command)



def restart_container(host):
    try:
        container_name = 'json?filters={"name":["jmeter-worker-01"]}'  # 替换为你的容器 ID
        stop_url = f"{host}/v1.41/containers/{container_name}"
        stop_response = requests.get(stop_url).json()[0]
        container_id = stop_response['Id']

        # 启动容器
        start_url = f"{host}/v1.41/containers/{container_id}/start"
        start_response = requests.post(start_url)
        if start_response.status_code == 204:
            print(f"Container {container_id} started successfully.")
        else:
            print(f"Failed to start container {container_id}. Status code: {stop_response.status_code}")

        # 等待几秒钟
        time.sleep(5)
        
        # 停止容器
        stop_url = f"{host}/v1.41/containers/{container_id}/stop"
        stop_response = requests.post(stop_url)
        if stop_response.status_code == 204:
            print(f"Container {container_id} stopped successfully.")
        else:
            print(f"Failed to stop container {container_id}. Status code: {stop_response.status_code}")
            return

        # 等待几秒钟
        time.sleep(5)

        # 启动容器
        start_url = f"{host}/v1.41/containers/{container_id}/start"
        start_response = requests.post(start_url)
        if start_response.status_code == 204:
            print(f"Container {container_id} started successfully.")
        else:
            print(f"Failed to start container {container_id}. Status code: {stop_response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


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

def startTestJmeter(request):
    import platform
    import shutil
    try:
        username = request.session.get('user', '')
        contents = json.loads(request.body.decode()).get('contents',0)
#get方式 contents = urllib.parse.unquote(request.GET.get('contents'))
        type = json.loads(request.body.decode()).get('type', 0)
#get方式 type = urllib.parse.unquote(request.GET.get('type'))
        test_time = time.strftime("%Y-%m-%d %H:%M:%S")
        path1 = current_dir+"/data/"+contents
        path = os.path.split(path1)[0] + '/'
        suffix = ".jmx"
        # if not os.path.exists(path):  # 判断所在目录下是否有该文件名的文件夹
        #     os.mkdir(path)  # 创建多级目录用mkdirs，单击目录mkdir
        # else:
        #     print('the file exists')
        report_id_list = []
        filename_list = getFileName1(path1, suffix)
        for file in filename_list:
            time.sleep(600)
            report_id = str(datetime.now().strftime("%Y%m%d%H%M%S%f"))
            # jmx_file = file
            # print(report_file)
        #    report_result_file = "d: && cd  "+current_dir+"/autotest/static/data/ && java -jar AggregateReport-2.0.jar "+report_id+".jtl 1 "+report_id
            if type == "csv" :
                run_jmeter_test(current_dir + "/apache-jmeter-5.1.1/bin/user-" + type + ".properties",path + file, report_id, current_dir + "/jmeter.log", 3600)
            elif type == "csv-w":
               # ip_address_list = ['10.43.161.180','10.3.210.116','10.3.204.222', '10.43.138.30','10.43.119.61','10.43.119.221','10.43.138.119']
                ip_address_list = ['10.0.180.85','10.0.180.86']

                # 示例：读取、修改、写回
                jmeter_properties_path = current_dir + "/apache-jmeter-5.1.1/bin/user-csv-w.properties"

                # 读取配置
                props = read_jmeter_properties(jmeter_properties_path)
                # print("当前配置：", props['remote_hosts'])
                for host in ip_address_list:
                    restart_container('http://'+host+':2375')
                time.sleep(60)
                # 修改某个参数
                props['remote_hosts'] = is_port_open(ip_address_list, 1099)

                # 写回文件
                write_jmeter_properties(jmeter_properties_path, props)
                # print("配置已修改！")

                run_jmeter_test(current_dir + "/apache-jmeter-5.1.1/bin/user-" + type + ".properties",path + file, report_id, current_dir + "/jmeter.log", 3600)
            else:
                run_jmeter_test(current_dir + "/apache-jmeter-5.1.1/bin/user-" + type + ".properties",path + file, report_id, current_dir + "/jmeter.log", 3600)
            if type == 'csv' or type == "csv-w":
                user_product_id = AuthUser.objects.filter(username=username).first().last_name
                product_name = AutotestplatProduct.objects.filter(id=user_product_id).first().product_name
                result_info = AutotestplatTestplanjmeterResult(report_id=report_id,
                                                              product_id=user_product_id,
                                                              product_name=contents,
                                                              suit_id=report_id,
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
                report_id_list.append(report_id)

            # return HttpResponse("success")
        result = {"status": status.HTTP_200_OK, "report_id": report_id_list, "filename": filename_list}
        return JsonResponse(result, safe=False)
    except Exception:
        traceback.print_exc()
        return HttpResponse("failed")



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
