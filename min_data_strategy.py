import pickle
import pandas as pd
from min_data_strategy_statistic import statistic_main
import numpy as np
import math


def date_to_int(date_):
    date_ = int(date_[0:4] + date_[5:7] + date_[8:])
    return date_


def divergence(close, indicator, wave_cross):
    # 加入波段长度判断
    cross = wave_cross['cross']
    wave = wave_cross['wave']
    # close = wave_cross['max_min_price']
    wave_len = wave_cross['wave_len']
    wave_len_max_min = wave_len[wave_len != 0]
    wave_max_min = wave[cross != 0]
    cross_max_min = cross[cross != 0]
    wave_max_min = pd.concat([wave_max_min, cross_max_min], axis=1)
    wave_max_min_shift = wave_max_min.shift(1).dropna()
    wave_len_max_min_shift = wave_len_max_min.shift(1).dropna()
    wave_max_min_shift['close_max_min'] = list(close[list(wave_max_min_shift['wave'])])
    wave_max_min_shift['indicator_max_min'] = list(indicator[list(wave_max_min_shift['wave'])])
    wave_max_min_shift['wave_len_max_min_shift'] = wave_len_max_min_shift
    wave_max_min_shift['wave_len_max_min'] = wave_len_max_min
    wave_max_min_shift = wave_max_min_shift.drop(list(wave_max_min_shift.index)[0], axis=0)
    wave_max_min_shift = wave_max_min_shift.reindex(close.index).fillna(method='ffill')
    wave_max_min_shift['close'] = close
    wave_max_min_shift['indicator'] = indicator
    # & (wave_max_min_shift['indicator'] > wave_max_min_shift['indicator_max_min']) & (wave_max_min_shift['wave_len_max_min_shift'] > 10) & (wave_max_min_shift['wave_len_max_min_shift'] / wave_max_min_shift['wave_len_max_min'] > 2) & (wave_max_min_shift['wave_len_max_min'] > 5)
    divergence_bottom = (wave_max_min_shift['cross'] == 1) & (wave_max_min_shift['close'] < wave_max_min_shift['close_max_min']) & (wave_max_min_shift['indicator'] > wave_max_min_shift['indicator_max_min'])
    divergence_top = (wave_max_min_shift['cross'] == -1) & (wave_max_min_shift['close'] > wave_max_min_shift['close_max_min']) & (wave_max_min_shift['indicator'] < wave_max_min_shift['indicator_max_min'])
    divergence_ = pd.concat([divergence_bottom, divergence_top], axis=1, keys=['divergence_bottom', 'divergence_top'])
    return divergence_


def resistance_support(wave_cross_, min_data_, lag):
    max_min_price = wave_cross_[wave_cross_['cross'] != 0]
    max_min_price_valid = max_min_price[max_min_price['wave_len'] > 10]
    max_min_price_valid['contract'] = min_data_['contract'][max_min_price_valid.index]
    big_list = []
    big_list_index = []
    max_min_price_list = []
    max_min_price_index_list = []
    contract = max_min_price_valid['contract'][0]
    for i in range(0, max_min_price_valid.shape[0]):
        if max_min_price_valid['contract'][i] != contract:
            max_min_price_list = []
            max_min_price_index_list = []
            contract = max_min_price_valid['contract'][i]
        max_min_price_list.append(max_min_price_valid['max_min_price'][i])
        max_min_price_index_list.append(list(max_min_price_valid.index)[i])
        if len(max_min_price_list) > lag:
            max_min_price_list.pop(0)
            max_min_price_index_list.pop(0)
        big_list.append(max_min_price_list.copy())
        big_list_index.append(max_min_price_index_list.copy())
    max_min_price_dict = {'max_min_price': big_list, 'max_min_price_list': big_list_index}
    return max_min_price_dict


def last_3_resistance_support(wave_cross_, min_data_):
    wave_cross_max_min = wave_cross_[wave_cross_['cross'] != 0]
    lag_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    for lag in lag_list:
        min_data_ = shift_max_min(wave_cross_max_min, min_data_, lag)
    return min_data_


def golden_dead_cross(ma_short, ma_long):
    diff = ma_short - ma_long
    diff_last = diff.shift(1)
    golden_cross = (diff_last <= 0) & (diff > 0)
    dead_cross = (diff_last > 0) & (diff <= 0)
    golden_dead_cross_ = pd.concat([golden_cross, dead_cross], axis=1)
    golden_dead_cross_.columns = ['golden_cross', 'dead_cross']
    return golden_dead_cross_


