import os
import sys
import time
import json
import logging
import requests
import socket
import psutil
import subprocess
from datetime import datetime
from threading import Thread
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler, ThrottledDTPHandler
from pyftpdlib.servers import FTPServer
import configparser
import multiprocessing
import hashlib
import uuid

# === 全局配置 ===
ONEAPI_BASE_URL = "https://your-oneapi-server.com/api"  # OneAPI 服务器地址
ONEAPI_AUTH_TOKEN = "your-secure-api-token"             # 从安全配置读取
HEARTBEAT_INTERVAL = 60                                # 心跳间隔（秒）
COMMAND_CHECK_INTERVAL = 10                            # 指令检查间隔（秒）

# === 日志配置 ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("client_control.log"),
        logging.StreamHandler()
    ]
)

# === 工具函数 ===
def get_machine_fingerprint():
    """生成设备唯一指纹（MAC + CPU序列号）"""
    mac = uuid.getnode()
    cpu_serial = subprocess.check_output("wmic cpu get ProcessorId", shell=True).decode().split("\n")[1].strip()
    return hashlib.sha256(f"{mac}-{cpu_serial}".encode()).hexdigest()

def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def terminate_process_tree(pid):
    """终止进程树"""
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
    except psutil.NoSuchProcess:
        pass

# === OneAPI 交互核心 ===
class OneAPIClient:
    @staticmethod
    def check_auth():
        """向OneAPI请求授权"""
        try:
            response = requests.post(
                f"{ONEAPI_BASE_URL}/auth",
                json={"machine_id": get_machine_fingerprint()},
                headers={"Authorization": f"Bearer {ONEAPI_AUTH_TOKEN}"},
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("allowed", False)
        except Exception as e:
            logging.error(f"授权检查失败: {e}")
        return False

    @staticmethod
    def send_heartbeat():
        """发送心跳包"""
        try:
            requests.post(
                f"{ONEAPI_BASE_URL}/heartbeat",
                json={"machine_id": get_machine_fingerprint()},
                headers={"Authorization": f"Bearer {ONEAPI_AUTH_TOKEN}"},
                timeout=5
            )
        except Exception as e:
            logging.warning(f"心跳发送失败: {e}")

    @staticmethod
    def fetch_command():
        """获取远程控制指令"""
        try:
            response = requests.get(
                f"{ONEAPI_BASE_URL}/commands",
                headers={"Authorization": f"Bearer {ONEAPI_AUTH_TOKEN}"},
                timeout=5
            )
            if response.status_code == 200:
                return response.json().get("command")
        except Exception as e:
            logging.warning(f"指令获取失败: {e}")
        return None

# === 主业务逻辑 ===
def start_jmeter_server(ip):
    """启动JMeter服务"""
    if is_port_in_use(1099):
        terminate_process_tree(next(p.info['pid'] for p in psutil.process_iter(['pid', 'name']) 
                               if p.info['name'] == 'java.exe' and 1099 in [conn.laddr.port 
                               for conn in psutil.Process(p.info['pid']).connections()]))

    jmeter_cmd = f"jmeter-server -Dserver_port=1099 -Dserver.rmi.localport=4000 -Jserver.rmi.ssl.disable=true -Djava.rmi.server.hostname={ip}"
    subprocess.Popen(jmeter_cmd, shell=True)

def client(main_pid, expiration):
    """受OneAPI控制的主业务逻辑"""
    # 1. 检查本地授权
    if expiration and datetime.now() > expiration:
        logging.error("本地授权已过期！")
        sys.exit(1)

    # 2. OneAPI动态授权
    if not OneAPIClient.check_auth():
        logging.error("OneAPI授权失败！")
        sys.exit(1)

    # 3. 启动心跳线程
    def heartbeat_loop():
        while True:
            OneAPIClient.send_heartbeat()
            time.sleep(HEARTBEAT_INTERVAL)
    
    Thread(target=heartbeat_loop, daemon=True).start()

    # 4. 启动指令监听线程
    def command_listener():
        while True:
            cmd = OneAPIClient.fetch_command()
            if cmd == "stop":
                logging.info("收到停止指令")
                sys.exit(0)
            elif cmd == "restart":
                logging.info("收到重启指令")
                os.execv(sys.executable, ['python'] + sys.argv)
            time.sleep(COMMAND_CHECK_INTERVAL)
    
    Thread(target=command_listener, daemon=True).start()

    # 5. 获取IP并启动服务
    local_ip = socket.gethostbyname(socket.gethostname())
    logging.info(f"服务启动，监听IP: {local_ip}")
    start_jmeter_server(local_ip)

    # 6. 保持主线程运行
    while True:
        time.sleep(1)

# === 主程序入口 ===
if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # 从配置文件读取参数
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    expiration_str = config.get('DEFAULT', 'expiration', fallback=None)
    expiration = datetime.strptime(expiration_str, '%Y-%m-%d %H:%M:%S') if expiration_str else None

    # 启动受控客户端
    try:
        client(os.getpid(), expiration)
    except KeyboardInterrupt:
        logging.info("程序终止")
    except Exception as e:
        logging.error(f"运行时错误: {e}")
        sys.exit(1)
