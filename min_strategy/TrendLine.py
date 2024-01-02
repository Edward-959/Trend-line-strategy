"""
趋势线策略。扇形原理
样例：
oi009, 6-10, 9:00 ,尤其有意思，首先是9;00-9:17分出现了三次趋势线的改变，形成了小扇形原理。随即价格开始调整。
                    然后，至10点55分，形成了第二个扇形原理，由第一个扇形原理的最后一根趋势线和后两根趋势线组成。
                    个股在第三根趋势线走出了最大的一浪。另外，在第一个小扇形原理的起点，是9:02分的最低点，
                    与开盘价平齐。趋势线的起点动态变化，从最直接的上涨起点处发起。
       6-10, 21:00， 注意，21:00处第一根趋势线是21:00分k线的最低点和21:01分k线的最低点。随即，21:02分开盘价低于上述
                     趋势线，于是21:02分价格首先冲高，在第一根趋势线处遇阻，随即回落。21:02分k线的最低点与开盘最低点
                     形成了第二根趋势线。而9:03分的k线上冲的最高点，即是与第二根趋势线斜率相同的，由9:02分k线最高点发
                     出的管道线在9:03分处的延长线位置。
             21：19-21：30分，由21:19分的最高点延伸出了一个小扇形，在21:31分被突破后拉升。

       6-12, 09:00
开始写事件驱动型框架，以扇形原理作为第一个策略。
简单使用界点作为趋势线的连接点，太粗糙。需要写循环，对趋势线的过程进行微调。
同样，也对波段的甄别也有问题，一些无效界点可以在循环中加以甄别和舍弃。
而且现在回测中已经涉及到多个循环，再使用之前的框架失去意义。
而且限于dataframe本身的问题，很多复杂策略很难实现。

趋势线：如果一根k线部分穿过趋势线，则修正趋势线
如果一根k线的open、close均在趋势线外则算突破了趋势线。
在大级别上，从日内的低点、高点发出的趋势线比较有意义，适合做进场信号
小级别的趋势线，也就是在趋势内部的趋势线，适合做出场信号。

规则1：只做close和ma5的界点做出的趋势线。
规则2：用本日最低点low划向上趋势线，用最高点high划向下趋势线。
规则3：对于趋势线，有两类方法：新划和调整，在本周期内上一个趋势线被明确突破，新划，否则，按新的open、close调整
       (如果close在ma5下方，不必调整前一条趋势线，等待下一个界点出现时的新趋势线，只在上升趋势中调整上升趋势线。反之亦然）。
规则4：只有close超出收盘价2个价位即称为趋势线被突破。
规则5：如果本日最低最高点出发的趋势线已经无法将最低最高点后发生的所有价格包含其中，称为趋势线加速，将最高点后的次高点与后续相邻的高点划趋势线，以此类推。
规则6：过于陡峭、离当前价位过远的趋势线（50单位以上的）则删掉。
规则7：同一根趋势线，被向上突破一次，又被向下突破一次（但是相邻k线或同一波趋势内，被突破，然后又突破回去，算是被突破了一次，
      要在被突破后的又一波趋势中再次被突破），则宣告失效。
规则8：如果上涨趋势中趋势线被突破，调整，不建立新的趋势线。如果下跌趋势中上涨趋势线被突破，则计入失效。
规则9：当后建立的趋势线也被突破，之前建立的自动失效。
规则10：同一时间同一趋势最多只有2条从最高点、最低点发出的趋势线：当前趋势线、被突破的趋势线，但可以有加速趋势线。

总结，三类趋势线形态：新建、调整、加速（开仓后再刻画）
观察：趋势线与ma20、ma50相结合，似乎可以做出不错的进场信号。
      加速趋势线被突破，在刚开盘时可以多拿一会，除非主趋势线被突破，希望有更大收益。如果距离收盘很近，则应在加速趋势线被突破后平仓。

20210802:
明天把逻辑重新盘一下。包括怎么写加速趋势线的问题、在TrendLineManagemnt中写创建趋势线方法的问题。目前来看不需要保留那么多历史趋势线，
主趋势线可以不用列入字典保管，但可以在字典中管理加速趋势线。每到一个新的趋势中只涉及到两个问题（下跌趋势中为例），下跌趋势线需不需要调整
以及上涨趋势线有没有被突破。
"""

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