def wave_distinguish(target_high, target_low, golden_dead_cross_):
    golden_cross = golden_dead_cross_['golden_cross']
    dead_cross = golden_dead_cross_['dead_cross']
    golden_cross = golden_cross + 0
    dead_cross = (dead_cross + 0) * -1
    cross = golden_cross + dead_cross
    cross_mid = cross[cross != 0]
    index_list = list(cross_mid.index)
    index_list_full = list(cross.index)
    index_loc = [index_list_full.index(x) for x in index_list]
    index_loc = pd.Series(index_loc, index=cross_mid.index)
    wave_len = (index_loc - index_loc.shift(1)).dropna()
    cross_mid = list(cross_mid)
    wave_high_list = []
    index_high_list = []
    index_low_list = []
    wave_low_list = []
    wave_iloc = []
    for i in range(1, len(index_list)):
        index = index_list[i]
        last_index = index_list[i-1]
        if cross_mid[i] == -1:
            max_iloc = target_high.loc[last_index:index].argmax()
            max_loc = list(target_high.loc[last_index:index].index)[max_iloc]
            wave_high_list.append(max_loc)
            index_high_list.append(index)
            # wave_iloc.append(list(target.index).index(max_loc))
        elif cross_mid[i] == 1:
            min_iloc = target_low.loc[last_index:index].argmin()
            min_loc = list(target_low.loc[last_index:index].index)[min_iloc]
            wave_low_list.append(min_loc)
            index_low_list.append(index)
            # wave_iloc.append(list(target.index).index(min_loc))
    # wave = pd.Series(wave_list, index=index_list[1:])
    wave_high = pd.Series(wave_high_list, index=index_high_list)
    wave_low = pd.Series(wave_low_list, index=index_low_list)
    # wave_iloc = pd.Series(wave_iloc, index=index_list[1:])
    wave = pd.concat([wave_high, wave_low], axis=0).sort_index(ascending=True)
    wave = wave[wave != 0]
    max_price = pd.Series(list(target_high[wave_high]), index=wave_high.index)
    min_price = pd.Series(list(target_low[wave_low]), index=wave_low.index)
    max_min_price = pd.concat([max_price, min_price], axis=0).sort_index(ascending=True)
    # max_min_price = pd.Series(list(target[wave]), index=wave.index)
    pnl = (max_min_price - max_min_price.shift(1))
    wave = wave.reindex(cross.index).fillna(0)
    # wave_iloc = wave_iloc.reindex(cross.index).fillna(0)
    max_min_price = max_min_price.reindex(cross.index).fillna(0)
    speed = pnl/wave_len
    pnl = pnl.reindex(cross.index).fillna(0)
    wave[index_list[0]] = index_list[0]
    wave_len = wave_len.reindex(cross.index).fillna(0)
    speed = speed.reindex(cross.index).fillna(0)
    wave_cross = pd.concat([cross, wave, wave_len, max_min_price, pnl, speed], keys=['cross', 'wave', 'wave_len', 'max_min_price', 'pnl', 'speed'], axis=1)
    return wave_cross


def wave_cross_iloc(wave_cross_, min_data_):
    wave_cross_ = wave_cross_[wave_cross_['cross'] != 0]
    wave_cross_['cross_index'] = list(wave_cross_.index)
    index_list = list(min_data_.index)
    cross_index_list = list(wave_cross_['cross_index'])
    cross_loc_list = [index_list.index(x) for x in cross_index_list]
    max_min_loc_list = [index_list.index(x) for x in list(wave_cross_['wave'])]
    wave_cross_['cross_iloc'] = cross_loc_list
    wave_cross_['wave_iloc'] = max_min_loc_list
    wave_cross_ = wave_cross_.reindex(min_data_.index).fillna(0)
    return wave_cross_


def dist_to_cross_point(wave_cross_, min_data_):
    wave_cross_max_min = wave_cross_[wave_cross_['cross'] != 0]
    wave_cross_max_min = wave_cross_max_min.reindex(min_data_.index).fillna(method='ffill')
    wave_cross_max_min['iloc'] = list(range(0, wave_cross_max_min.shape[0]))
    wave_cross_max_min['dist_to_cross_point'] = wave_cross_max_min['iloc'] - wave_cross_max_min['cross_iloc']
    wave_cross_max_min['pnl_inter_wave'] = min_data_['close'] - wave_cross_max_min['max_min_price']
    wave_cross_max_min['speed'] = wave_cross_max_min['pnl'] / wave_cross_max_min['dist_to_cross_point']
    return wave_cross_max_min


