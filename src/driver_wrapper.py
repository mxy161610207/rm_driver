import time
import os
import queue

import gui_controller
import ep_handler
import server_connecter

from multiprocessing import Value, Process, Queue, Manager

# 约定所有status
# 0 都是未初始化
# 1 都是正常工作
# 2 都是等待关闭
# -1 都是报错

if __name__ == '__main__':
    # 系统多进程资源
    platform_manager = Manager()
    platform_resources = {}

    # 通信地址
    platform_socket_address = {
        'phy_sender': ('127.0.0.1', 41997),
    }

    # 系统多进程全局状态
    platform_resources['global_status'] = Value('i', 0)

    # --- EP小车资源 ---
    # 小车状态[int] 0 - 无车, 1 - 有车且初始化完成, 2 - 其他线程要求关机
    platform_resources['ep_status'] = Value('i', 0)
    # 小车读取数据[dict] 多进程一致的字典
    platform_resources['sensor_syncer'] = platform_manager.dict()
    # 小车动作数据[queue] 多进程一致的队列
    platform_resources['actuator_syncer'] = Queue()

    # --- 通信资源 ---
    # 自身client状态
    platform_resources['client_status'] = Value('i', 0)
    # 平台状态
    platform_resources['server_status'] = Value('i', 0)
    # C <- S 从平台接受的数据
    platform_resources['driver_recv'] = Queue(-1)
    # C -> S 向平台发送的数据
    platform_resources['driver_send'] = Queue(-1)

    # --- 多进程处理器定义 ---
    # 1) EP小车管理进程
    process_name = 'ep_conn_raiser'
    proc_ep = Process(
        name=process_name,
        target=ep_handler.ep_conn_raiser,
        args=(process_name,
              platform_resources,
              platform_socket_address)
    )
    # 随主线程退出
    proc_ep.daemon = True

    # 2) 和平台的通信进程
    process_name = 'server_conn_raiser'
    proc_conn = Process(
        name=process_name,
        target=server_connecter.server_conn_raiser,
        args=(process_name,
              platform_resources,
              platform_socket_address)
    )
    # 随主线程退出
    proc_conn.daemon = True

    # 2) 临时的用户界面进程
    process_name = 'gui_raiser'
    proc_gui = Process(
        name=process_name,
        target=gui_controller.gui_raiser,
        args=(process_name,
              platform_resources,
              platform_socket_address)
    )
    proc_gui.daemon = True

    # ------ 进程按顺序开启 -------
    # 3) 连接gui进程开启
    proc_gui.start()

    # 1) EP小车管理进程开启，连接小车成功后开启服务器
    proc_ep.start()
    ep_status = platform_resources['ep_status']
    while (ep_status.value == 0):
        time.sleep(0.5)

    # 2) 连接平台进程开启
    proc_conn.start()
    client_status = platform_resources['client_status']
    while (client_status.value == 0):
        time.sleep(0.5)
    
    proc_pool = [proc_ep, proc_conn, proc_gui]

    global_status = platform_resources['global_status']

    while True:
        for proc in proc_pool:
            print("[{}]exitcode={}".format(proc.name, proc.exitcode))
            if (not proc.is_alive()):
                # 某进程异常，TODO 之后改为重启
                # 关机
                print("[{}] 驱动监测到进程关闭".format(proc.name))
                global_status.value = 2

        if (global_status.value == 2):
            print("关闭所有资源中...")
            for proc in proc_pool:
                if (proc.is_alive()):
                    proc.terminate()
            # wait_list = []
            # client_status.value = 2
            # wait_list.append(client_status)

            # ep_status.value = 2
            # wait_list.append(ep_status)

            # sdk_handler.closer(
            #     platform_resources,
            #     platform_resources,
            #     platform_socket_address)

            print("关闭完成...")
            break

        time.sleep(3)
        print("驱动状态 =", global_status.value)

    print("驱动退出")
