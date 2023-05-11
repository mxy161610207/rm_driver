import time
import socket 
import json

def server_conn_raiser(proc_name, platform_resources, platform_socket_address):
    print("Proc [{}] start".format(proc_name))

    with open("config.json","r") as f:
        config = f.read()
        print(config)

    # --- 获取全局状态 ---
    global_status = platform_resources['global_status']

    # --- 获取资源 ---
    client_status = platform_resources['client_status']
    sensor_syncer = platform_resources['sensor_syncer']
    actuator_syncer = platform_resources['actuator_syncer']

    client_status.value = 1
    
    task(config, client_status, sensor_syncer, actuator_syncer)

    print("Proc [{}] end".format(proc_name))

def recv(client_socket):
    buffer = bytearray(1024)
    r = client_socket.recv_into(buffer)
    if r == 0:
        return None
    data = buffer[:r].decode("utf-8")
    return data
    
def send(client_socket, data):
    client_socket.send(data.encode("utf-8"))

def task(config, client_status, sensor_syncer, actuator_syncer):
    #创建一个socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #连接服务器
    ip = "127.0.0.1"
    point = 9091
    client_socket.connect((ip, point))
    #发送数据
    client_socket.send(config.encode("utf-8"))
    #接收数据
    register_back = recv(client_socket)
    if register_back == None:
        client_status.value = -1
        return
    
    obj = json.loads(register_back)
    if obj["cmd"] != "register_back" or obj["message"] != "true":
        return
        
    while True:
        request = recv(client_socket)
        if request == None:
            client_status.value = -1
            return
        obj = json.loads(request)
        if obj["cmd"] == "sensory_request":
            value = {}
            value["speed"] = 10.0
            value["longitude"] = 20.0
            value["latitude"] = 30.0
            response = {}
            response["cmd"] = "sensory_back"
            response["message"] = json.dumps(value)
            send(socket, json.dumps(response))
        elif obj["cmd"] == "action_request":
            action_back = {}
            action_back["cmd"] = "action_back"
            action_back["message"] = "true"