def upper_lower_ma_last_lag(min_data_, lag, jump):
    symbol_list = ['ma5', 'ma10', 'ma20']
    for i in range(0, len(symbol_list)):
        min_data_['upper_' + symbol_list[i]] = ((min_data_['open'] > min_data_[symbol_list[i]]) & (min_data_['close'] > min_data_[symbol_list[i]])) + 0
        min_data_['lower_' + symbol_list[i]] = ((min_data_['open'] < min_data_[symbol_list[i]]) & (min_data_['close'] < min_data_[symbol_list[i]])) + 0
        min_data_['support_' + symbol_list[i]] = ((min_data_['open'] > min_data_[symbol_list[i]]) & (min_data_['open'] <= min_data_['close']) & (abs(min_data_['low'] - min_data_[symbol_list[i]]) < jump * 1.5)) + 0
        min_data_['resistance_' + symbol_list[i]] = ((min_data_['open'] < min_data_[symbol_list[i]]) & (min_data_['open'] >= min_data_['close']) & (abs(min_data_['high'] - min_data_[symbol_list[i]]) < jump * 1.5)) + 0
        min_data_['upper_' + symbol_list[i] + '_percentage'] = (min_data_['upper_' + symbol_list[i]].rolling(lag).sum()/lag)
        min_data_['lower_' + symbol_list[i] + '_percentage'] = (min_data_['lower_' + symbol_list[i]].rolling(lag).sum()/lag)
        min_data_['support_' + symbol_list[i] + '_times'] = min_data_['support_' + symbol_list[i]].rolling(lag).sum()
        min_data_['resistance_' + symbol_list[i] + '_times'] = min_data_['resistance_' + symbol_list[i]].rolling(lag).sum()
    return min_data_


def upper_lower_ma_percentage(min_data_, wave_cross_):
    # 太耗时，暂时不用
    wave_cross_max_min = wave_cross_[wave_cross_['cross'] != 0]
    symbol_list = ['ma5', 'ma10', 'ma20']
    index_list = list(wave_cross_max_min.index)
    percentage_index = []
    for i in range(0, len(symbol_list)):
        locals()['upper_' + symbol_list[i]] = ((min_data_['open'] > min_data_[symbol_list[i]]) & (min_data_['close'] > min_data_[symbol_list[i]])) + 0
        locals()['lower_' + symbol_list[i]] = ((min_data_['open'] < min_data_[symbol_list[i]]) & (min_data_['close'] < min_data_[symbol_list[i]])) + 0
        locals()['percentange_upper_' + symbol_list[i]] = []
        locals()['percentange_lower_' + symbol_list[i]] = []
    for i in range(0, wave_cross_max_min.shape[0] - 1):
        print(i)
        for j in range(0, min_data_.loc[index_list[i]:index_list[i+1]].shape[0]):
            for k in range(0, len(symbol_list)):
                locals()['percentange_upper_' + symbol_list[k]].append((locals()['upper_' + symbol_list[k]].loc[index_list[i]:index_list[i + 1]].iloc[0:j].sum()) / (j + 1))
                locals()['percentange_lower_' + symbol_list[k]].append((locals()['lower_' + symbol_list[k]].loc[index_list[i]:index_list[i + 1]].iloc[0:j].sum()) / (j + 1))
    upper_lower_percentage_dict = {}
    for i in range(0, len(symbol_list)):
        upper_lower_percentage_dict.update({'upper_' + symbol_list[i] + '_percentage': locals()['percentange_upper_' + symbol_list[i]]})
        upper_lower_percentage_dict.update({'lower_' + symbol_list[i] + '_percentage': locals()['percentange_lower_' + symbol_list[i]]})
    return upper_lower_percentage_dict


