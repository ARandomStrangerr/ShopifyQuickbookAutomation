import pandas as pd;
import SQLiteController as sql;

# read the excel file: [vendor name, liability, rental, commission]
df = pd.read_excel("file1.xlsx");

# list of needed accounts
incomeSaleAcc = sql.queryAccountByName("Income Sale");
liabilityAcc = sql.queryAccountByName("Liability Payback to Vendors");
incomeSubleaseAcc = sql.queryAccountByName("Income Vendor Sublease");
incomeCommission = sql.queryAccountByName("Income Commission Earned from Sales");

# list of journal entry to send
journalEntry = [];

# iterate throught each row to add to journalEntry
for row in df.iterrows():
    vendor = sql.queryVendor(row['vendor name']);
    # remove from income sale
    journalEntry.append( {
        "JournalEntryLineDetail": {
            "PostingType": "Debit", 
            "AccountRef": {
                'value': incomeSaleAcc[0],
                "name": incomeSaleAcc[1]
            }
        }, 
        "DetailType": "JournalEntryLineDetail", 
        "Amount": row['liability'], 
        "Id": "0", 
        "Description": "nov portion of rider insurance"
    });
    # input from liability
    journalEntry.append({
        "JournalEntryLineDetail": {
            "PostingType": "Credit", 
            "AccountRef": {
                'value': incomeSaleAcc[0],
                "name": incomeSaleAcc[1]
            }
        }, 
        "DetailType": "JournalEntryLineDetail", 
        "Amount": row['liability'],
        "Id": "0", 
        "Description": "nov portion of rider insurance"

    });
    # remove liability
    journalEntry.append({
        "JournalEntryLineDetail": {
            "PostingType": "Debit", 
            "AccountRef": {
                'value': incomeSaleAcc[0],
                "name": incomeSaleAcc[1]
            }
        }, 
        "DetailType": "JournalEntryLineDetail", 
        "Amount": row['liability'],
        "Id": "0", 
        "Description": "nov portion of rider insurance"
    });
    # income vendor sale
    if (row['rental'] != 0):
        journalEntry.append({
            "JournalEntryLineDetail": {
                "PostingType": "Debit", 
                "AccountRef": {
                    'value': incomeSaleAcc[0],
                    "name": incomeSaleAcc[1]
                }
            }, 
            "DetailType": "JournalEntryLineDetail", 
            "Amount": row['liability'],
            "Id": "0", 
            "Description": "nov portion of rider insurance"
        });

    # income vendor Sublease
    if (row['commission'] != 0):
        journalEntry.append({
            "JournalEntryLineDetail": {
                "PostingType": "Debit", 
                "AccountRef": {
                    'value': incomeSaleAcc[0],
                    "name": incomeSaleAcc[1]
                }
            }, 
            "DetailType": "JournalEntryLineDetail", 
            "Amount": row['liability'],
            "Id": "0", 
            "Description": "nov portion of rider insurance"
        });

