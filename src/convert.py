def convert(action):
    large_move_dis = 0.3
    small_move_dis = 0.1
    large_rot_deg = 90
    small_rot_deg = 10
    if (action == 'W'):
        return large_move_dis,0,0
    elif (action == 'S'):
        return -large_move_dis,0,0
    elif (action == 'A'):
        return 0,-large_move_dis,0
    elif (action == 'D'):
        return 0,large_move_dis,0
    elif (action == 'w'):
        return small_move_dis,0,0
    elif (action == 's'):
        return -small_move_dis,0,0
    elif (action == 'a'):
        return 0,-small_move_dis,0
    elif (action == 'd'):
        return 0,small_move_dis,0
    elif (action == 'L'):
        return 0,0,large_rot_deg
    elif (action == 'R'):
        return 0,0,-large_rot_deg
    elif (action == 'l'):
        return 0,0,small_rot_deg
    elif (action == 'r'):
        return 0,0,-small_rot_deg
    elif (action == 'w'):
        return small_move_dis,0,0
    elif (action == 'B'):
        return 0,0,180
    else:
        pass