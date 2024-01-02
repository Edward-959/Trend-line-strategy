import numpy as np
import pandas as pd


def kline_calculate(min_data):
    min_data['real_body'] = min_data['close'] - min_data['open']
    min_data['upper_shadow'] = (min_data['high'] - min_data[['close', 'open']].max(axis=1)).abs()
    min_data['lower_shadow'] = (min_data[['close', 'open']].min(axis=1) - min_data['low']).abs()
    min_data['shadow_ratio'] = (min_data['upper_shadow'] + min_data['lower_shadow']) / min_data['real_body'].abs()
    min_data['lower_shadow_ratio'] = min_data['lower_shadow'] / abs(min_data['real_body'])
    min_data['upper_shadow_ratio'] = min_data['upper_shadow'] / abs(min_data['real_body'])
    min_data['shadow_ratio'] = min_data['shadow_ratio'].replace(np.inf, 10000)
    min_data['lower_shadow_ratio'] = min_data['lower_shadow_ratio'].replace(np.inf, 10000)
    min_data['upper_shadow_ratio'] = min_data['upper_shadow_ratio'].replace(np.inf, 10000)
    return min_data


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
    wave_cross_max_min['speed_inter_wave'] = wave_cross_max_min['pnl'] / wave_cross_max_min['dist_to_cross_point']
    for key in list(wave_cross_max_min.columns):
        min_data_[key] = wave_cross_max_min[key]
    return min_data_


def ma_calculate(min_data, ma_para_list):
    for ma in ma_para_list:
        min_data['ma' + str(ma)] = min_data['close'].rolling(ma).mean()
    return min_data


def macd(min_data, short_lag, long_lag, diff_lag):
    ema_12 = [min_data['close'][0]]
    ema_26 = [min_data['close'][0]]
    dif = [0]
    dea = [0]
    for i in range(1, min_data.shape[0]):
        ema_12_ele = ema_12[i-1] * (short_lag - 1) / (short_lag + 1) + min_data['close'][i] * 2 / (short_lag + 1)
        ema_26_ele = ema_26[i-1] * (long_lag - 1) / (long_lag + 1) + min_data['close'][i] * 2 / (long_lag + 1)
        dif_ele = ema_12_ele - ema_26_ele
        dea_ele = dea[i-1] * (diff_lag - 1)/(diff_lag + 1) + dif_ele * 2/(diff_lag + 1)
        ema_12.append(ema_12_ele)
        ema_26.append(ema_26_ele)
        dif.append(dif_ele)
        dea.append(dea_ele)
    min_data['ema_12'] = ema_12
    min_data['ema_26'] = ema_26
    min_data['dif'] = dif
    min_data['dea'] = dea
    return min_data


def gradient_calculate(target, lag):
    gradient_ = (target - target.shift(lag))/lag
    return gradient_


def gradient(min_data, lag):
    min_data['gradient'] = gradient_calculate(min_data['close'], lag)
    min_data['ma5_gradient'] = gradient_calculate(min_data['ma5'], lag)
    min_data['ma10_gradient'] = gradient_calculate(min_data['ma10'], lag)
    min_data['ma20_gradient'] = gradient_calculate(min_data['ma20'], lag)
    # min_data['vwap_gradient'] = gradient_calculate(min_data['vwap_200'], lag)

    return min_data


def obv(min_data):
    p_n = min_data['close'] - min_data['close'].shift(1)
    p_n_volume = (p_n / abs(p_n) * min_data['volume']).fillna(0)
    min_data['obv'] = p_n_volume + p_n_volume.shift(1)
    return min_data


def kd(min_data, k_lag, d_lag):
    min_data['k'] = (min_data['close'] - min_data['low'].rolling(k_lag).min())/(min_data['high'].rolling(k_lag).max() - min_data['low'].rolling(k_lag).min()) * 100
    min_data['k'] = min_data['k'].rolling(k_lag).mean()
    min_data['d'] = min_data['k'].rolling(d_lag).mean()
    return min_data


def rsi(min_data, lag):
    pnl = min_data['close'] - min_data['close'].shift(1)
    pnl_pos = pnl * (pnl > 0)
    pnl_neg = pnl * (pnl < 0)
    min_data['rsi'] = pnl_pos.rolling(lag).sum() / (pnl_pos.rolling(lag).sum() + abs(pnl_neg.rolling(lag).sum())) * 100
    return min_data


