

import numpy as np


class TrendLine:
    def __init__(self, start_index, end_index, start_price, end_price, up_down_flag, start_time, end_time, is_inuse=True, cross_index=0, support_times=0):
        # 趋势线的属性：首先两点确定一条趋势线，决定趋势线的位置和斜率。第五个参数是标定是下跌趋势线还是上涨趋势线，
        # 第六个参数标定趋势线是否生效（注意并不是失效趋势线就要删除，失去支撑作用后可能还有阻挡作用），最后一个参数是
        # 价格穿越趋势线的次数。规定穿越两次（注意是在不同的波段里）这条趋势线即失效。
        self.start_index = start_index
        self.end_index = end_index
        self.start_time = start_time
        self.end_time = end_time
        self.start_price = start_price
        self.end_price = end_price
        self.up_down_flag = up_down_flag
        self.is_inuse = is_inuse
        self.cross_index = cross_index
        self.support_times = support_times
        self.gradient = (self.end_price - self.start_price) / (self.end_index - self.start_index)
        self.trend_price = None
        self.trend_price_list = None
        self.last_gradient = None
        self.adapt_times = 0
        self.cross_back_times = 0
        self.cross_times = 0

    def trend_price_calculate(self, iloc):
        self.trend_price = self.end_price + (iloc - self.end_index) * self.gradient
        return self.trend_price

    def trend_price_list_calculate(self, iloc):
        self.trend_price_list = [x * self.gradient + self.start_price for x in range(0, iloc - self.start_index + 1)]


