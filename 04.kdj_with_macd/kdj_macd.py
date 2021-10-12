# Python实用宝典
# 2020/05/05
# 转载请注明出处
import datetime
import os.path
import sys
import backtrader as bt
from backtrader.indicators import EMA
from loguru import logger


class TestStrategy(bt.Strategy):
    def log(self, txt, dt=None):
        """ Logging function fot this strategy"""
        dt = dt or self.datas[0].datetime.date(0)
        logger.info("%s, %s" % (dt.isoformat(), txt))

    @staticmethod
    def percent(today, yesterday):
        return float(today - yesterday) / today

    def __init__(self):
        self.data_close = self.datas[0].close
        self.volume = self.datas[0].volume

        self.order = None
        self.buy_price = None
        self.buy_comm = None

        self.bar_executed_close = None
        self.bar_executed = None

        # 9个交易日内最高价
        self.high_nine = bt.indicators.Highest()

        # 9个交易日内最低价
        self.low_nine = bt.indicators.Lowest()

        # 计算rsv值
        self.rsv = 100 * bt.DivByZero(self.data_close - self.low_nine, self.high_nine - self.low_nine, zero=None)

        # 计算rsv的3周期加权平均值，即K值
        self.K = bt.indicators.EMA(self.rsv, period=3, plot=False)

        # D值=K值的3周期加权平均值
        self.D = bt.indicators.EMA(self.K, period=3, plot=False)

        # J=3*K-2*D
        self.J = 3 * self.K - 2 * self.D

        # MACD策略参数
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
                self.log("BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f" % (order.executed.price, order.executed.value, order.executed.comm))

                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm

                self.bar_executed_close = self.data_close[0]
            else:
                self.log("SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f" % (order.executed.price, order.executed.value, order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log("OPERATION PROFIT, GROSS %.2f, NET %.2f" % (trade.pnl, trade.pnlcomm))

    # Python 实用宝典
    def next(self):
        self.log("Close, %.2f" % self.data_close[0])

        if self.order:
            return

        if not self.position:
            # 买入基于MACD策略
            condition1 = self.macd[-1] - self.signal[-1]
            condition2 = self.macd[0] - self.signal[0]

            if condition1 < 0 and condition2 > 0:
                self.log('BUY CREATE, %.2f' % self.data_close[0])
                self.order = self.buy()

        else:
            # 卖出基于KDJ策略
            condition1 = self.J[-1] - self.D[-1]
            condition2 = self.J[0] - self.D[0]

            if condition1 > 0 or condition2 < 0:
                self.log("SELL CREATE, %.2f" % self.data_close[0])
                self.order = self.sell()


if __name__ == "__main__":
    cerebro = bt.Cerebro()

    cerebro.addstrategy(TestStrategy)

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, "002859.csv")

    # 加载数据到模型中
    data = bt.feeds.GenericCSVData(
        dataname=datapath,
        fromdate=datetime.datetime(2010, 1, 1),
        todate=datetime.datetime(2020, 4, 21),
        dtformat="%Y%m%d",
        datetime=2,
        open=3,
        high=4,
        low=5,
        close=6,
        volume=10,
        reverse=True,
    )

    cerebro.adddata(data)

    cerebro.broker.setcash(10000)

    cerebro.addsizer(bt.sizers.FixedSize, stake=100)

    cerebro.broker.setcommission(commission=0.005)

    print("Starting Portfolio Value: %.2f" % cerebro.broker.getvalue())

    cerebro.run()

    print("Final Portfolio Value: %.2f" % cerebro.broker.getvalue())

    cerebro.plot()
