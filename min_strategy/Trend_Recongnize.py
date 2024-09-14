
from min_strategy.TrendLine import TrendLine


class Trend:
    def __init__(self, direc, lenth, chg, start_index, start_daily_index, last_high_low, trend_line, datetime, in_trend, wave_num=2):
        self.trend_direc = direc
        self.trend_lenth = lenth
        self.trend_chg = chg
        self.trend_start_index = start_index
        self.trend_start_daily_index = start_daily_index
        self.trend_start_datetime = datetime
        self.trend_last_high_low = last_high_low
        self.trend_line = trend_line
        self.in_trend = in_trend
        self.wave_num = wave_num
        self.wave_chg = []
        self.wave_gradient = []
        self.trend_pause = 0

    def max_chg(self, min_data):
        max_chg_ = self.trend_last_high_low - min_data['low'][self.trend_start_daily_index] if self.trend_direc == 1 else self.trend_last_high_low - min_data['high'][self.trend_start_daily_index]
        return max_chg_


class TrendManagement:
    def __init__(self):
        self.__last_up_trend = None
        self.__last_down_trend = None
        self.__last_cross_up_point = 0
        self.__last_cross_down_point = 0
        self.__in_up_trend = 0
        self.__in_down_trend = 0

    def trend_initial(self, min_data, board_point, iloc, plot):
        if len(board_point['max_min_price']) >= 3 and self.__in_up_trend == 0:
            if (min_data['close'][iloc] > board_point['max_min_price'][-2]) \
                    and (board_point['max_min_price'][-1] > board_point['max_min_price'][-3]) \
                    and board_point['cross_direc'][-1] == 1 \
                    and abs(board_point['wave_volatility'][-2]) > 0.75*abs(board_point['wave_volatility'][-3]) \
                    and abs(board_point['wave_volatility'][-1]) < 0.5 * abs(board_point['wave_volatility'][-2]):
                trend_chg = min_data['close'][iloc] - board_point['max_min_price'][-3]
                trend_direc = 1
                start_index = board_point['max_min_iloc'][-3]
                start_daily_index = self.iloc_to_daily_iloc(board_point['max_min_iloc'][-3], min_data)
                start_daytime = list(min_data.index)[start_daily_index]
                end_daily_index = self.iloc_to_daily_iloc(board_point['max_min_iloc'][-1], min_data)
                end_daytime = list(min_data.index)[end_daily_index]
                trend_lenth = iloc - start_index
                trend_last_high_low = min_data['close'][iloc]
                trend_datetime = list(min_data.index)[self.iloc_to_daily_iloc(start_index, min_data)]
                trend_line = TrendLine(board_point['max_min_iloc'][-3], board_point['max_min_iloc'][-1], board_point['max_min_price'][-3], board_point['max_min_price'][-1],
                                       'up', start_daytime, end_daytime)
                wave_chg1 = board_point['wave_volatility'][-2]
                wave_gradient1 = wave_chg1 / board_point['wave_len'][-2]
                wave_chg2 = min_data['high'][iloc] - board_point['max_min_price'][-1]
                wave_gradient2 = wave_chg2 / (iloc - board_point['max_min_iloc'][-1])

                plot.add_trace([start_daytime, end_daytime], [board_point['max_min_price'][-3], board_point['max_min_price'][-1]], 1)

                self.__last_cross_up_point = board_point['cross_iloc'][-1]
                self.__last_up_trend = Trend(trend_direc, trend_lenth, trend_chg, start_index, start_daily_index, trend_last_high_low, trend_line, trend_datetime, in_trend=1)
                self.__last_up_trend.wave_chg.extend([wave_chg1, wave_chg2])
                self.__last_up_trend.wave_gradient.extend([wave_gradient1, wave_gradient2])
                self.__in_up_trend = 1
        if len(board_point['max_min_price']) >= 3 and self.__in_down_trend == 0:
            if (min_data['close'][iloc] < board_point['max_min_price'][-2]) \
                    and (board_point['max_min_price'][-1] < board_point['max_min_price'][-3]) \
                    and board_point['cross_direc'][-1] == -1 \
                    and abs(board_point['wave_volatility'][-2]) > 0.75*abs(board_point['wave_volatility'][-3])\
                    and abs(board_point['wave_volatility'][-1]) < 0.5*abs(board_point['wave_volatility'][-2]):
                trend_chg = min_data['close'][iloc] - board_point['max_min_price'][-3]
                trend_direc = -1
                start_index = board_point['max_min_iloc'][-3]
                start_daily_index = self.iloc_to_daily_iloc(board_point['max_min_iloc'][-3], min_data)
                start_daytime = list(min_data.index)[start_daily_index]
                end_daily_index = self.iloc_to_daily_iloc(board_point['max_min_iloc'][-1], min_data)
                end_daytime = list(min_data.index)[end_daily_index]
                trend_lenth = iloc - start_index
                trend_last_high_low = min_data['close'][iloc]
                trend_datetime = list(min_data.index)[self.iloc_to_daily_iloc(start_index, min_data)]
                wave_chg1 = board_point['wave_volatility'][-2]
                wave_gradient1 = wave_chg1 / (board_point['cross_iloc'][-2] - board_point['max_min_iloc'][-2])
                wave_chg2 = min_data['low'][iloc] - board_point['max_min_price'][-1]
                wave_gradient2 = wave_chg2 / (iloc - self.iloc_to_daily_iloc(board_point['cross_iloc'][-1], min_data))

                self.__last_cross_up_point = board_point['cross_iloc'][-1]
                trend_line = TrendLine(board_point['max_min_iloc'][-3], board_point['max_min_iloc'][-1], board_point['max_min_price'][-3], board_point['max_min_price'][-1],
                                       'down', start_daytime, end_daytime)
                self.__last_down_trend = Trend(trend_direc, trend_lenth, trend_chg, start_index, start_daily_index, trend_last_high_low, trend_line, trend_datetime, in_trend=1)
                self.__last_down_trend.wave_chg.extend([wave_chg1, wave_chg2])
                self.__last_down_trend.wave_gradient.extend([wave_gradient1, wave_gradient2])
                self.__in_down_trend = 1
                plot.add_trace([start_daytime, end_daytime], [board_point['max_min_price'][-3], board_point['max_min_price'][-1]], -1)

    def in_trend(self, min_data, board_point, iloc):
        self.trend_end(min_data, iloc)
        self.trend_pause(min_data, board_point, iloc)
        self.trend_refresh(min_data, board_point, iloc)

    def trend_end(self, min_data, iloc):
        if self.__in_up_trend == 1:
            if min_data['low'][iloc] < self.__last_up_trend.trend_last_high_low - 0.5 * self.__last_up_trend.max_chg(min_data):
                self.__in_up_trend = 0
                self.__last_up_trend.in_trend = 0
        if self.__in_down_trend == 1:
            if min_data['high'][iloc] > self.__last_down_trend.trend_last_high_low - 0.5 * self.__last_down_trend.max_chg(min_data):
                self.__in_down_trend = 0
                self.__last_down_trend.in_trend = 0

    def trend_pause(self, min_data, board_point, iloc):
        if self.__in_up_trend == 1:
            if (board_point['cross_direc'][-1] == -1 and ((min_data['low'][iloc] < board_point['max_min_price'][-2] + 0.5*(board_point['max_min_price'][-1] - board_point['max_min_price'][-2])) or (board_point['max_min_price'][-1] < board_point['max_min_price'][-3]))) and self.__last_up_trend.in_trend == 1:
                self.__last_up_trend.trend_pause = 1
        if self.__in_down_trend == 1:
            if (board_point['cross_direc'][-1] == 1 and ((min_data['high'][iloc] > board_point['max_min_price'][-2] - 0.5*(+ 0.5*(board_point['max_min_price'][-2] - board_point['max_min_price'][-1]))) or (board_point['max_min_price'][-1] > board_point['max_min_price'][-3]))) and self.__last_down_trend.in_trend == 1:
                self.__last_down_trend.trend_pause = 1

    def trend_refresh(self, min_data, board_point, iloc):
        if self.__in_up_trend == 1:
            if board_point['cross_direc'][-1] == 1 and (min_data['high'][iloc] > self.__last_up_trend.trend_last_high_low):
                temp_gradient = (board_point['max_min_price'][-3] - board_point['max_min_price'][-1])/(board_point['max_min_iloc'][-3] - board_point['max_min_iloc'][-1])
                # 更新趋势线
                if temp_gradient > self.__last_up_trend.trend_line.gradient:
                    temp_trend_line = TrendLine(board_point['max_min_iloc'][-3], board_point['max_min_iloc'][-1], board_point['max_min_price'][-3], board_point['max_min_price'][-1],
                                                'up', list(min_data.index)[self.iloc_to_daily_iloc(board_point['max_min_iloc'][-3], min_data)], list(min_data.index)[self.iloc_to_daily_iloc(board_point['max_min_iloc'][-1], min_data)])
                    self.__last_up_trend.trend_line = temp_trend_line
                # 将暂停的趋势解除暂停
                if self.__last_up_trend.trend_pause == 1:
                    self.__last_up_trend.trend_pause = 0
                # 更新趋势的波段数量和波段长度、波段斜率
                if self.__last_cross_up_point != board_point['cross_iloc'][-1]:
                    self.__last_up_trend.wave_num += 1
                    self.__last_cross_up_point = board_point['cross_iloc'][-1]
                wave_chg = min_data['high'][iloc] - board_point['max_min_price'][-1]
                wave_gradient = wave_chg / (iloc - self.iloc_to_daily_iloc(board_point['cross_iloc'][-1], min_data))
                wave_num = self.__last_up_trend.wave_num
                if len(self.__last_up_trend.wave_chg) < wave_num:
                    self.__last_up_trend.wave_chg.append(wave_chg)
                    self.__last_up_trend.wave_gradient.append(wave_gradient)
                else:
                    self.__last_up_trend.wave_chg[wave_num - 1] = wave_chg
                    self.__last_up_trend.wave_gradient[wave_num - 1] = wave_gradient
            # 更新趋势长度、趋势大小
            self.__last_up_trend.trend_chg = min_data['close'][iloc] - board_point['max_min_price'][-3]
            self.__last_up_trend.trend_lenth = iloc - self.__last_up_trend.trend_start_index
            # 更新趋势最高点
            if min_data['close'][iloc] > self.__last_up_trend.trend_last_high_low:
                self.__last_up_trend.trend_last_high_low = min_data['close'][iloc]
        if self.__in_down_trend == 1:
            if board_point['cross_direc'][-1] == -1 and min_data['close'][iloc] < self.__last_down_trend.trend_last_high_low:
                temp_gradient = (board_point['max_min_price'][-3] - board_point['max_min_price'][-1]) / (board_point['max_min_iloc'][-3] - board_point['max_min_iloc'][-1])
                if temp_gradient < self.__last_down_trend.trend_line.gradient:
                    temp_trend_line = TrendLine(board_point['max_min_iloc'][-3], board_point['max_min_iloc'][-1], board_point['max_min_price'][-3], board_point['max_min_price'][-1],
                                                'down', list(min_data.index)[self.iloc_to_daily_iloc(board_point['max_min_iloc'][-3], min_data)], list(min_data.index)[self.iloc_to_daily_iloc(board_point['max_min_iloc'][-1], min_data)])
                    self.__last_down_trend.trend_line = temp_trend_line
                if self.__last_down_trend.trend_pause == 1:
                    self.__last_down_trend.trend_pause = 0
                if self.__last_cross_down_point != board_point['cross_iloc'][-1]:
                    self.__last_down_trend.wave_num += 1
                    self.__last_cross_down_point = board_point['cross_iloc'][-1]
                wave_chg = min_data['low'][iloc] - board_point['max_min_price'][-1]
                wave_gradient = wave_chg / (iloc - self.iloc_to_daily_iloc(board_point['cross_iloc'][-1], min_data))
                if len(self.__last_down_trend.wave_chg) < self.__last_down_trend.wave_num:
                    self.__last_down_trend.wave_chg.append(wave_chg)
                    self.__last_down_trend.wave_gradient.append(wave_gradient)
                else:
                    wave_num = self.__last_down_trend.wave_num
                    self.__last_down_trend.wave_chg[wave_num - 1] = wave_chg
                    self.__last_down_trend.wave_gradient[wave_num - 1] = wave_gradient

                self.__last_down_trend.trend_chg = min_data['close'][iloc] - board_point['max_min_price'][-3]
                self.__last_down_trend.trend_lenth = iloc - self.__last_down_trend.trend_start_index

                if min_data['close'][iloc] < self.__last_down_trend.trend_last_high_low:
                    self.__last_down_trend.trend_last_high_low = min_data['close'][iloc]

    def get_last_up_trend(self):
        return self.__last_up_trend

    def get_last_down_trend(self):
        return self.__last_down_trend

    @staticmethod
    def iloc_to_daily_iloc(iloc, min_data):
        return min_data['daily_iloc'][min_data['iloc'] == iloc][0]