class TrendLineManagement:
    def __init__(self):
        self.__daily_accelerate_down_trend_line = {}
        self.__daily_accelerate_up_trend_line = {}
        self.__last_up_trend_line = None
        self.__crossed_up_trend_line = None
        self.__crossed_up_trend_line1 = None
        self.__last_down_trend_line = None
        self.__crossed_down_trend_line = None
        self.__crossed_down_trend_line1 = None
        self.__last_accelerate_up_trend_line = None
        self.__last_accelerate_down_trend_line = None
        self.__crossed_accelerate_up_trend_line = None
        self.__crossed_accelerate_down_trend_line = None

    @staticmethod
    def __trend_line_support(trend_line, min_data_slice):
        if trend_line.up_down_flag == 'up' and abs(min_data_slice['low'] - trend_line.trend_price) < 1 * min_data_slice['jump']:
            return True
        elif trend_line.up_down_flag == 'down' and abs(min_data_slice['high'] - trend_line.trend_price) < 1 * min_data_slice['jump']:
            return True
        else:
            return False

    @staticmethod
    def __cross_trend_line(trend_line, min_data_slice):
        if trend_line.up_down_flag == 'up' and min_data_slice['low'] < (trend_line.trend_price - 1*min_data_slice['jump']):
            return True
        elif trend_line.up_down_flag == 'down' and min_data_slice['high'] > (trend_line.trend_price + 1*min_data_slice['jump']):
            return True
        else:
            return False

    @staticmethod
    def __adapt_trend_line(trend_line, min_data_slice):
        if trend_line.up_down_flag == 'up' and min_data_slice['low'] < (trend_line.trend_price - 1*min_data_slice['jump']) and (min_data_slice['low'] >= (trend_line.trend_price - 1*min_data_slice['jump'])):
            return True
        elif trend_line.up_down_flag == 'down' and min_data_slice['high'] > (trend_line.trend_price + 1*min_data_slice['jump']) and (min_data_slice['high'] <= (trend_line.trend_price + 1*min_data_slice['jump'])):
            return True
        else:
            return False

    @staticmethod
    def __trend_line_accelerate(trend_line, max_min_iloc, max_min_price):
        if trend_line.up_down_flag == 'up' and (max_min_price - trend_line.start_price)/(max_min_iloc - trend_line.start_index) > trend_line.gradient:
            return True
        elif trend_line.up_down_flag == 'down' and (max_min_price - trend_line.start_price)/(max_min_iloc - trend_line.start_index) < trend_line.gradient:
            return True
        else:
            return False

    @staticmethod
    def temp_trend_line_crossed(temp_trend_line, min_data, iloc):
        if temp_trend_line.up_down_flag == 'up':
            return sum((min_data['low'][temp_trend_line.start_index:iloc + 1] > (np.array(temp_trend_line.trend_price_list) - 0.5 * min_data['jump'][0])) + 0)
        elif temp_trend_line.up_down_flag == 'down':
            return sum((min_data['high'][temp_trend_line.start_index:iloc + 1] < (np.array(temp_trend_line.trend_price_list) + 0.5 * min_data['jump'][0])) + 0)

    @staticmethod
    def __high_low_return(up_down_flag):
        if up_down_flag == 'up':
            return 'low'
        else:
            return 'high'

    def set_start_point(self, min_data, board_point):
        return

    def set_trend_line(self, daily_high_low_index, daily_high_low_price, board_point, up_down_flag, min_data, iloc):
        # 创建当出现新的极值点时，考虑画一条新的趋势线。
        # 考虑两个问题，一是当前极值点刚好落在之前的趋势线上，之前的趋势线可以沿用；二是新趋势线会穿过k线，即上升趋势发生了加速，需要引出加速趋势线。
        if board_point['max_min_iloc'][-1] > daily_high_low_index:
            if locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'] is None:
                cover_num_list = []
                for k in range(board_point['cross_iloc'][-2], board_point['cross_iloc'][-1] + 1):
                    if k != daily_high_low_index:
                        temp_trend_line = TrendLine(daily_high_low_index, k, daily_high_low_price, min_data[self.__high_low_return(up_down_flag)][k], up_down_flag, list(min_data.index)[daily_high_low_index], list(min_data.index)[k], is_inuse=True)
                        temp_trend_line.trend_price_list_calculate(iloc)
                        cover_num = self.temp_trend_line_crossed(temp_trend_line, min_data, iloc)
                        cover_num_list.append(cover_num)
                max_cover_num = max(cover_num_list)
                max_loc = np.where(np.array(cover_num_list) == max_cover_num)[-1][-1]
                k = board_point['cross_iloc'][-2] + max_loc
                temp_trend_line = TrendLine(daily_high_low_index, k, daily_high_low_price, min_data[self.__high_low_return(up_down_flag)][k], up_down_flag, list(min_data.index)[daily_high_low_index], list(min_data.index)[k], is_inuse=True)

                locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'] = temp_trend_line
            else:
                locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].trend_price_calculate(iloc)
                locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].trend_price_list_calculate(iloc)
                cover_num_list = []
                for k in range(board_point['cross_iloc'][-2], board_point['cross_iloc'][-1] + 1):
                    if k != daily_high_low_index:
                        temp_trend_line = TrendLine(daily_high_low_index, k, daily_high_low_price, min_data[self.__high_low_return(up_down_flag)][k], up_down_flag, list(min_data.index)[daily_high_low_index], list(min_data.index)[k], is_inuse=True)
                        temp_trend_line.trend_price_list_calculate(iloc)
                        cover_num = self.temp_trend_line_crossed(temp_trend_line, min_data, iloc)
                        cover_num_list.append(cover_num)
                max_cover_num = max(cover_num_list)
                max_loc = np.where(np.array(cover_num_list) == max_cover_num)[-1][-1]
                k = board_point['cross_iloc'][-2] + max_loc
                temp_trend_line = TrendLine(daily_high_low_index, k, daily_high_low_price, min_data[self.__high_low_return(up_down_flag)][k], up_down_flag, list(min_data.index)[daily_high_low_index], list(min_data.index)[k], is_inuse=True)
                last_cover_num = self.temp_trend_line_crossed(locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'], min_data, iloc)
                if (last_cover_num == max_cover_num) and (last_cover_num == iloc - locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].start_index):
                    locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].support_times += 1
                elif self.temp_trend_line_crossed(locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'], min_data, iloc) < max_cover_num or (locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].start_index != daily_high_low_index):
                    if (temp_trend_line.gradient > 0 and up_down_flag == 'up') or (temp_trend_line.gradient < 0 and up_down_flag == 'down'):
                        if locals()['self'].__dict__['_TrendLineManagement__crossed_' + up_down_flag + '_trend_line'] is not None:
                            locals()['self'].__dict__['_TrendLineManagement__crossed_' + up_down_flag + '_trend_line1'] = locals()['self'].__dict__['_TrendLineManagement__crossed_' + up_down_flag + '_trend_line']
                        locals()['self'].__dict__['_TrendLineManagement__crossed_' + up_down_flag + '_trend_line'] = locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line']
                        locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'] = temp_trend_line
                        locals()['self'].__dict__['_TrendLineManagement__last_accelerate_' + up_down_flag + '_trend_line'] = None
                        locals()['self'].__dict__['_TrendLineManagement__crossed_accelerate_' + up_down_flag + '_trend_line'] = None
                        locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].last_gradient = locals()['self'].__dict__['_TrendLineManagement__crossed_' + up_down_flag + '_trend_line'].gradient
                        if locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].start_index == locals()['self'].__dict__['_TrendLineManagement__crossed_' + up_down_flag + '_trend_line'].start_index:
                            if (abs((locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].last_gradient / locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].gradient) - 1)) < 0.1:
                                locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].support_times = locals()['self'].__dict__['_TrendLineManagement__crossed_' + up_down_flag + '_trend_line'].support_times + 1
                                locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].adapt_times = locals()['self'].__dict__['_TrendLineManagement__crossed_' + up_down_flag + '_trend_line'].adapt_times
                            else:
                                locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].adapt_times = locals()['self'].__dict__['_TrendLineManagement__crossed_' + up_down_flag + '_trend_line'].adapt_times + 1
                                locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].support_times = locals()['self'].__dict__['_TrendLineManagement__crossed_' + up_down_flag + '_trend_line'].support_times

                elif (temp_trend_line.gradient > locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].gradient > 0) \
                        or (temp_trend_line.gradient < locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].gradient < 0):
                    if locals()['self'].__dict__['_TrendLineManagement__last_accelerate_' + up_down_flag + '_trend_line'] is None:
                        temp_start_index = locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].end_index
                        temp_start_price = locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].end_price
                        locals()['self'].__dict__['_TrendLineManagement__last_accelerate_' + up_down_flag + '_trend_line'] = TrendLine(temp_start_index, board_point['max_min_iloc'][-1], temp_start_price, board_point['max_min_price'][-1], up_down_flag, list(min_data.index)[temp_start_index], list(min_data.index)[board_point['max_min_iloc'][-1]], is_inuse=True)
                    else:
                        locals()['self'].__dict__['_TrendLineManagement__last_accelerate_' + up_down_flag + '_trend_line'].trend_price_calculate(iloc)
                        temp_start_index = locals()['self'].__dict__['_TrendLineManagement__last_accelerate_' + up_down_flag + '_trend_line'].end_index
                        temp_start_price = locals()['self'].__dict__['_TrendLineManagement__last_accelerate_' + up_down_flag + '_trend_line'].end_price
                        temp_accelerate_trend_line = TrendLine(temp_start_index, board_point['max_min_iloc'][-1], temp_start_price, board_point['max_min_price'][-1], up_down_flag, list(min_data.index)[temp_start_index], list(min_data.index)[board_point['max_min_iloc'][-1]], is_inuse=True)
                        if self.__trend_line_support(locals()['self'].__dict__['_TrendLineManagement__last_accelerate_' + up_down_flag + '_trend_line'], min_data.iloc[iloc, :]):
                            locals()['self'].__dict__['_TrendLineManagement__last_accelerate_' + up_down_flag + '_trend_line'].support_times += 1
                        elif self.__cross_trend_line(locals()['self'].__dict__['_TrendLineManagement__last_accelerate_' + up_down_flag + '_trend_line'], min_data.iloc[iloc, :]):
                            locals()['self'].__dict__['_TrendLineManagement__crossed_accelerate_' + up_down_flag + '_trend_line'] = locals()['self'].__dict__['_TrendLineManagement__last_accelerate_' + up_down_flag + '_trend_line']
                            locals()['self'].__dict__['_TrendLineManagement__last_accelerate_' + up_down_flag + '_trend_line'] = temp_accelerate_trend_line
                        elif (temp_accelerate_trend_line.gradient > locals()['self'].__dict__['_TrendLineManagement__last_accelerate_' + up_down_flag + '_trend_line'].gradient > 0) \
                                or (temp_accelerate_trend_line.gradient < locals()['self'].__dict__['_TrendLineManagement__last_accelerate_' + up_down_flag + '_trend_line'].gradient < 0):
                            locals()['self'].__dict__['_TrendLineManagement__last_accelerate_' + up_down_flag + '_trend_line'] = temp_accelerate_trend_line

    def trend_line_adapt(self, up_down_flag, min_data, iloc):
        if locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'] is not None:
            locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].trend_price_calculate(iloc)
            adapt_times = locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].adapt_times
            if self.__adapt_trend_line(locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'], min_data.iloc[iloc, :]):
                locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'] = TrendLine(locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].start_index, iloc, locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].start_price, min_data.iloc[iloc, :][self.__high_low_return(up_down_flag)], up_down_flag, list(min_data.index)[locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].start_index], list(min_data.index)[iloc], is_inuse=True)
                locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].adapt_times = adapt_times
            elif self.__trend_line_support(locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'], min_data.iloc[iloc, :]):
                locals()['self'].__dict__['_TrendLineManagement__last_' + up_down_flag + '_trend_line'].support_times += 1

    def trend_line_cross(self, min_data, iloc):
        if self.__last_up_trend_line is not None:
            self.__last_up_trend_line.trend_price_calculate(iloc)
            if (min_data['open'][iloc] < self.__last_up_trend_line.trend_price) and (min_data['open'][iloc] >= min_data['close'][iloc]):
                self.__last_up_trend_line.cross_index = iloc
                self.__last_up_trend_line.cross_times += 1
        if self.__last_down_trend_line is not None:
            self.__last_down_trend_line.trend_price_calculate(iloc)
            if (min_data['open'][iloc] > self.__last_down_trend_line.trend_price) and (min_data['open'][iloc] <= min_data['close'][iloc]):
                self.__last_down_trend_line.cross_index = iloc
                self.__last_down_trend_line.cross_times += 1
        if self.__crossed_up_trend_line is not None:
            self.__crossed_up_trend_line.trend_price_calculate(iloc)
            if (min_data['open'][iloc] > self.__crossed_up_trend_line.trend_price) and (min_data['open'][iloc] <= min_data['close'][iloc]):
                self.__crossed_up_trend_line.cross_back_times += 1
        if self.__crossed_down_trend_line is not None:
            self.__crossed_down_trend_line.trend_price_calculate(iloc)
            if (min_data['open'][iloc] < self.__crossed_down_trend_line.trend_price) and (min_data['open'][iloc] >= min_data['close'][iloc]):
                self.__crossed_down_trend_line.cross_back_times += 1

    def get_last_down_trend_line(self):
        return self.__last_down_trend_line

    def get_last_up_trend_line(self):
        return self.__last_up_trend_line

    def get_crossed_up_trend_line(self):
        return self.__crossed_up_trend_line

    def get_crossed_down_trend_line(self):
        return self.__crossed_down_trend_line

    def get_crossed_up_trend_line1(self):
        return self.__crossed_up_trend_line1

    def get_crossed_down_trend_line1(self):
        return self.__crossed_down_trend_line1

    def get_last_accelearte_up_trend_line(self):
        return self.__last_accelerate_up_trend_line

    def get_last_accelearte_down_trend_line(self):
        return self.__last_accelerate_down_trend_line

    def trend_line_reset(self):
        self.__daily_accelerate_down_trend_line = {}
        self.__daily_accelerate_up_trend_line = {}
        self.__last_up_trend_line = None
        self.__crossed_up_trend_line = None
        self.__last_down_trend_line = None
        self.__crossed_down_trend_line = None
        self.__last_accelerate_up_trend_line = None
        self.__last_accelerate_down_trend_line = None