def shift_max_min(wave_cross_max_min, min_data_, lag):
    wave_cross_shift = wave_cross_max_min.shift(lag).reindex(min_data_.index).fillna(method='ffill')
    min_data_['wave_len_shift' + str(lag)] = wave_cross_shift['wave_len']
    min_data_['wave_shift' + str(lag)] = wave_cross_shift['wave']
    min_data_['cross_shift' + str(lag)] = wave_cross_shift['cross']
    min_data_['cross_iloc_shift' + str(lag)] = wave_cross_shift['cross_iloc']
    min_data_['wave_iloc_shift' + str(lag)] = wave_cross_shift['wave_iloc']
    min_data_['cross_shift' + str(lag)] = wave_cross_shift['cross']
    min_data_['max_min_price_shift' + str(lag)] = wave_cross_shift['max_min_price']
    min_data_['pnl_shift' + str(lag)] = wave_cross_shift['pnl']
    return min_data_


def data_combine(min_data_target, min_data_prime, factor):
    # 将长级别k线的数据填充到短k线上
    time_interval = min_data_target['time_interval'][-1]
    min_data_target = min_data_target.reindex(min_data_prime.index)
    min_data_target['open'].fillna(method='bfill', inplace=True)
    min_data_target.fillna(method='ffill', inplace=True)
    min_data_prime[time_interval + '_' + factor] = min_data_target[factor]
    return min_data_prime


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


def ma_combine(min_data_dict_):
    min_data_1 = min_data_dict_['min_data_1']
    min_data_5 = min_data_dict_['min_data_5']
    min_data_15 = min_data_dict_['min_data_15']
    min_data_30 = min_data_dict_['min_data_30']
    min_data_60 = min_data_dict_['min_data_60']
    daily_data = min_data_dict_['daily_data']
    min_data_1 = data_combine(min_data_5, min_data_1, 'ma5')
    min_data_1 = data_combine(min_data_5, min_data_1, 'ma10')
    min_data_1 = data_combine(min_data_5, min_data_1, 'ma20')
    min_data_1 = data_combine(min_data_5, min_data_1, 'ma200')
    min_data_1 = data_combine(min_data_15, min_data_1, 'ma5')
    min_data_1 = data_combine(min_data_15, min_data_1, 'ma10')
    min_data_1 = data_combine(min_data_15, min_data_1, 'ma20')
    min_data_1 = data_combine(min_data_15, min_data_1, 'ma200')
    min_data_1 = data_combine(min_data_30, min_data_1, 'ma5')
    min_data_1 = data_combine(min_data_30, min_data_1, 'ma10')
    min_data_1 = data_combine(min_data_30, min_data_1, 'ma20')
    min_data_1 = data_combine(min_data_30, min_data_1, 'ma200')
    min_data_1 = data_combine(min_data_60, min_data_1, 'ma5')
    min_data_1 = data_combine(min_data_60, min_data_1, 'ma10')
    min_data_1 = data_combine(min_data_60, min_data_1, 'ma20')
    min_data_1 = data_combine(min_data_60, min_data_1, 'ma200')
    min_data_1 = data_combine(daily_data, min_data_1, 'ma5')
    min_data_1 = data_combine(daily_data, min_data_1, 'ma10')
    min_data_1 = data_combine(daily_data, min_data_1, 'ma20')
    min_data_1 = data_combine(daily_data, min_data_1, 'ma200')
    return min_data_1
    

def trade_time(v):
    # if not ((v.hour == 9 and 0 <= v.minute <= 5) or (v.hour == 11 and 25 <= v.minute <= 30) or (v.hour == 13 and 30 <= v.minute <= 35) or (v.hour == 15) or (v.hour == 14 and 57 <= v.minute <= 59) or (v.hour == 2 and 27 <= v.minute <= 30) or (v.hour == 22 and 57 <= v.minute <= 59) or (v.hour == 23)):
    if not ((v.hour == 11 and 25 <= v.minute <= 30) or (v.hour == 15) or (v.hour == 14 and 57 <= v.minute <= 59) or (v.hour == 22 and 57 <= v.minute <= 59) or (v.hour == 23)):
        return True
    else:
        return False


def max_min_price_in_wave(min_data_, wave_cross_max_min):
    max_ = []
    min_ = []
    dist_list = list(wave_cross_max_min['dist_to_cross_point'])
    close_list = list(min_data_['close'])
    for i in range(0, wave_cross_max_min.shape[0]):
        if np.isnan(dist_list[i]):
            max_.append(close_list[i])
            min_.append(close_list[i])
        else:
            max_.append(max(close_list[int(i - dist_list[i]):i + 1]))
            min_.append(min(close_list[int(i - dist_list[i]):i + 1]))
    min_data_['inter_wave_max'] = max_
    min_data_['inter_wave_min'] = min_
    return min_data_


