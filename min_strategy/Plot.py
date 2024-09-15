import plotly.graph_objects as go
from datetime import datetime as dt

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

    def add_open(self, iloc, price, flag):
        if flag == "buy":
            self.__fig.add_trace(go.Scatter(
                x=[iloc],
                y=[price],
                mode='markers+text',
                name='Marked Points',
                marker=dict(color='blue', size=10),  # 设置标记的颜色和大小
                text=['Point 1', 'Point 2'],  # 添加文本标签
                textposition='top center'  # 文本位置
            ))
        elif flag == "sell":
            self.__fig.add_trace(go.Scatter(
                x=[iloc],
                y=[price],
                mode='markers+text',
                name='Marked Points',
                marker=dict(color='red', size=10),  # 设置标记的颜色和大小
                text=['Point 1', 'Point 2'],  # 添加文本标签
                textposition='top center'  # 文本位置
            ))
        return

    def add_close(self, iloc, price, flag):
        if flag == "buy":
            self.__fig.add_trace(go.Scatter(
                x=[iloc],
                y=[price],
                mode='markers+text',
                name='Marked Points',
                marker=dict(color='blue', size=10),  # 设置标记的颜色和大小
                text=['Point 1', 'Point 2'],  # 添加文本标签
                textposition='top center'  # 文本位置
            ))
        elif flag == "sell":
            self.__fig.add_trace(go.Scatter(
                x=[iloc],
                y=[price],
                mode='markers+text',
                name='Marked Points',
                marker=dict(color='red', size=10),  # 设置标记的颜色和大小
                text=['Point 1', 'Point 2'],  # 添加文本标签
                textposition='top center'  # 文本位置
            ))
        return

        return

    def show(self):
        self.__fig.show()
        return

