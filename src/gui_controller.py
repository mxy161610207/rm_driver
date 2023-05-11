import tkinter as tk
import threading
import queue,time

from ep_handler import json_dumps

def gui_raiser(proc_name, platform_resources, platform_socket_address):
    print("Proc [{}] start".format(proc_name))

    # --- 获取全局状态 ---
    global_status = platform_resources['global_status']

    # --- 获取驱动资源 ---
    sensor_syncer = platform_resources['sensor_syncer']
    actuator_syncer = platform_resources['actuator_syncer']

    window = tk.Tk()
    window.title("EP车临时控制器")

    text = tk.Text(window,state= tk.DISABLED)
    text.grid(row=0,column=0,columnspan=3,padx=10,pady=10)

    button_name = [
        ['左转','L'],
        ['前进','W'],
        ['右转','R'],
        ['左移','A'],
        ['后退','S'],
        ['右移','D'],
        ['退出','q'],
    ]

    
    for i,(name,cmd) in enumerate(button_name):
        button = tk.Button(window,text = name,
        command= lambda act = cmd: _append_action(actuator_syncer,act))
        button.grid(row=1+i//3,column=i%3,padx=10,pady=10)

    t = threading.Thread(target=_update_text,args=(sensor_syncer,text))
    t.daemon = True
    t.start()

    window.mainloop()

def _append_action(actuator_syncer,act):
    print("put",act)
    actuator_syncer.put(act)

def _update_text(sensor_syncer,text):
    while True:
        text_content = json_dumps(sensor_syncer)

        text.configure(state=tk.NORMAL)
        text.delete('1.0',tk.END)
        text.insert('1.0',text_content)
        text.configure(state=tk.DISABLED)

        time.sleep(0.5)



        
