def round_(jump):
    round_num = 0
    if 100 < 1/jump < 1000:
        round_num = 3
    elif 10 < 1/jump <= 100:
        round_num = 2
    elif 1 < 1/jump <= 10:
        round_num = 1
    elif 0.1 < 1/jump <= 1:
        round_num = 0
    elif 0.01 < 1/jump <= 0.1:
        round_num = -1
    return round_num
