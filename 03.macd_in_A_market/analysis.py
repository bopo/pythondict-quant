import pickle

from loguru import logger

# 加载保存的结果
with open('./batch_macd_result.txt', 'rb') as f:
    data = pickle.load(f)

# 计算
# pos = []
# neg = []

# ten_pos = []
# ten_neg = []
#
# for result in data:
#     res = data[result]
#
#     if res > 0:
#         pos.append(res)
#     else:
#         neg.append(res)
#
#     if res > 0.1:
#         ten_pos.append(result)
#     elif res < -0.1:
#         ten_neg.append(result)

pos = [data[result] for result in data if data[result] > 0]
neg = [data[result] for result in data if data[result] <= 0]

ten_pos = [data[result] for result in data if data[result] > 0.1]
ten_neg = [data[result] for result in data if data[result] < -0.1]

max_stock = max(data, key=data.get)

logger.info(f'最高收益的股票： {max_stock}, 达到 {data[max_stock]}')
logger.info(f'正收益数量: {len(pos)}, 负收益数量: {len(neg)}')
logger.info(f'+10% 数量: {len(ten_pos)}, -10% 数量: {len(ten_neg)}')
logger.info(f'收益 10% 以上的股票: {ten_pos}')
