import xlwt
import time


def excel_write(trade_record, trade_statistic, daily_statistic):
    work_book = xlwt.Workbook()
    sheet1 = work_book.add_sheet('trade_record')
    sheet2 = work_book.add_sheet('trade_statistic')
    sheet3 = work_book.add_sheet('daily_statistic')
    trade_record_keys = list(trade_record.keys())
    for i in range(0, len(trade_record_keys)):
        key = trade_record_keys[i]
        sheet1.write(0, i, key)
        for j in range(0, len(trade_record[key])):
            sheet1.write(j+1, i, trade_record[key][j])
    trade_statistic_key = list(trade_statistic.keys())
    for i in range(0, len(trade_statistic_key)):
        key = trade_statistic_key[i]
        sheet2.write(0, i, key)
        sheet2.write(1, i, trade_statistic[key])
    daily_statistic_keys = list(daily_statistic.keys())
    for i in range(0, len(daily_statistic_keys)):
        key = daily_statistic_keys[i]
        sheet3.write(0, i, key)
        for j in range(0, len(daily_statistic[key])):
            sheet3.write(j+1, i, daily_statistic[key][j] if i != 0 else str(daily_statistic[key][j]))
    commodity = trade_statistic['commodity']
    time_ = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    work_book.save('../back_test_result/' + commodity + '_trade_record_statistic_' + time_ + '.xls')
    return


def excel_write1(trade_record, trade_statistic):
    work_book = xlwt.Workbook()
    sheet1 = work_book.add_sheet('trade_record')
    sheet2 = work_book.add_sheet('trade_statistic')
    trade_record_keys = list(trade_record.keys())
    for i in range(0, len(trade_record_keys)):
        key = trade_record_keys[i]
        sheet1.write(0, i, key)
        for j in range(0, len(trade_record[key])):
            sheet1.write(j+1, i, trade_record[key][j])
    trade_statistic_key = list(trade_statistic.keys())
    for i in range(0, len(trade_statistic_key)):
        key = trade_statistic_key[i]
        sheet2.write(0, i, key)
        sheet2.write(1, i, trade_statistic[key])
    commodity = trade_statistic['commodity']
    time_ = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    work_book.save('../back_test_result/' + commodity + '_trade_record_statistic_' + time_ + '.xls')
    return

