#coding: utf-8
from quantTradeSystem.dataSort.QAFetch.QAQuery_Advance import QA_fetch_stock_day_adv, QA_fetch_stock_list_adv
from multiprocessing import Manager
from multiprocessing import Pool as ThreadPool
from quantTradeSystem.dataSort.QAUtil import QA_util_log_info

import quantTradeSystem.selectStock.select.SelectResultDao as SelectResultDao
import talib as ta

# class SelectStockService():
#
#     def select_stock(self):
#         pass
#
#     def get_select_result(self):
#         pass

# class SelectStockServiceImpl():
#     def __init__(self):
#         self.select_result = []
select_result = []

def get_stock_data(code):
    stock_day_data = QA_fetch_stock_day_adv(code).to_qfq()
    stock_day_data = stock_day_data.to_pd()
    if stock_day_data is None:
        return []
    return stock_day_data

def save_select_result(code, select_result, para):
    select_date = SelectResultDao.get_last_index_date()
    contains_code_result = check_result_contains(code, select_result)
    if contains_code_result is None:
        single_result_dict = {"code": code, "date": select_date}
        single_result_dict["parameter"] = [para]
        select_result.append(single_result_dict)
    else:
        single_result_para = para
        contains_code_result["parameter"].append(single_result_para)

    # print(single_result_dict)
    QA_util_log_info(select_result)
    # SelectResultDao.save_select_result(select_result, code)

def MACD_select(code, select_result):
    """
        MACD Line: (12-day EMA - 26-day EMA)

        Signal Line: 9-day EMA of MACD Line

        MACD Histogram: MACD Line - Signal Line
    :param stock_day_data:
    :return:
    """
    stock_day_data = get_stock_data(code)
    if len(stock_day_data) < 26:
        return
    stock_day_data["macd"], stock_day_data["macdsignal"], \
    stock_day_data["macdhist"] = ta.MACD(stock_day_data["close"], fastperiod=12, slowperiod=26, signalperiod=9)
    stock_day_data["close_ma5"] = ta.MA(stock_day_data["close"], timeperiod=5)
    last_macd_item = stock_day_data["macdhist"][len(stock_day_data["macdhist"]) - 10:]
    macd_condition = all(macd1 < macd2 for macd1, macd2 in zip(last_macd_item, last_macd_item[1:]))
    if macd_condition:
        last_ma_item = stock_day_data["close_ma5"][len(stock_day_data["close_ma5"]) - 5:]
        ma_condition = all(ma1 < ma2 for ma1, ma2 in zip(last_ma_item, last_ma_item[1:]))
        if ma_condition:
            prevclose = stock_day_data["close"][-1]
            # contains_code_result = check_result_contains(code, select_result)
            single_result_para = {"S1": {"stop_price": round(prevclose * 0.95, 2), "profit_price":
                round(prevclose * 1.15, 2), "buy_price": round(prevclose * 1.02, 2)}}
            save_select_result(code, select_result, single_result_para)

def KDJ_select(code, select_result):
    select_date = SelectResultDao.get_last_index_date()
    stock_day_data = get_stock_data(code)
    if len(stock_day_data) < 10 :
        return
    stock_day_data["slowk"], stock_day_data["slowd"] = ta.STOCH(stock_day_data["high"].values,
                                                                stock_day_data["low"].values,
                                                                stock_day_data["close"].values,
                                                                fastk_period=9,
                                                                slowk_period=3,
                                                                slowk_matype=0,
                                                                slowd_period=3,
                                                                slowd_matype=0)
    if len(stock_day_data["slowk"]) < 2:
        return
    if stock_day_data["slowk"][-1] > stock_day_data["slowd"][-1] and stock_day_data["slowk"][-2] < stock_day_data["slowd"][-2] and stock_day_data["slowk"][-1] <= 15:
        prevclose = stock_day_data["close"][-1]
        single_result_para = {"S2": {"stop_price": round(prevclose * 0.95, 2), "profit_price":
            round(prevclose * 1.15, 2), "buy_price": round(prevclose * 1, 2)}}
        save_select_result(code, select_result, single_result_para)

def check_result_contains(code, select_result):
    """
    检查选股结果是否包含code
    :param code:
    :return: Node 或 该code对应的dict
    """
    for dict_item in select_result:
        if dict_item["code"] == code:
            return dict_item
    return None

# def select_stock():

if __name__ == '__main__':

    manager = Manager()
    select_result = manager.list()
    code_list = QA_fetch_stock_list_adv()
    code_list = code_list["code"]
    threadPool = ThreadPool(10)
    # MACD_select("000825", select_result)
    # MACD_select("000063", select_result)
    KDJ_select("603665", select_result)
    # for item in code_list:
    #     threadPool.apply_async(MACD_select, [item,select_result])
    #     threadPool.apply_async(KDJ_select, [item, select_result])
    threadPool.close()
    threadPool.join()
    if len(select_result) > 0:
        SelectResultDao.save_select_result(select_result)
    print(select_result)
    QA_util_log_info(select_result)

# select_stock()