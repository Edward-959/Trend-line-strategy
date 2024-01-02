import numpy as np


class BoardPoint:
    def __init__(self):
        self.board_point = {}
        self.init_board_point()

    def init_board_point(self):
        self.board_point = {'cross_iloc': [], 'cross_direc': [], 'max_min_price': [], 'max_min_iloc': [], 'wave_len': [], 'wave_volatility': [], 'max_min_price_close': []}

    def set_board_point(self, direction, iloc, min_data):
        last_cross_point = self.board_point['cross_iloc'][-1] if len(self.board_point['cross_iloc']) > 0 else min_data['iloc'][0]
        last_max_min_price = self.board_point['max_min_price'][-1] if len(self.board_point['max_min_price']) > 0 else min_data['close'][0]
        search_interval = np.array(min_data['low'][self.iloc_to_daily_iloc(last_cross_point, min_data):self.iloc_to_daily_iloc(iloc, min_data)]) if direction == 1 else np.array(min_data['high'][self.iloc_to_daily_iloc(last_cross_point, min_data):self.iloc_to_daily_iloc(iloc, min_data)])
        if direction == 1:
            self.board_point['max_min_price'].append(min(search_interval))
            self.board_point['max_min_price_close'].append(min(min_data['close'][self.iloc_to_daily_iloc(last_cross_point, min_data):self.iloc_to_daily_iloc(iloc, min_data)]))
            self.board_point['max_min_iloc'].append(last_cross_point + np.where(search_interval == min(search_interval))[-1][-1])
        elif direction == -1:
            self.board_point['max_min_price'].append(max(search_interval))
            self.board_point['max_min_iloc'].append(last_cross_point + np.where(search_interval == max(search_interval))[-1][-1])
            self.board_point['max_min_price_close'].append(max(min_data['close'][self.iloc_to_daily_iloc(last_cross_point, min_data):self.iloc_to_daily_iloc(iloc, min_data)]))
        self.board_point['cross_iloc'].append(iloc)
        self.board_point['cross_direc'].append(direction)
        self.board_point['wave_len'].append(iloc - last_cross_point)
        self.board_point['wave_volatility'].append(self.board_point['max_min_price'][-1] - last_max_min_price)
        if (len(self.board_point['wave_len']) > 2) and self.board_point['wave_len'][-1] == 1:
            del self.board_point['max_min_price'][-2:]
            del self.board_point['max_min_iloc'][-2:]
            del self.board_point['cross_iloc'][-2:]
            del self.board_point['cross_direc'][-2:]
            del self.board_point['wave_len'][-2:]
            del self.board_point['wave_volatility'][-2:]

    @staticmethod
    def iloc_to_daily_iloc(iloc, min_data):
        return min_data['daily_iloc'][min_data['iloc'] == iloc][0]