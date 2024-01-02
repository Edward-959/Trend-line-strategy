import xlwt
import numpy as np
import datetime as dt
import time
# from margin_fee_confg import margin_fee_dict


def digit_time(datetime_):
    return int(str(datetime_.hour) + str(datetime_.minute) + str(datetime_.second))


def open_long(open_time, open_time_digit, index_list, i, open_price, contract, min_data, direction):
    open_time.append(index_list[i].strftime('%Y-%m-%d %H:%M:%S'))
    open_time_digit.append(digit_time(index_list[i]))
    open_price.append(min_data['open_price_long'][i])
    direction.append('long')
    contract.append(min_data['contract'][i])
    open_flag = 1
    return open_time, open_time_digit, open_price, direction, contract, open_flag


def open_short(open_time, open_time_digit, index_list, i, open_price, contract, min_data, direction):
    open_time.append(index_list[i].strftime('%Y-%m-%d %H:%M:%S'))
    open_time_digit.append(digit_time(index_list[i]))
    open_price.append(min_data['open_price_short'][i])
    direction.append('short')
    contract.append(min_data['contract'][i])
    open_flag = -1
    return open_time, open_time_digit, open_price, direction, contract, open_flag


def statistic(commodity, min_data, open_symbol, close_symbol, stop_loss, backhand):
    open_time = []
    open_price = []
    direction = []
    close_time = []
    close_price = []
    open_time_digit = []
    close_time_digit = []
    contract = []
    hold_time = []
    pnl = []
    daily_pnl = 0
    daily_pnl_list = []
    daily_index = []
    open_flag = 0
    stop_profit_list = min_data['stop_profit']
    index_list = list(min_data.index)
    for i in range(min_data.shape[0] - 1):
        if min_data[open_symbol][i] == 1 and open_flag == 0:
            open_time, open_time_digit, open_price, direction, contract, open_flag = open_long(open_time, open_time_digit, index_list, i, open_price, contract, min_data, direction)
        if min_data[open_symbol][i] == -1 and open_flag == 0:
            open_time, open_time_digit, open_price, direction, contract, open_flag = open_short(open_time, open_time_digit, index_list, i, open_price, contract, min_data, direction)
        if min_data[close_symbol][i] != 0 and open_flag == 1:
            close_time.append(index_list[i].strftime('%Y-%m-%d %H:%M:%S'))
            close_time_digit.append(digit_time(index_list[i]))
            hold_time.append((close_time_digit[-1] - open_time_digit[-1])/100)
            if min_data[close_symbol][i] == 1:
                close_price.append(min_data['close'][i])
                pnl.append(close_price[-1] - open_price[-1])
                daily_pnl += close_price[-1] - open_price[-1]
                open_flag = 0
            elif min_data[close_symbol][i] == 2:
                pnl.append(stop_loss)
                close_price.append(open_price[-1] + stop_loss)
                daily_pnl += stop_loss
                open_flag = 0
            elif min_data[close_symbol][i] == 3:
                pnl.append(float(stop_profit_list[i]))
                close_price.append(open_price[-1] + stop_profit_list[i])
                daily_pnl += stop_profit_list[i]
                open_flag = 0
                if min_data[open_symbol][i] == -1 and backhand:
                    open_time, open_time_digit, open_price, direction, contract, open_flag = open_short(open_time, open_time_digit, index_list, i, open_price, contract, min_data, direction)
                    continue
        if min_data[close_symbol][i] != 0 and open_flag == -1:
            close_time.append(index_list[i].strftime('%Y-%m-%d %H:%M:%S'))
            close_time_digit.append(digit_time(index_list[i]))
            hold_time.append((close_time_digit[-1] - open_time_digit[-1])/100)
            if min_data[close_symbol][i] == 1:
                close_price.append(min_data['close'][i])
                pnl.append(-close_price[-1] + open_price[-1])
                daily_pnl += -close_price[-1] + open_price[-1]
                open_flag = 0
            elif min_data[close_symbol][i] == 2:
                pnl.append(stop_loss)
                close_price.append(open_price[-1] - stop_loss)
                daily_pnl += stop_loss
                open_flag = 0
            elif min_data[close_symbol][i] == 3:
                pnl.append(float(stop_profit_list[i]))
                close_price.append(open_price[-1] - stop_profit_list[i])
                daily_pnl += stop_profit_list[i]
                open_flag = 0
                if min_data[open_symbol][i] == 1 and backhand:
                    open_time, open_time_digit, open_price, direction, contract, open_flag = open_long(open_time, open_time_digit, index_list, i, open_price, contract, min_data, direction)
        bool_end_day = index_list[i].hour == 15 if commodity[-3:] != 'czc' else (index_list[i].hour == 14 and index_list[i].minute >= 59)
        if bool_end_day:
            daily_pnl_list.append(daily_pnl)
            date = dt.datetime(index_list[i].year, index_list[i].month, index_list[i].day)
            daily_index.append(date.strftime('%Y-%m-%d %H:%M:%S'))
            daily_pnl = 0
    times = len(open_price)
    average_return = sum(pnl) / times
    win_times = np.alen(np.array(pnl)[np.array(pnl) > 0])
    lose_times = np.alen(np.array(pnl)[np.array(pnl) <= 0])
    winning_rate = win_times / times
    sharp_ratio_daily = np.mean(daily_pnl_list)/np.std(daily_pnl_list)
    win_to_loss = abs(np.average(np.array(pnl)[np.array(pnl) >= 0])/np.average(np.array(pnl)[np.array(pnl) < 0]))
    trade_record = {'open_time': open_time, 'open_digit_time': open_time_digit, 'direction': direction, 'open_price': open_price, 'contract': contract, 'close_time': close_time, 'close_digit_time': close_time_digit, 'close_price': close_price,  'pnl': pnl}
    trade_statistic = {'commodity': commodity, 'times': times, 'average_return': average_return, 'win_times': win_times, 'lose_times': lose_times, 'win_rate': winning_rate, 'win_to_loss': win_to_loss, 'sharp_ratio_daily': sharp_ratio_daily}
    daily_statistic = {'date': daily_index, 'daily_pnl': daily_pnl_list}
    return trade_record, trade_statistic, daily_statistic