def cci(min_data, lag):
    tp = (min_data['high'] + min_data['low'] + min_data['close']) / 3
    ma = tp.rolling(lag).mean()
    md = tp.rolling(lag).std()
    min_data['cci'] = (tp - ma) / md / 0.015
    return min_data


def vwap(min_data, lag):
    min_data['vwap_' + str(lag)] = (min_data['close'] * min_data['volume']).rolling(lag).sum() / min_data['volume'].rolling(lag).sum()
    return min_data


def daily_high_low_mean(min_data):
    close_list = list(min_data['close'])
    volume_list = list(min_data['volume'])
    index_list = list(min_data['close'].index)
    daily_high = []
    daily_low = []
    daily_mean = []
    daily_vwap = []
    bond_future_list = ['t.cfe', 'tf.cfe']
    contract = min_data['contract'][0]
    new_day_index = 0
    for i in range(0, len(close_list)):
        daily_high.append(max(close_list[new_day_index:i + 1]))
        daily_low.append(min(close_list[new_day_index:i + 1]))
        daily_mean.append(sum(close_list[new_day_index:i + 1]) / len(close_list[new_day_index:i + 1]))
        daily_vwap.append(sum(list(np.array(close_list[new_day_index:i + 1]) * np.array(volume_list[new_day_index:i + 1]))) / np.sum(volume_list[new_day_index:i + 1]))
        if (index_list[i].hour == 15 and contract not in bond_future_list) or (index_list[i].hour == 15 and index_list[i].minute == 15 and contract in bond_future_list):
            new_day_index = i + 1
    min_data['daily_high'] = daily_high
    min_data['daily_low'] = daily_low
    min_data['daily_mean'] = daily_mean
    min_data['daily_vwap'] = daily_vwap
    return min_data


def bolling(min_data, lag, multi):
    min_data['bolling'] = min_data['close'].rolling(lag).mean()
    min_data['upper'] = min_data['bolling'] + multi * min_data['close'].rolling(lag).std()
    min_data['lower'] = min_data['bolling'] - multi * min_data['close'].rolling(lag).std()
    return min_data


def adx(min_data, lag):
    up = min_data['high'] - min_data['high'].shift(1)
    down = min_data['low'].shift(1) - min_data['low']
    down_pos = down[down > 0].reindex(down.index).fillna(0)
    up_pos = up[up > 0].reindex(up.index).fillna(0)
    dm_pos = up[up > down_pos].reindex(up.index).fillna(0)
    dm_neg = down[down > up_pos].reindex(down.index).fillna(0)
    tr = pd.concat([min_data['high'] - min_data['low'], abs(min_data['high'] - min_data['close'].shift(1)), abs(min_data['low'] - min_data['close'].shift(1))], axis=1).max(axis=1)
    di_pos = dm_pos.rolling(lag).mean() / tr.rolling(lag).mean() * 100
    di_neg = dm_neg.rolling(lag).mean() / tr.rolling(lag).mean() * 100
    dx = (di_pos - di_neg) / (di_pos + di_neg) * 100
    min_data['adx'] = dx.rolling(lag).mean()
    return min_data


def technical_calculate(min_data):
    ma_para_list_ = [5, 10, 20, 30, 50, 200, 250]
    min_data = ma_calculate(min_data, ma_para_list_)
    min_data = kline_calculate(min_data)
    min_data = macd(min_data, 12, 26, 9)
    min_data = obv(min_data)
    min_data = kd(min_data, 9, 3)
    min_data = rsi(min_data, 12)
    min_data = cci(min_data, 20)
    min_data = bolling(min_data, 20, 3)
    min_data = adx(min_data, 10)
    golden_dead_cross_close_5 = golden_dead_cross(min_data['close'], min_data['ma5'])
    wave_cross_close_5 = wave_distinguish(min_data['high'], min_data['low'], golden_dead_cross_close_5)
    wave_cross_close_5 = wave_cross_iloc(wave_cross_close_5, min_data)
    min_data = dist_to_cross_point(wave_cross_close_5, min_data)
    # min_data = daily_high_low_mean(min_data)
    min_data = vwap(min_data, 200)
    min_data = gradient(min_data, 1)
    return min_data


if __name__ == '__main__':
    data_name = 'ETHUSDT-1m-2023-11'
    data: pd.DataFrame = pd.read_csv('min_data_crypto/' + data_name + '.csv')
    columns: list = ['open_time','open','high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'count',
                     'taker_buy_volume', 'taker_buy_quote_volume', 'ignore']
    data.columns = columns
    data = technical_calculate(data)
    data.to_csv('min_data_crypto/' + data_name + '-washed.csv')