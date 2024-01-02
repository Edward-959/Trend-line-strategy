"""

20210830:
1.通过向上向下趋势线gradient绝对值判断趋势方向
2.15分钟rsi>80,1分钟<20策略
3.建立一整套体系,包括趋势判断、持仓中监控等等

20210904:
1.不同的趋势，不同的开仓位置、不同的回撤点，对应不同的平仓方式，现在的三类平仓太简单。
趋势有加速、减速、匀速等，如果发现开仓的时刻趋势之前有所加速，就要快平仓，因为不可持续
同样，显著降速的趋势也要快速平仓，不可以将敞口放大。
只有匀速的趋势能保持长久。

整个波段在前低上方、下方的比例
波段的涨幅、涨速
触及不同均线的速度

20210913:
靠连续上涨/下跌形态以及上涨下跌的速度来判断开平仓点
用alpha因子做因子模型

"""

import pickle
from min_strategy.TrendLine import TrendLineManagement
import pandas as pd
from min_strategy.Trend_Recongnize import TrendManagement
from min_strategy.TradeManagement import TradeManangement
from min_strategy.excel_write import excel_write
from min_strategy.util import round_
from min_strategy.BoardPoint import BoardPoint
from min_data_strategy import data_combine
import math
import numpy as np


def date_to_int(date_):
    date_ = int(date_[0:4] + date_[5:7] + date_[8:])
    return date_


