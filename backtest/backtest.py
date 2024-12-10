import tushare as ts
import pandas as pd
import backtrader as bt
from flask import Flask, jsonify, request

# 设置tushare token
ts.set_token('b2a0f83a07f3d1a1590f33fc9031ac454747cf4f52d8eaf13e17f4d8')
pro = ts.pro_api()

# 获取平安银行的历史数据
df = pro.daily(ts_code='000001.SZ', start_date='20230101', end_date='20231231')

# 格式化数据，保存为CSV
df = df[['trade_date', 'open', 'high', 'low', 'close', 'vol', 'amount']]
df['trade_date'] = pd.to_datetime(df['trade_date'])
df.set_index('trade_date', inplace=True)
df.to_csv('pingan.csv')


def load_data(file_path):
    df = pd.read_csv('pingan.csv')

    # 确保 'trade_date' 是日期格式
    df['trade_date'] = pd.to_datetime(df['trade_date'])

    # 将日期列设置为索引
    df.set_index('trade_date', inplace=True)

    # 确保数据按日期升序排列
    df = df.sort_index()

    # 筛选需要的列：open, high, low, close, volume
    df = df[['open', 'high', 'low', 'close', 'vol']]
    df = df.rename(columns={'vol': 'volume'})  # backtrader要求列名为 'volume'

    return df


# 策略：均线交叉策略
class MovingAverageCrossStrategy(bt.Strategy):
    params = (
        ('short_period', 12),  # 12日均线
        ('long_period', 26),  # 26日均线
        ('risk', 0.2),  # 每次买入本金的20%
        ('slippage', 0.0001)  # 滑点
    )

    def __init__(self):
        # 初始化12日和26日均线
        self.short_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.long_period)

    def next(self):
        # 确保至少有26个数据点才开始计算均线
        if len(self) < self.params.long_period:
            return  # 数据不足时跳过计算

        # 12日均线穿越26日均线时买入
        if self.short_ma[0] > self.long_ma[0] and not self.position:
            size = self.broker.get_cash() * self.params.risk / self.data.close[0]  # 计算买入股数
            self.buy(size=size)

        # 如果价格跌破26日均线时卖出
        elif self.data.close[0] < self.long_ma[0] and self.position:
            self.sell(size=self.position.size)


# 设置回测环境
def run_backtest(file_path):
    # 加载数据
    data = load_data(file_path)

    # 创建 Cerebro 引擎
    cerebro = bt.Cerebro()

    # 将数据加载到 backtrader 数据源
    data_feed = bt.feeds.PandasData(dataname=data)

    # 添加数据和策略
    cerebro.adddata(data_feed)
    cerebro.addstrategy(MovingAverageCrossStrategy)

    # 设置初始资金和滑点
    cerebro.broker.set_cash(1000000)  # 初始资金100万
    cerebro.broker.set_slippage_perc(0.0001)  # 设置滑点

    # 设置佣金
    cerebro.broker.setcommission(commission=0.001)

    # 设置回测时间周期
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')

    # 运行回测
    results = cerebro.run()

    # 获取回测结果
    final_value = cerebro.broker.getvalue()
    initial_value = 1000000  # 初始资金
    
    # 计算收益率
    return_on_investment = ((final_value - initial_value) / initial_value)
    
    return final_value, return_on_investment


# 创建 Flask API
app = Flask(__name__)


# POST接口：设置回测周期和股票数据文件
@app.route('/backtest', methods=['POST'])
def backtest():
    data = request.json
    file_path = data.get('file_path', 'pingan.csv')

    # 运行回测并返回最终资产和收益率
    final_value, return_on_investment = run_backtest(file_path)

    return jsonify({
        "final_value": final_value,
        "return_on_investment": return_on_investment  # 返回收益率
    })


# GET接口：获取回测结果
@app.route('/backtest_result', methods=['GET'])
def get_backtest_result():
    final_value, return_on_investment = run_backtest('pingan.csv')

    return jsonify({
        "final_value": final_value,
        "return_on_investment": return_on_investment  # 返回收益率
    })


if __name__ == '__main__':
    # 启动 Flask 应用
    app.run(debug=True, host="0.0.0.0", port=5000)