def open_bool(min_data_, parameter_dict_):
    # 做趋势线斜率，引入每段趋势线斜率。
    # 标注趋势线生效与否。
    # 动态止损，以趋势线的斜率作为准绳。硬止损的数量动态变化，同时也可以以趋势线的斜率变化作为退出参考。
    # 引入一分钟线最高点、最低点的趋势线
    # 平仓方式：1.阻力位平仓， 2.达到前一浪长度时平仓 3.整数位平仓 4.死叉平仓
    jump = parameter_dict_['jump']
    round_num = round_(jump)
    golden_dead_cross_5_10 = golden_dead_cross(min_data_['ma10'], min_data_['ma20'])
    golden_dead_cross_5_10 = golden_dead_cross(min_data_['close'], min_data_['ma5'])
    wave_cross_5_10 = wave_distinguish(min_data_['high'], min_data_['low'], golden_dead_cross_5_10)
    wave_cross_5_10 = wave_cross_iloc(wave_cross_5_10, min_data_)
    min_data_ = last_3_resistance_support(wave_cross_5_10, min_data_)
    wave_cross_max_min_10_20 = dist_to_cross_point(wave_cross_5_10, min_data_)
    min_data_ = upper_lower_ma_last_lag(min_data_, 20, jump)
    min_data_ = max_min_price_in_wave(min_data_, wave_cross_max_min_10_20)
    min_data_['trade_time'] = min_data_['datetime'].apply(lambda v: trade_time(v))
    min_data_['loc'] = min_data_.index
    min_data_['iloc'] = list(range(0, min_data_.shape[0]))
    # min_data_['low_trend_line'] = (min_data_['low'] - min_data_['low'].shift(2))
    # min_data_['high_trend_line'] = (min_data_['high'] - min_data_['high'].shift(2))
    # min_data_['close_on_trend'] = abs(min_data_['low'] + min_data_['low_trend_line'] - min_data_['close']) < 1*jump
    # min_data_['low_trend_long'] = min_data_['low_trend_line'] > 5 * jump
    # min_data_['low_trend_short'] = min_data_['high_trend_line'] < -5 * jump
    # min_data_['open_price_long'] = min_data_['close']
    # min_data_['open_price_short'] = min_data_['close']
    # min_data_['strategy1_open_long'] = (min_data_['trade_time'] & min_data_['close_on_trend'] & min_data_['low_trend_long'] + 0) * -1
    # min_data_['strategy1_open_short'] = (min_data_['trade_time'] & min_data_['close_on_trend'] & min_data_['low_trend_short'] + 0)
    # min_data_['strategy1_open'] = min_data_['strategy1_open_long'] + min_data_['strategy1_open_short']
    # min_data_['touch_ma10_long'] = (wave_cross_max_min_10_20['cross'].shift(1) == 1) & (min_data_['ma10'].shift(1) > min_data_['ma20'].shift(1)) & (min_data_['ma5_gradient'].shift(1) > 0) & (min_data_['low'] <= (min_data_['ma5'] + min_data_['ma5_gradient'] + 1*jump).shift(1)) & (min_data_['open'] >= (min_data_['ma5'] + min_data_['ma5_gradient'] + 1*jump).shift(1)) & (wave_cross_max_min_10_20['max_min_price'].shift(1) > min_data_['max_min_price_shift2'].shift(1)) & (min_data_['pnl_shift1'].shift(1) > 20*jump) & (min_data_['pnl_shift1'].shift(1) > abs(2*wave_cross_max_min_10_20['pnl'].shift(1))) & (min_data_['wave_len_shift1'].shift(1) > 20) & (wave_cross_max_min_10_20['wave_len'].shift(1) > 5) & (wave_cross_max_min_10_20['wave_len'].shift(1) <= min_data_['wave_len_shift1'].shift(1))
    # min_data_['touch_ma10_short'] = (wave_cross_max_min_10_20['cross'].shift(1) == -1) & (min_data_['ma10'].shift(1) < min_data_['ma20'].shift(1)) & (min_data_['ma5_gradient'].shift(1) < 0) & (min_data_['high'] >= (min_data_['ma5'] + min_data_['ma5_gradient'] - 1*jump).shift(1)) & (min_data_['open'] <= (min_data_['ma5'] + min_data_['ma5_gradient'] - 1*jump).shift(1)) & (wave_cross_max_min_10_20['max_min_price'].shift(1) < min_data_['max_min_price_shift2'].shift(1)) & (min_data_['pnl_shift1'].shift(1) < -20*jump) & (abs(min_data_['pnl_shift1'].shift(1)) > 2*wave_cross_max_min_10_20['pnl'].shift(1)) & (min_data_['wave_len_shift1'].shift(1) > 20) & (wave_cross_max_min_10_20['wave_len'].shift(1) > 5) & (wave_cross_max_min_10_20['wave_len'].shift(1) <= min_data_['wave_len_shift1'].shift(1))
    # min_data_['touch_ma10_long'] = (wave_cross_max_min_10_20['cross'].shift(1) == -1) & (min_data_['open'] >= min_data_['open_price_long']) & (min_data_['low'] < min_data_['open_price_long']) & (wave_cross_max_min_10_20['max_min_price'].shift(1) > min_data_['max_min_price_shift2'].shift(1) + 5) & (min_data_['max_min_price_shift2'].shift(1) > min_data_['max_min_price_shift4'].shift(1) + 5) & (abs(min_data_['max_min_price_shift1'] - min_data_['max_min_price_shift3']).shift(1) < 3)
    # min_data_['touch_ma10_short'] = (wave_cross_max_min_10_20['cross'].shift(1) == 1) & (min_data_['open'] <= min_data_['open_price_short']) & (min_data_['high'] > min_data_['open_price_short']) & (wave_cross_max_min_10_20['max_min_price'].shift(1) < min_data_['max_min_price_shift2'].shift(1) - 5) & (min_data_['max_min_price_shift2'].shift(1) < min_data_['max_min_price_shift4'].shift(1) - 5) & (abs(min_data_['max_min_price_shift1'] - min_data_['max_min_price_shift3']).shift(1) < 3)
    min_data_['trend_line_gradient1'] = (min_data_['max_min_price_shift1'] - min_data_['max_min_price_shift5'])/(min_data_['wave_iloc_shift1'] - min_data_['wave_iloc_shift5'])
    min_data_['trend_line_gradient2'] = (wave_cross_max_min_10_20['max_min_price'] - min_data_['max_min_price_shift4'])/(wave_cross_max_min_10_20['wave_iloc'] - min_data_['wave_iloc_shift4'])
    min_data_['dis_to_last_max_min'] = min_data_['iloc'] - min_data_['wave_iloc_shift1']
    min_data_['dis_max_min_2_4'] = (min_data_['wave_iloc_shift2'] - min_data_['wave_iloc_shift4']).shift(1)
    min_data_['open_price_long'] = round((wave_cross_max_min_10_20['max_min_price'] + min_data_['trend_line_gradient2'] * min_data_['dis_to_last_max_min']).shift(1), round_num)
    min_data_['open_price_short'] = round((wave_cross_max_min_10_20['max_min_price'] + min_data_['trend_line_gradient2'] * min_data_['dis_to_last_max_min']).shift(1), round_num)
    min_data_['open_price_long_position'] = (wave_cross_max_min_10_20['cross'].shift(1) == 1) & (min_data_['open'] >= min_data_['open_price_long']) & (min_data_['low'] < (min_data_['open_price_long']))
    min_data_['open_price_short_position'] = (wave_cross_max_min_10_20['cross'].shift(1) == -1) & (min_data_['open'] <= min_data_['open_price_short']) & (min_data_['high'] > (min_data_['open_price_short']))
    min_data_['touch_ma10_long'] = min_data_['open_price_long_position'] & (min_data_['trend_line_gradient2'].shift(1) > 1 * jump) & (min_data_['max_min_price_shift2'].shift(1) >= (min_data_['max_min_price_shift4'].shift(1) + min_data_['trend_line_gradient2'].shift(1) * min_data_['dis_max_min_2_4']) - 1*jump) & (min_data_['max_min_price_shift2'].shift(1) <= (min_data_['max_min_price_shift4'].shift(1) + min_data_['trend_line_gradient2'].shift(1) * min_data_['dis_max_min_2_4']) + 1*jump)
    min_data_['touch_ma10_short'] = min_data_['open_price_short_position'] & (min_data_['trend_line_gradient2'].shift(1) < -1 * jump) & (min_data_['max_min_price_shift2'].shift(1) <= (min_data_['max_min_price_shift4'].shift(1) + min_data_['trend_line_gradient2'].shift(1) * min_data_['dis_max_min_2_4']) + 1*jump) & (min_data_['max_min_price_shift2'].shift(1) >= (min_data_['max_min_price_shift4'].shift(1) + min_data_['trend_line_gradient2'].shift(1) * min_data_['dis_max_min_2_4']) - 1*jump)
    min_data_['strategy1_open_long'] = ((min_data_['trade_time'] & min_data_['touch_ma10_long']) + 0) * -1
    min_data_['strategy1_open_short'] = (min_data_['trade_time'] & min_data_['touch_ma10_short'] + 0)
    min_data_['strategy1_open'] = min_data_['strategy1_open_long'] + min_data_['strategy1_open_short']
    return min_data_


