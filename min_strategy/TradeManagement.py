import datetime as dt
import numpy as np


class Order:
    def __init__(self, time, price, volume, direction, contract, index):
        self.time = time
        self.index = index
        self.price = price
        self.volume = volume
        self.direction = direction
        self.contract = contract


class TradeManangement:
    def __init__(self, commodity):
        self.__open_time = []
        self.__open_index = []
        self.__close_index = []
        self.__hold_time = []
        self.__close_num = []
        self.__open_price = []
        self.__volume = []
        self.__direction = []
        self.__close_time = []
        self.__close_price = []
        self.__contract = []
        self.__pnl = []
        self.__commodity = commodity
        self.__float_loss = 0
        self.__float_profit = 0
        self.__open_close_flag = 0
        self.__daily_trade_index = 0
        self.__daily_return = []
        self.__sum_daily_return = []
        self.__date = []
        self.__temp_float_loss = []
        self.__temp_float_profit = []

    def open_(self, order: Order):
        self.__open_time.append(order.time.strftime('%Y-%m-%d %H:%M:%S'))
        self.__open_index.append(int(str(order.index)))
        self.__open_price.append(order.price)
        self.__direction.append(order.direction)
        self.__volume.append(order.volume)
        self.__contract.append(order.contract)
        self.__open_close_flag = 1

    def close_(self, order: Order):
        self.__close_price.append(order.price)
        self.__close_index.append(order.index)
        self.__close_time.append(order.time.strftime('%Y-%m-%d %H:%M:%S'))
        self.__hold_time.append(int(str(order.index - self.__open_index[-1])))
        self.__pnl.append((self.__close_price[-1] - self.__open_price[-1]) if self.__direction[-1] == 'buy' else (self.__open_price[-1] - self.__close_price[-1]))
        self.__open_close_flag = 0
        self.__float_loss = 0
        self.__float_profit = 0

    @staticmethod
    def gradient_stop_loss(gradient, round_num):
        stop_loss = 2 + round(1 * abs(gradient), round_num)
        return stop_loss

    @staticmethod
    def daily_high_low_stop_loss(daily_high, daily_low, jump, round_num):
        stop_loss = round((daily_high - daily_low) * 0.025, round_num) / jump + 8
        moving_stop_loss = round((daily_high - daily_low) * 0.05, round_num) / jump + 10
        return stop_loss, moving_stop_loss

    def float_loss(self, high_low):
        open_price = self.__open_price[-1]
        self.__float_loss = high_low - open_price if self.__direction[-1] == 'buy' else (open_price - high_low)
        self.__temp_float_loss.append(self.__float_loss)

    def float_profit(self, high_low):
        open_price = self.__open_price[-1]
        self.__float_profit = high_low - open_price if self.__direction[-1] == 'buy' else (open_price - high_low)
        self.__temp_float_profit.append(self.__float_profit)

    def calc_float_profit_loss(self, min_data_slice):
        self.float_loss(min_data_slice['low']) if self.__direction[-1] == 'buy' else self.float_loss(min_data_slice['high'])
        self.float_profit(min_data_slice['high']) if self.__direction[-1] == 'buy' else self.float_profit(min_data_slice['low'])

    def trade_management(self, min_data_slice, open_bool, close_num, direction, new_day_bool, datetime, close_price,
                         open_price, plot):
        if open_bool == 1 and self.__open_close_flag == 0:
            order = Order(datetime, open_price, 1, direction, min_data_slice['contract'], min_data_slice['iloc'])
            plot.add_open(datetime, open_price, direction)
            self.open_(order)
        if close_num != 0 and self.__open_close_flag == 1 and direction != self.__direction[-1]:
            order = Order(datetime, close_price, 1, direction, min_data_slice['contract'], min_data_slice['iloc'])
            plot.add_close(datetime, open_price, self.__direction[-1])
            self.__close_num.append(int(str(close_num)))
            self.close_(order)
            self.reset_float()
        if new_day_bool == 1:
            self.__date.append(dt.datetime(datetime.year, datetime.month, datetime.day))
            if len(self.__pnl) != self.__daily_trade_index:
                self.__daily_return.append(float(str(sum(self.__pnl[self.__daily_trade_index:]))))
                self.__sum_daily_return.append(float(str(sum(self.__daily_return))))
                self.__daily_trade_index = len(self.__pnl)
            else:
                self.__daily_return.append(0)
                self.__sum_daily_return.append(float(str(sum(self.__daily_return))))

    def reset_float(self):
        self.__float_loss = 0
        self.__float_profit = 0
        self.__temp_float_loss = []
        self.__temp_float_profit = []

    def get_float_loss(self):
        return self.__temp_float_loss

    def get_float_profit(self):
        return self.__temp_float_profit

    def get_open_close_flag(self):
        return self.__open_close_flag

    def get_last_direction(self):
        return self.__direction[-1]

    def get_start_price(self):
        return self.__open_price[-1]

    def get_last_start_index(self):
        return self.__open_index[-1]

    def trade_statistic(self):
        times = len(self.__open_price)
        average_return = sum(self.__pnl) / times
        win_times = alen(np.array(self.__pnl)[np.array(self.__pnl) > 0])
        lose_times = alen(np.array(self.__pnl)[np.array(self.__pnl) <= 0])
        winning_rate = win_times / times
        win_to_loss = abs(np.average(np.array(self.__pnl)[np.array(self.__pnl) >= 0]) / np.average(np.array(self.__pnl)[np.array(self.__pnl) < 0]))
        trade_statistic_ = {'commodity': self.__commodity, 'times': times, 'average_return': average_return, 'win_times': win_times, 'lose_times': lose_times, 'win_rate': winning_rate, 'win_to_loss': win_to_loss}
        return trade_statistic_

    def data_collect(self):
        trade_record = {'contract': self.__contract, 'open_time': self.__open_time, 'open_index': self.__open_index, 'open_price': self.__open_price, 'volume': self.__volume, 'direction': self.__direction,
                        'close_time': self.__close_time, 'close_price': self.__close_price, 'close_num': self.__close_num, 'hold_time': self.__hold_time, 'pnl': self.__pnl}
        daily_record = {'date': self.__date,  'daily_return': self.__daily_return, 'sum_daily_return': self.__sum_daily_return}
        trade_statistic_ = self.trade_statistic()
        return trade_record, daily_record, trade_statistic_



def alen(x):
    return 1 if np.isscalar(x) else len(x)