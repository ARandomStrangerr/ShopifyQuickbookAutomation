import PoSAutomation;
import QBAutomation;
import Trunk;
import pandas as pd;

def generatePayroll(excelPath):
    df = pd.read_excel(excelPath);
    uniqueDate = df['Start Date'].unique();
    splitDf = {date: df[df['Start Date'] == date] for date in uniqueDate};
    for date in uniqueDate:
        date = date;
        print(date);
#        data, cursor = PoSAutomation.getOrderData(startDate = f"{date}T00:00:00", endDate = f"{date}T:23:59:59");
#        total = 0;
#        while (True):
#            for d in data:
#                total += float(d['amount']);
#            if cursor is None:
#                break;
#            data, cursor = PoSAutomation.getOrderData(cursor=cursor);
#            print(f'{date} total = {total}');
    return;

Trunk.readData('./api_key.txt');
generatePayroll("./a.xlsx");