def excel_write(trade_record, trade_statistic, daily_statistic):
    work_book = xlwt.Workbook()
    sheet1 = work_book.add_sheet('trade_record')
    sheet2 = work_book.add_sheet('trade_statistic')
    sheet3 = work_book.add_sheet('daily_statistic')
    trade_record_keys = list(trade_record.keys())
    for i in range(0, len(trade_record_keys)):
        key = trade_record_keys[i]
        sheet1.write(0, i, key)
        for j in range(0, len(trade_record[key])):
            sheet1.write(j+1, i, trade_record[key][j])
    trade_statistic_key = list(trade_statistic.keys())
    for i in range(0, len(trade_statistic_key)):
        key = trade_statistic_key[i]
        sheet2.write(0, i, key)
        sheet2.write(1, i, trade_statistic[key])
    daily_statistic_keys = list(daily_statistic.keys())
    for i in range(0, len(daily_statistic_keys)):
        key = daily_statistic_keys[i]
        sheet3.write(0, i, key)
        for j in range(0, len(daily_statistic[key])):
            sheet3.write(j+1, i, str(daily_statistic[key][j]))
    commodity = trade_statistic['commodity']
    time_ = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    work_book.save('./back_test_result/' + commodity + '_trade_record_statistic_' + time_ + '.xls')
    return


# def back_test_with_initial_capital(init_capital, trade_record, commodity):
#     margin_fee = margin_fee_dict[commodity]
#     margin_rate = margin_fee[0]
#     fee = margin_fee[1]
#     multiplier = margin_fee[2]
#     for i in range(0, len(trade_record['open_time'])):
#

def statistic_main(commodity, min_data, open_symbol, close_symbol, stop_loss, backhand):
    trade_record_, trade_statistic_, daily_statistic_ = statistic(commodity, min_data, open_symbol, close_symbol, stop_loss, backhand)
    excel_write(trade_record_, trade_statistic_, daily_statistic_)
    return
