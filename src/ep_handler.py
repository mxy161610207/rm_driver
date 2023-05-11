import time
import json
import copy
import queue
import os
import convert
from robomaster import robot

def ep_conn_raiser(proc_name, platform_resources, platform_socket_address):
    print("Proc [{}] start".format(proc_name))

    # --- 获取全局状态 ---
    global_status = platform_resources['global_status']

    # --- 获取驱动资源 ---
    ep_status = platform_resources['ep_status']
    sensor_syncer = platform_resources['sensor_syncer']
    actuator_syncer = platform_resources['actuator_syncer']

    # --- 连接小车,连接小车的传感器 ---
    try:
        ep_robot = _get_initialized_ep_robot(sensor_syncer)
    except Exception as e:
        print("发生异常:{}", e)
        ep_status.value = -1
        
        global_status.value = 2
        os._exit(1)   # 大疆连接是一个thread，需要连该thread一起退出

    ep_status.value = 1  # 连接成功

    # --- 获取执行动作 ---
    try:
        while True:
            try:
                act = actuator_syncer.get(block=False)
                if (act == 'q' or act == 'Q'):
                    break
                print("get",act)
            except queue.Empty:
                continue
            
            try:    
                x, y, deg = convert.convert(act)
            except Exception as e:
                print("undefined action: [{}]".format(act))
                continue

            # print("before action:", json_dumps(sensor_syncer))
            ep_robot.chassis.move(x, y, deg).wait_for_completed()
            time.sleep(0.5)
            # print("after action:", json_dumps(sensor_syncer))
    except Exception as e:
        print("sdk error: [{}]".format(e))

    # 释放小车资源
    _close_ep_robot(ep_robot)
    print("Proc [{}] end".format(proc_name))
    # while True:
    #     if ep_status == 2:
    #         ep_handler.close_ep_robot(ep_robot)
    #         print("Proc [{}] end".format(proc_name))
    #     time.sleep(3)

def json_dumps(syncer,indent=2):
    syncer_copy = copy.deepcopy(syncer)
    return json.dumps(syncer_copy, indent=indent)

def _get_initialized_ep_robot(syncer):
    ep_robot = robot.Robot()
    ep_robot.initialize(conn_type="sta")
    ep_robot.set_robot_mode(mode=robot.CHASSIS_LEAD)

    print("connect success!")

    # battery
    ep_robot.battery.sub_battery_info(
        freq=20, callback=_sub_battery_info_handler, syncer=syncer)

    # sensor
    ep_robot.sensor.sub_distance(
        freq=20, callback=_sub_distance_handler, syncer=syncer)

    # chassis
    ep_robot.chassis.sub_position(
        cs=1, freq=20, callback=_sub_position_handler, syncer=syncer)
    ep_robot.chassis.sub_attitude(
        freq=20, callback=_sub_attitude_handler, syncer=syncer)

    # gimbal
    ep_robot.gimbal.sub_angle(
        freq=20, callback=_sub_angle_handler, syncer=syncer)

    # 等订阅成功
    time.sleep(0.5)

    # if (sth. error):
    #     raise Exception("_sub_battery_info failed!!")

    if syncer['battery'] < 10:
        raise Exception("电量过低 percent = {}%, 先充电！！".format(syncer['battery']))

    # print("INIT:",json_dumps(syncer, indent=2))
    return ep_robot

# 好像没有用，退出小车连接就直接terminate整个线程了
def _close_ep_robot(ep_robot):
    if not isinstance(ep_robot,robot.Robot):
        raise Exception("close_ep_robot: 小车的参数不正确 ep_robot {}".format(ep_robot))
    
    ep_robot.battery.unsub_battery_info()
    ep_robot.sensor.unsub_distance()

    ep_robot.chassis.unsub_position()
    ep_robot.chassis.unsub_attitude()

    ep_robot.gimbal.unsub_angle()

    ep_robot.close()

def _sub_battery_info_handler(info, syncer):
    """
      回调数据: percent:

      使用 
        :percent: 电池电量百分比
    """
    syncer['battery'] = info

def _sub_distance_handler(info, syncer):
    """
      回调数据: distance[4] 默认顺序 F,R,B,L

      使用 
        :distance[4]: 4个tof的距离信息, 默认单位mm
    """
    syncer['ir_distance'] = {
        'F': info[0],
        'R': info[1],
        'B': info[2],
        'L': info[3],
    }
    # print("[+ Sim] tof1:{0}  tof2:{1}  tof3:{2}  tof4:{3}".format(d[0], d[1], d[2], d[3]))

def _sub_position_handler(info, syncer):
    """
      回调数据: (x, y, z) 默认上电时刻

      使用 
        :x: x轴方向距离,单位 m
        :y: y轴方向距离,单位 m
    """
    syncer['sdk_position'] = {
        'x': info[0],
        'y': info[1],
        'cs': 1
    }

def _sub_angle_handler(info, syncer):
    """
      回调数据:(pitch_angle, yaw_angle, pitch_ground_angle, yaw_ground_angle)

      使用 
        :yaw_ground_angle: 上电时刻yaw轴角度 该值左转变小右转变大
    """
    pitch_angle, yaw_angle, pitch_ground_angle, yaw_ground_angle = info
    syncer['gimbal_angle'] = {
        'degree': yaw_ground_angle,
        'cs': 1
    }

def _sub_attitude_handler(info, syncer):
    """
      回调数据: (yaw, pitch, roll)

      使用
        :yaw: yaw轴姿态角, 该值左转变小右转变大
    """
    yaw, pitch, roll = info
    syncer['chassis_angle'] = {
        'degree': yaw,
        'cs': 1
    }