class MinDataStrategy:
    def __init__(self, min_data_, para_dict):
        self.__min_data = min_data_
        self.__daily_high = 0
        self.__daily_low = 10000000
        self.__last_daily_high = 0
        self.__last_daily_low = 0
        self.__last_daily_high_index = 0
        self.__last_daily_low_index = 0
        self.__daily_high_index = 0
        self.__daily_low_index = 0
        self.__daily_high_index = 0
        self.__daily_low_index = 0
        self.__jump = para_dict['jump']
        self.__round_num = round_(self.__jump)
        self.__commodity = para_dict['commodity']
        self.__short_symb = para_dict['short_symb']
        self.__long_symb = para_dict['long_symb']
        # 开平仓相关
        self.__open_high_index = 0
        self.__open_low_index = 0
        self.__open_high = 100000000
        self.__open_low = 0
        self.__open_long_trend_line = None
        self.__open_short_trend_line = None
        self.__open_long_k = 1000
        self.__open_short_k = 1000
        # 连涨连跌
        self.__continuous_up = 1
        self.__continuous_down = 1
        self.__last_continuous_up = 0
        self.__last_continuous_down = 0
        self.__last_continuous_up_index = 0
        self.__last_continuous_down_index = 0
        self.__in_up_continuous = 0
        self.__in_down_continuous = 0
        # 止损位
        self.__stop_loss_price_long = 0
        self.__stop_loss_price_short = 0
        self.__open_long_cross_iloc = 0
        self.__open_short_cross_iloc = 0
        # # 波段
        # board_point.board_point = {}
        # board_point.init_board_point()

    @staticmethod
    def new_half_day(index):
        return False

    @staticmethod
    def new_day(index):
        bool_end_day = (index.hour == 0 and index.minute == 4)
        return bool_end_day

    def trade_time(self, v):
        return True


    # or (v.hour == 23)
    def reset_daily_high_low(self):
        self.__daily_high = 0
        self.__daily_low = 10000000
        self.__last_daily_high = 0
        self.__last_daily_low = 10000000
        self.__daily_high_index = 0
        self.__daily_low_index = 0

    def set_daily_high_low(self, i):
        if self.__min_data['high'][i] >= self.__daily_high - 1*self.__jump:
            if self.__min_data['iloc'][i] - self.__daily_high_index > 90:
                self.__last_daily_high = self.__daily_high
                self.__last_daily_high_index = self.__daily_high_index
            self.__daily_high = self.__min_data['high'][i]
            self.__daily_high_index = self.__min_data['iloc'][i]
        if self.__min_data['low'][i] <= self.__daily_low + 1*self.__jump:
            if self.__min_data['iloc'][i] - self.__daily_low_index > 90:
                self.__last_daily_low = self.__daily_low
                self.__last_daily_low_index = self.__daily_low_index
            self.__daily_low = self.__min_data['low'][i]
            self.__daily_low_index = self.__min_data['iloc'][i]

    @staticmethod
    def iloc_to_daily_iloc(iloc, min_data):
        return min_data['daily_iloc'][min_data['iloc'] == iloc][0]

    def open_long_strategy(self, trend_management: TrendManagement, iloc):
        open_bool = 0
        open_price = 0
        # and (int(str(self.__min_data['iloc'][iloc] - board_point.board_point['max_min_iloc'][-1])) > int(str(board_point.board_point['max_min_iloc'][-1] - board_point.board_point['max_min_iloc'][-2])))
        # if len(board_point.board_point['cross_direc']) >= 2:
        #     last_high = board_point.board_point['max_min_price'][-1]
        #     last_low = min(self.__min_data['low'][self.iloc_to_daily_iloc(board_point.board_point['cross_iloc'][-1], self.__min_data):iloc+1])
        #     if board_point.board_point['cross_direc'][-1] == 1 and (self.__min_data['open'][iloc] < last_high) and (self.__min_data['close'][iloc] > last_high)\
        #         and self.__min_data['real_body'][iloc] > 0.3 * (last_high-last_low) and (last_high - last_low) > 12*jump:
        #             open_bool = 1
        #             open_price = self.__min_data['close'][iloc]
        #             self.__stop_loss_price_long = round(0.5*(last_high - last_low) + last_low, self.__round_num)
        up_trend = trend_management.get_last_up_trend()
        down_trend = trend_management.get_last_down_trend()
        if up_trend is not None and iloc-1 > up_trend.trend_start_daily_index and board_point.board_point['cross_direc'][-1] == 1:
            cross_daily_iloc = self.iloc_to_daily_iloc(board_point.board_point['cross_iloc'][-1], self.__min_data)
            if iloc > cross_daily_iloc:
                high_low_inter_wave = max(self.__min_data['high'][cross_daily_iloc:iloc])
            else:
                high_low_inter_wave = self.__min_data['high'][iloc]
            chg_inter_wave = high_low_inter_wave - board_point.board_point['max_min_price'][-1]
            max_chg = up_trend.max_chg(self.__min_data)
            # and up_trend.wave_num <= 3 \
            #     and abs(self.__min_data['close'][iloc] - up_trend.trend_last_high_low) < 0.2 * abs(max_chg) \
            #     and 0.2 * abs(chg_inter_wave) < abs(self.__min_data['close'][iloc] - high_low_inter_wave) < 0.4 * abs(chg_inter_wave) \
            if self.__min_data['low'][iloc] <= self.__min_data['ma10'][iloc] and (self.__min_data['close'][iloc] >= self.__min_data['ma10'][iloc])\
                and up_trend.in_trend == 1 and up_trend.trend_pause == 0 and (down_trend is None or (down_trend is not None and down_trend.in_trend == 0))\
                    and self.__min_data['real_body'][iloc] <= 3*jump:
                open_bool = 1
                open_price = self.__min_data['close'][iloc]
                self.__stop_loss_price_long = board_point.board_point['max_min_price'][-1]
                self.__open_long_cross_iloc = board_point.board_point['cross_direc'][-1]
        return open_bool, open_price


    def open_short_strategy(self, trend_management, iloc):
        open_bool = 0
        open_price = 0
        # if len(board_point.board_point['cross_direc']) >= 2:
        #     last_low = board_point.board_point['max_min_price'][-2]
        #     last_high = board_point.board_point['max_min_price'][-1]
        #     if board_point.board_point['cross_direc'][-1] == -1 and (self.__min_data['close'][iloc] < last_low) and (self.__min_data['open'][iloc] > last_low) \
        #             and abs(self.__min_data['real_body'][iloc]) > 0.3 * (last_high - last_low) and (last_high - last_low) > 12 * jump:
        #             open_bool = 1
        #             open_price = self.__min_data['close'][iloc]
        #             self.__stop_loss_price_short = round(0.5*(last_high - last_low) + last_low, self.__round_num)
        # up_trend = trend_management.get_last_up_trend()
        # down_trend = trend_management.get_last_down_trend()
        # if down_trend is not None and iloc-1 > down_trend.trend_start_daily_index and board_point.board_point['cross_direc'][-1] == -1:
        #     cross_daily_iloc = self.iloc_to_daily_iloc(board_point.board_point['cross_iloc'][-1], self.__min_data)
        #     if iloc > cross_daily_iloc:
        #         high_low_inter_wave = min(self.__min_data['low'][cross_daily_iloc:iloc])
        #     else:
        #         high_low_inter_wave = self.__min_data['low'][iloc]
        #     chg_inter_wave = high_low_inter_wave - board_point.board_point['max_min_price'][-1]
        #     max_chg = down_trend.max_chg(self.__min_data)
        #     # and down_trend.wave_num <= 3 \
        #     #     and abs(self.__min_data['close'][iloc] - down_trend.trend_last_high_low) < 0.2 * abs(max_chg) \
        #     #     and 0.2 * abs(chg_inter_wave) < abs((self.__min_data['close'][iloc] - high_low_inter_wave)) < 0.4 * abs(chg_inter_wave) \
        #     if self.__min_data['high'][iloc] >= self.__min_data['ma20'][iloc] and (self.__min_data['close'][iloc] <= self.__min_data['ma20'][iloc])\
        #         and down_trend.in_trend == 1 and down_trend.trend_pause == 0 and (up_trend is None or (up_trend is not None and up_trend.in_trend == 0))\
        #             and self.__min_data['real_body'][iloc] >= -3*jump:
        #             open_bool = 1
        #             open_price = self.__min_data['close'][iloc]
        #             self.__stop_loss_price_short = board_point.board_point['max_min_price'][-1]
        #             self.__open_short_cross_iloc = board_point.board_point['cross_direc'][-1]
        return open_bool, open_price

    def close_long_strategy(self, trend_management, trade_management: TradeManangement, iloc):
        float_profit = trade_management.get_float_profit()
        float_loss = trade_management.get_float_loss()
        start_index = trade_management.get_last_start_index()
        open_price = trade_management.get_start_price()
        up_trend = trend_management.get_last_up_trend()
        stop_loss, moving_stop_loss = trade_management.daily_high_low_stop_loss(self.__daily_high, self.__daily_low, self.__jump, self.__round_num)
        close_num = 0
        close_price = 0
        if len(float_profit) > 1 and close_num == 0:
            if max(float_profit[0:-1]) > 10*self.__jump and self.__min_data['low'][iloc] - open_price <= 0.5 * max(float_profit[0:-1]):
                close_num = 1
                close_price = round(0.5 * max(float_profit), self.__round_num) + open_price
        # if self.__min_data['ma5'][iloc] - self.__min_data['ma10'][iloc] < 0:
        #     close_num = 1
        #     close_price = self.__min_data['close'][iloc]
        if len(float_loss) != 0 and close_num == 0:
            if self.__min_data['low'][iloc] <= self.__stop_loss_price_long:
                close_num = 2
                close_price = self.__stop_loss_price_long
        # if len(float_profit) > 1 and close_num == 0 and up_trend is not None:
        #     if max(float_profit[0:-1]) > 5*self.__jump and (up_trend.wave_gradient[-1] < up_trend.wave_gradient[-2]) \
        #             and (self.__min_data['low'][iloc] - open_price < 3*self.__jump):
        #         close_num = 4
        #         close_price = open_price + 3*self.__jump
        # if len(float_profit) > 1 and close_num == 0:
        #     if 5 < max(float_profit[0:-1]) <= moving_stop_loss*self.__jump and self.__min_data['low'][iloc] - open_price <= 3*jump:
        #         close_num = 2
        #         close_price = 3*jump + open_price
        # if len(float_loss) != 0 and close_num == 0:
        #     if float_loss[-1] <= -15*self.__jump:
        #         close_num = 5
        #         close_price = open_price - 15*self.__jump
        if not self.trade_time(list(self.__min_data.index)[iloc]) and close_num == 0:
            close_num = 3
            close_price = self.__min_data['close'][iloc]
        return close_num, close_price

    def close_short_strategy(self, trend_management, trade_management:TradeManangement, iloc):
        float_profit = trade_management.get_float_profit()
        float_loss = trade_management.get_float_loss()
        start_index = trade_management.get_last_start_index()
        open_price = trade_management.get_start_price()
        down_trend = trend_management.get_last_down_trend()
        stop_loss, moving_stop_loss = trade_management.daily_high_low_stop_loss(self.__daily_high, self.__daily_low, self.__jump, self.__round_num)
        close_num = 0
        close_price = 0
        if len(float_profit) > 1 and close_num == 0:
            if max(float_profit[0:-1]) > 10*jump and open_price - self.__min_data['high'][iloc] <= 0.5 * max(float_profit[0:-1]):
                close_num = 1
                close_price = open_price - round(0.5 * max(float_profit), self.__round_num)
        # if self.__min_data['ma5'][iloc] - self.__min_data['ma10'][iloc] > 0:
        #     close_num = 1
        #     close_price = self.__min_data['close'][iloc]
        # if len(float_profit) > 1 and close_num == 0 and down_trend is not None:
        #     if max(float_profit[0:-1]) > 5*self.__jump and down_trend.wave_gradient[-1] < down_trend.wave_gradient[-2] \
        #             and (open_price - self.__min_data['high'][iloc] < 3*self.__jump):
        #         close_num = 4
        #         close_price = open_price - 3*self.__jump
        if len(float_loss) != 0 and close_num == 0:
            if self.__min_data['high'][iloc] >= self.__stop_loss_price_short:
                close_num = 2
                close_price = self.__stop_loss_price_short
        # if len(float_profit) > 1 and close_num == 0:
        #     if 5 < max(float_profit[0:-1]) <= moving_stop_loss*jump and (open_price - self.__min_data['high'][iloc] <= 3*jump):
        #         close_num = 2
        #         close_price = open_price - 3*jump
        # if len(float_loss) != 0 and close_num == 0:
        #     if float_loss[-1] <= -15 * self.__jump:
        #         close_num = 5
        #         close_price = open_price + 15*self.__jump
        if not self.trade_time(list(self.__min_data.index)[iloc]) and close_num == 0:
            close_num = 3
            close_price = self.__min_data['close'][iloc]
        return close_num, close_price

    def continuous_up_down(self, iloc):
        if self.__min_data['high'][iloc] >= self.__min_data['high'][iloc - 1] \
                and self.__min_data['low'][iloc] >= self.__min_data['low'][iloc-1]\
                and self.__min_data['close'][iloc] >= self.__min_data['open'][iloc]:
            self.__continuous_up += 1
            self.__in_up_continuous = 1
        else:
            if self.__in_up_continuous == 1:
                self.__last_continuous_up = self.__continuous_up
                self.__last_continuous_up_index = iloc-1
                self.__continuous_up = 1
                self.__in_up_continuous = 0
        if self.__min_data['high'][iloc] <= self.__min_data['high'][iloc - 1] \
                and self.__min_data['low'][iloc] <= self.__min_data['low'][iloc-1]\
                and self.__min_data['close'][iloc] <= self.__min_data['open'][iloc]:
            self.__continuous_down += 1
            self.__in_down_continuous = 1
        else:
            if self.__in_down_continuous == 1:
                self.__last_continuous_down = self.__continuous_down
                self.__last_continuous_down_index = iloc-1
                self.__continuous_down = 1
                self.__in_down_continuous = 0

    def open_strategy(self, trend_management, iloc):
        open_long_bool, open_long_price = self.open_long_strategy(trend_management, iloc)
        open_short_bool, open_short_price = self.open_short_strategy(trend_management, iloc)
        if open_long_bool == 1 and self.trade_time(list(self.__min_data.index)[iloc]):
            return True, 'buy', open_long_price
        elif open_short_bool == 1 and self.trade_time(list(self.__min_data.index)[iloc]):
            return True, 'sell', open_short_price
        else:
            return False, None, 0

    def close_strategy(self,  iloc, trade_management, trend_management):
        # 当务之急是利用趋势线做几个平仓策略。
        # 如果是顺趋势线方向开仓，趋势线被破时就应当出场。
        # 如果是利用趋势线被突破后的阻挡效应，则这条趋势线被重新突破时止损，或者临近的上升趋势线被突破后止损
        direction = trade_management.get_last_direction()
        close_long_num, close_long_price = self.close_long_strategy(trend_management, trade_management, iloc)
        close_short_num, close_short_price = self.close_short_strategy(trend_management, trade_management, iloc)
        if close_long_num != 0 and direction == 'buy':
            return close_long_num, 'sell', close_long_price
        elif close_short_num != 0 and direction == 'sell':
            return close_short_num, 'buy', close_short_price
        else:
            return 0, None, 0

    def open_close_model(self, trade_management, trend_management, i):
        open_bool = 0
        close_num = 0
        close_price = 0
        open_price = 0
        datetime = list(self.__min_data.index)[i]
        open_close_flag = trade_management.get_open_close_flag()
        if open_close_flag == 0:
            open_bool, direction, open_price = self.open_strategy(trend_management, i)
        else:
            trade_management.calc_float_profit_loss(self.__min_data.iloc[i, :])
            close_num, direction, close_price = self.close_strategy(i, trade_management, trend_management)
        trade_management.trade_management(self.__min_data.iloc[i, :], open_bool, close_num, direction, self.new_day(list(self.__min_data.index)[i]), datetime, close_price, open_price)

    def main_calculate(self, trade_management_, board_point_):
        index_list = list(self.__min_data.index)
        trend_management = TrendManagement()
        for i in range(0, self.__min_data.shape[0]):
            datetime = list(self.__min_data.index)[i]
            print(datetime)
            if self.new_half_day(index_list[i]):
                self.reset_daily_high_low()
            # 当close在ma5上方时，不画新的上升趋势线，调整过去的上升趋势线。同时，找寻最高点画新的下降趋势线
            if i >= 1:
                if self.__min_data['contract'][i] != self.__min_data['contract'][i-1]:
                    self.reset_daily_high_low()
                if self.__min_data[self.__short_symb][i] > self.__min_data[self.__long_symb][i]:
                    if self.__min_data[self.__short_symb][i-1] <= self.__min_data[self.__long_symb][i-1] and self.__min_data[self.__short_symb][i] > self.__min_data[self.__long_symb][i]:
                        board_point_.set_board_point(1, self.__min_data['iloc'][i], self.__min_data)
                if self.__min_data[self.__short_symb][i] <= self.__min_data[self.__long_symb][i]:
                    if self.__min_data[self.__short_symb][i-1] > self.__min_data[self.__long_symb][i-1] and self.__min_data[self.__short_symb][i] <= self.__min_data[self.__long_symb][i]:
                        board_point_.set_board_point(-1, self.__min_data['iloc'][i], self.__min_data)

                self.open_close_model(trade_management_, trend_management, i)
            trend_management.trend_initial(self.__min_data, board_point.board_point, i)
            trend_management.in_trend(self.__min_data, board_point.board_point, i)
            self.set_daily_high_low(i)
            self.continuous_up_down(i)


