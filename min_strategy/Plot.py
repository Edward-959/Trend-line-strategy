import plotly.graph_objects as go
import pandas as pd

class Plot:
    def __init__(self):
        self.__fig = None

    def init_fig(self, data):

        data['color'] = data['close'] >= data['open']
        data['color'] = data['color'].map({True: 'green', False: 'red'})  # 涨为绿色，跌为红色
        self.__fig = go.Figure(data=[go.Candlestick(x=data.index,
                                              open=data['open'],
                                              high=data['high'],
                                              low=data['low'],
                                              close=data['close'],
                                              increasing_line_color='green',
                                              decreasing_line_color='red')])

        self.__fig.update_layout(title='K线图示例',
                          xaxis_title='日期',
                          yaxis_title='价格',
                          xaxis_rangeslider_visible=False)

    def add_trace(self, iloc: [], price: [], flag):
        if flag == 1:
            self.__fig.add_trace(go.Scatter(x=iloc, y=price, mode='lines', name='Trend Line',
                                     line=dict(color='blue', width=2)))
        elif flag == -1:
            self.__fig.add_trace(go.Scatter(x=iloc, y=price, mode='lines', name='Trend Line',
                                     line=dict(color='red', width=2)))
        return

    def show(self):
        self.__fig.show()


# # 示例数据
# data = pd.DataFrame({
#     'date': pd.date_range(start='2023-01-01', periods=10),
#     'open': [100, 105, 102, 108, 110, 115, 113, 120, 125, 130],
#     'high': [105, 110, 108, 112, 115, 120, 118, 125, 130, 135],
#     'low': [98, 104, 101, 107, 109, 113, 111, 118, 123, 128],
#     'close': [104, 108, 107, 110, 112, 118, 116, 115, 128, 132]
# })
#
# # 计算涨跌情况
# data['color'] = data['close'] >= data['open']
# data['color'] = data['color'].map({True: 'green', False: 'red'})  # 涨为绿色，跌为红色
#
# # 创建K线图
# fig = go.Figure(data=[go.Candlestick(x=data['date'],
#                                       open=data['open'],
#                                       high=data['high'],
#                                       low=data['low'],
#                                       close=data['close'],
#                                       increasing_line_color='green',
#                                       decreasing_line_color='red')])
#
# # 确定两点
# x1, y1 = data['date'].iloc[1], 104  # 第一个点
# x2, y2 = data['date'].iloc[9], 130  # 第二个点
#
# # 添加趋势线，使用实线
# fig.add_trace(go.Scatter(x=[x1, x2], y=[y1, y2], mode='lines', name='Trend Line',
#                          line=dict(color='blue', width=2)))
#
# # 更新布局
# fig.update_layout(title='K线图示例',
#                   xaxis_title='日期',
#                   yaxis_title='价格',
#                   xaxis_rangeslider_visible=False)
#
# fig.show()