def close_bool(min_data_):
    min_data_['strategy1_close'] = min_data_['trade_time'] == np.False_
    min_data_['strategy1_close'] = (min_data_['strategy1_close']) + 0
    return min_data_


def open_signal_process(min_data_dict_, parameter_dict_):
    # min_data_1 = ma_combine(min_data_dict_)
    min_data_1 = min_data_dict_['min_data_1']
    # min_data_1 = data_process(min_data_dict_, min_data_1)
    # min_data_1 = min_data_dict['min_data_1']
    min_data_1 = open_bool(min_data_1, parameter_dict_)
    min_data_1 = close_bool(min_data_1)
    min_data_1 = moving_stop_loss(min_data_1, 'strategy1_open', 'strategy1_close', parameter_dict_)
    return min_data_1


def data_process(min_data_dict_, min_data_1):
    min_data_1 = data_combine(min_data_dict_['min_data_15'], min_data_1, 'open')
    min_data_1 = data_combine(min_data_dict_['min_data_15'], min_data_1, 'ma5_gradient')
    min_data_1 = data_combine(min_data_dict_['min_data_15'], min_data_1, 'k')
    return min_data_1


def moving_stop_loss(min_data_, symbol_open, symbol_close, parameter_dict_):
    backhand_ = parameter_dict_['backhand']
    close = 0
    open_close_flag = 0
    min_data_['stop_profit'] = [0.0]*min_data_.shape[0]
    # trend_gradient = min_data_['trend_line_gradient1']
    paper_pnl_list = []
    stop_loss_threshold = parameter_dict_['stop_loss_threshold']
    moving_stop_loss_threshold = parameter_dict_['moving_stop_loss_threshold']
    moving_stop_loss_percentage = parameter_dict_['moving_stop_loss_percentage']
    cost_fee_threshold = parameter_dict_['cost_fee_threshold']
    jump = parameter_dict_['jump']
    round_num = round_(jump)
    stop_loss = 0
    for i in range(1, min_data_.shape[0]):
        if min_data_[symbol_open][i] == 1 and open_close_flag == 0:
            close = round(min_data_['open_price_long'][i], round_num)
            stop_loss = round(min(min_data_['open'][i], min_data_['close'][i]), round_num)
            open_close_flag = 1
            continue
        elif min_data_[symbol_open][i] == -1 and open_close_flag == 0:
            close = round(min_data_['open_price_short'][i], round_num)
            stop_loss = round(max(min_data_['open'][i], min_data_['close'][i]), round_num)
            open_close_flag = -1
            continue
        if open_close_flag == 1:
            paper_pnl_list.append(min_data_['high'][i] - close)
            paper_loss = min_data_['low'][i] - close
            if len(paper_pnl_list) > 1:
                if max(paper_pnl_list) > moving_stop_loss_threshold and paper_loss <= moving_stop_loss_percentage * max(paper_pnl_list):
                    min_data_[symbol_close][i] = 3
                    min_data_['stop_profit'][i] = float(str(round(moving_stop_loss_percentage * max(paper_pnl_list), round_num)))
                    open_close_flag = 0
                    paper_pnl_list = []
                elif max(paper_pnl_list) < moving_stop_loss_threshold and (paper_loss <= cost_fee_threshold) and (max(paper_pnl_list) > cost_fee_threshold):
                    min_data_[symbol_close][i] = 3
                    min_data_['stop_profit'][i] = cost_fee_threshold - jump
                    open_close_flag = 0
                    paper_pnl_list = []
            # if (min_data_['low_trend_line'][i] <= 0) and (min_data_['close'][i] < min_data_['open'][i]):
            #     min_data_[symbol_close][i] = 3
            #     min_data_['stop_profit'][i] = min_data_['close'][i] - close
            #     open_close_flag = 0
            #     paper_pnl_list = []
            # if min_data_['low'][i] < stop_loss:
            #     min_data_[symbol_close][i] = 3
            #     min_data_['stop_profit'][i] = stop_loss - close
            #     open_close_flag = 0
            #     paper_pnl_list = []
            if paper_loss <= stop_loss_threshold:
                min_data_[symbol_close][i] = 2
                open_close_flag = 0
                paper_pnl_list = []
            if min_data_[symbol_open][i] == -1:
                min_data_[symbol_close][i] = 3
                min_data_['stop_profit'][i] = round(min_data_['open_price_short'][i], round_num) - close
                open_close_flag = 0
                paper_pnl_list = []
                if backhand_:
                    close = round(min_data_['open_price_short'][i], round_num)
                    open_close_flag = -1
                    paper_pnl_list = []
                    continue
            if min_data_[symbol_close][i] == 1:
                open_close_flag = 0
                paper_pnl_list = []
        if open_close_flag == -1:
            paper_pnl_list.append(close - min_data_['low'][i])
            paper_loss = close - min_data_['high'][i]
            if len(paper_pnl_list) > 1:
                if max(paper_pnl_list) > moving_stop_loss_threshold and paper_loss <= moving_stop_loss_percentage * max(paper_pnl_list):
                    min_data_[symbol_close][i] = 3
                    min_data_['stop_profit'][i] = float(str(round(moving_stop_loss_percentage * max(paper_pnl_list), round_num)))
                    open_close_flag = 0
                    paper_pnl_list = []
                elif max(paper_pnl_list) < moving_stop_loss_threshold and (paper_loss <= cost_fee_threshold) and (max(paper_pnl_list) > cost_fee_threshold):
                    min_data_[symbol_close][i] = 3
                    min_data_['stop_profit'][i] = cost_fee_threshold - jump
                    open_close_flag = 0
                    paper_pnl_list = []
            if min_data_[symbol_close][i] == 1:
                open_close_flag = 0
                paper_pnl_list = []
            # if (min_data_['high_trend_line'][i] >= 0) and (min_data_['close'][i] > min_data_['open'][i]):
            #     min_data_[symbol_close][i] = 3
            #     min_data_['stop_profit'][i] = close - min_data_['close'][i]
            #     open_close_flag = 0
            #     paper_pnl_list = []
            # if min_data_['high'][i] > stop_loss:
            #     min_data_[symbol_close][i] = 3
            #     min_data_['stop_profit'][i] = close - stop_loss
            #     open_close_flag = 0
            #     paper_pnl_list = []
            if paper_loss <= stop_loss_threshold:
                min_data_[symbol_close][i] = 2
                open_close_flag = 0
                paper_pnl_list = []
            if min_data_[symbol_open][i] == 1:
                min_data_[symbol_close][i] = 3
                min_data_['stop_profit'][i] = close - round(min_data_['open_price_long'][i], round_num)
                open_close_flag = 0
                paper_pnl_list = []
                if backhand_:
                    close = round(min_data_['open_price_short'][i], round_num)
                    open_close_flag = 1
                    paper_pnl_list = []
    return min_data_


if __name__ == '__main__':
    commodity = 'oi.czc'
    start_date = "2020-06-01"
    end_date = "2021-06-18"
    backhand = True
    jump = 1
    parameter_dict = {'jump': jump, 'stop_loss_threshold': -8 * jump, 'moving_stop_loss_threshold': 30 * jump, 'moving_stop_loss_percentage': 0.7, 'cost_fee_threshold': 6*jump, 'backhand': backhand}
    file_name = commodity + '_' + str(date_to_int(start_date)) + '-' + str(date_to_int(end_date)) + '_min_data_dict.pkl'
    with open('./min_data/' + file_name, 'rb') as f:
        min_data_dict = pickle.load(f)
    min_data = open_signal_process(min_data_dict, parameter_dict)
    statistic_main(commodity, min_data, 'strategy1_open', 'strategy1_close', parameter_dict['stop_loss_threshold'], backhand)