if __name__ == '__main__':
    commodity = 'ETHUSDT'
    start_date = "2023-11-01"
    end_date = "2023-12-01"
    jump = 1
    dir: str = '../min_data_crypto/'
    time_class = '1m'
    month = '2023-11'
    data_path = dir + commodity + "-" + time_class + "-" + month + '-washed.csv'
    parameter_dict = {'jump': jump, 'commodity': commodity, 'short_symb': 'ma5', 'long_symb': 'ma10'}
    min_data_1 = pd.read_csv(data_path)
    min_data_1['iloc'] = list(range(0, min_data_1.shape[0]))
    min_data_1['daily_iloc'] = list(range(0, min_data_1.shape[0]))
    min_data_1['jump'] = jump
    min_data_1['contract'] = [commodity] * min_data_1.shape[0]
    index = min_data_1['close_time'].map(lambda x: pd.to_datetime(x, unit='ms'))
    min_data_1.index = index
    trade_management = TradeManangement(commodity)
    board_point = BoardPoint()
    min_data_strategy = MinDataStrategy(min_data_1, parameter_dict)
    min_data_strategy.main_calculate(trade_management, board_point)
    trade_record, daily_record, trade_statistic_ = trade_management.data_collect()
    excel_write(trade_record, trade_statistic_, daily_record)

