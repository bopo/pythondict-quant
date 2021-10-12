# Python实用宝典
# 2020/04/25
# 转载请注明出处
import datetime
import glob
import pickle
from pathlib import Path

import backtrader as bt
from backtrader.indicators import EMA
from loguru import logger


class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        """ Logging function fot this strategy"""
        dt = dt or self.datas[0].datetime.date(0)
        logger.info('%s, %s' % (dt.isoformat(), txt))

    @staticmethod
    def percent(today, yesterday):
        return float(today - yesterday) / today

    def __init__(self):
        self.bar_executed_close = 0
        self.bar_executed = 0

        self.data_close = self.datas[0].close
        self.volume = self.datas[0].volume

        self.order = None
        self.buy_price = None
        self.buy_comm = None

        me1 = EMA(self.data, period=12)
        me2 = EMA(self.data, period=26)

        self.macd = me1 - me2
        self.signal = EMA(self.macd, period=9)

        bt.indicators.MACDHisto()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm
                self.bar_executed_close = self.data_close[0]
            else:
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' % (order.executed.price, order.executed.value, order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm))

    # Python 实用宝典
    def next(self):
        self.log('Close, %.2f' % self.data_close[0])

        if self.order:
            return

        if not self.position:
            condition1 = self.macd[-1] - self.signal[-1]
            condition2 = self.macd[0] - self.signal[0]

            if condition1 < 0 and condition2 > 0:
                self.log('BUY CREATE, %.2f' % self.data_close[0])
                self.order = self.buy()

        else:
            condition = (self.data_close[0] - self.bar_executed_close) / self.data_close[0]

            if condition > 0.1 or condition < -0.1:
                self.log('SELL CREATE, %.2f' % self.data_close[0])
                self.order = self.sell()


def run_cerebro(stock_file):
    """
    运行策略
    :param stock_file: 股票数据文件位置
    """

    cerebro = bt.Cerebro()
    cerebro.addstrategy(TestStrategy)

    # 加载数据到模型中
    data = bt.feeds.GenericCSVData(
        dataname=stock_file,
        fromdate=datetime.datetime(2010, 1, 1),
        todate=datetime.datetime(2020, 4, 25),
        dtformat='%Y%m%d',
        datetime=2,
        open=3,
        high=4,
        low=5,
        close=6,
        volume=10,
        reverse=True
    )

    cerebro.adddata(data)

    # 本金10000，每次交易100股
    cerebro.broker.setcash(10000)
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)

    # 万五佣金
    cerebro.broker.setcommission(commission=0.0005)

    # 运行策略
    cerebro.run()

    # 剩余本金
    money_left = cerebro.broker.getvalue()

    # 获取股票名字
    stock_name = Path(stock_file).name.split('.csv')[0]

    # 将最终回报率以百分比的形式返回
    result = {stock_name: float(money_left - 10000) / 10000}

    logger.info(f'stock_file => {stock_file}')
    logger.info(f'stock_name => {stock_name}')
    logger.info(f'result => {result}')

    return result


results = {}

for stock in glob.glob('stocks/*.csv'):
    try:
        results.update(run_cerebro(stock))
    except Exception as e:
        logger.exception(e)

with open('./batch_macd_result.txt', 'wb') as f:
    pickle.dump(results, f)
