import PoSAutomation as pos;
import QBAutomation as qb;
import Trunk;
import pandas as pd;

Trunk.readData('api_key.txt')

# read needed excel file
hourRateDf = pd.read_excel("WorkerRate.xlsx");
hourSheetDf = pd.read_excel('PayrollMarch2025-1.xlsx');

# format the data
hourSheetDf['Date'] = hourSheetDf['Date'].dt.date;
hourSheetDf['Description'] = hourSheetDf['Description'].fillna("new west");
hourSheetDf.loc[hourSheetDf['Description'] == 'CHURI Lougheed', 'Description'] = 'lougheed';

# define the output data to put into excel
dateList = hourSheetDf['Date'].unique(); # list out the date in the data frame

# get the total revenue by day
revenueByDate = {date: {"lougheed": 0.0, "new west": 0.0} for date in dateList}; # map to store revenue by day

# fill in the revenue
for date in dateList:
    invoices, cursor = pos.getOrderData(startDate=f'{date}T00:00:00', endDate=f'{date}T23:00:00', limit=100);
    while (True):
        for invoice in invoices:
            if "Lougheed" in invoice['location']:
                revenueByDate[date]["lougheed"] = revenueByDate[date]["lougheed"]  + float(invoice['amount']);
            elif "Newwest" in invoice['location']:
                revenueByDate[date]['new west'] = revenueByDate[date]['new west'] + float(invoice['amount']);
        if cursor is None:
            break;
        invoices, cursor = pos.getOrderData(cursor=cursor);

hourSheetDf.loc[hourSheetDf['Description'] == 'Project 1', "Billable Rate (USD)"] = 10;

for idx, row in hourSheetDf.iterrows():
    if (row['Billable Rate (USD)'] == 10):
        continue;
    workingLocation = row['Description'];
    numPeople = len(hourSheetDf[(hourSheetDf['Date'] == row['Date']) & (hourSheetDf['Billable Rate (USD)']!= 10)]);
    revenue = revenueByDate[row['Date']][workingLocation];
    hourSheetDf.loc[idx, 'Description'] = f'{workingLocation} revenue {revenue:.2f}';
    rateColName = "UpRate" if (revenue >= 1000 and numPeople == 1 or revenue >= 2000 and numPeople >= 2) else "Rate";
    hourSheetDf.loc[idx, 'Billable Rate (USD)'] = hourRateDf.loc[hourRateDf["Name"] == row['User'], rateColName].values[0];


hourSheetDf['Billable Amount (USD)'] = hourSheetDf['Duration (decimal)'] * hourSheetDf['Billable Rate (USD)'];
print(hourSheetDf);
try:
    writer = pd.ExcelWriter('output.xlsx', engine='xlsxwriter')
    hourSheetDf.to_excel(writer, sheet_name='Sheet1', index=False)
    writer.close();
except Exception as e:
    print(f"Error writing to Excel: {e}")
