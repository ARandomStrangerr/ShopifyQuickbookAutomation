from sqlite3 import IntegrityError
from requests import request
import Trunk;
import PoSAutomation;
import QBAutomation;
import SQLiteController;

Trunk.readData('api_key.txt');

def updateInvoices():
    """
    Get Order from PoS and create a matching invoice on QB.
    This will get x amount of invoice, PoSAutomation.getOrderData will clean up and extract cleaner fields
    Give the list of extracted invocie to QBAutomation.pushInvoice to push to QB.
        This function will query product ID, location ID of the item form SQLite
        Therefore updateProduct function must be called first before this function is called
    After finish the process, the last update date - time will be recorded.
    (need update for when the program is interupted, continue where is left off).
    """
    try:
        orders, cursor = PoSAutomation.getOrderData(startDate=Trunk.data['lastUpdatedInvoice']);
    except:
        orders, cursor = PoSAutomation.getOrderData();
    while (True): # thy stupid language does not support do-while loop
        QBAutomation.pushInvoice(orders);
        if (cursor is None):
            break;
        else:
            orders, cursor = PoSAutomation.getOrderData(cursor=cursor);
    lastUpdatedInvoice: str = str(orders[-1]['date']);
    Trunk.data['lastUpdatedInvoice'] = lastUpdatedInvoice;
    Trunk.writeData("api_key.txt");
    print(f"Finished updating invoice to {lastUpdatedInvoice}");
    return;

def updateProduct():
    """
    There are 2 cases:
        If last update date found (mean that we should have items till the last update):
            query data from the last update till the current moment
            update the data with the SQLite
            update the data with QB
            query all data of SQLite to check if anything is deleted
            if anything is deleted, update with QB
        If no last update date found (mean that this is a fresh system, no item is downloaded):
            retreat x items from PoS
            create those x items with QB
            insert those x items into SQLite
        record the last update date - time
    """
    try: # case when the lastUpdateProductTime is in the system
        productList, cursor = PoSAutomation.getProductData(startDate=Trunk.data['lastUpdatedProductTime']);
    except: # case when the lastUpdateProductTime is not in the system
        productList, cursor = PoSAutomation.getProductData(startDate='0001-01-01');
    lastUpdatedItemTime = "";
    while (True):
        for product in productList: # list of product from PoS
            # prep each product to comply with QB standard
            readyToPushProducts = QBAutomation.__prepProductToPush(product);
            for idx, prod in enumerate(readyToPushProducts): # list of varaints of each product
                # upload an item to QB
                print(prod['Name']);
                posId = product['variants'][idx]['id'];
                localItem = SQLiteController.queryItem(posId=posId);
                if localItem is None: # if the item is not found, then create a new item
                    response = QBAutomation.__pushProduct(prod);
                    vendor = SQLiteController.queryVendor(product['vendor']);
                    try:
                        qbId = response['Item']['Id'];
                        print(f'Create new QB with ID = {qbId}');
                    except Exception as e: # there is a chance that the db is deleted and the item is already on QB
                        # the pit fall here is when the item needed to be update but there is no local DB as reference, hence we upload a new item.
                        qbId = response['Fault']['Error'][0]['Detail'].split(":")[1].split("=")[1];
                        print(f'Already exsits in QB with ID = {qbId}, but not inside local DB');
                        # make an attemp to update the item incase change;
                        prod['Id'] = qbId;
                        prod['SyncToken'] = QBAutomation.__getProductSyncToken(qbId);
                        print('Updated product on QB');
                    try:
                        print(prod)
                        SQLiteController.insertItem(qbId, posId, prod['Name'], vendor[0]);
                        print('Updated item on local BD');
                    except IntegrityError:
                        print(f'product {prod["Name"]} pos Id {posId} already exists {localItem} possible duplicates');
                else: # if the item is found, then update the item in case something changes
                    # why do this?
                    # i am not going to waste the memory on my laptop for insiginificant down time in query.
                    # We pay QB top money and their server better works.
                    # If i store everything on my laptop, then I simply don't need QB
                    print("product is inside local DB");
                    prod['Id'] = localItem[0];
                    response = QBAutomation.__pushProduct(prod);
                    print("Updated product on QB");
                    try:
                        SQLiteController.updateItem(localItem[0], prod['Name']);
                    except Exception as e:
                        print(e);
                    print('Updated item on local BD')
                lastUpdatedItemTime = response['time'];
                print();
        if (cursor is None): # there is no next page to fetch
            break;
        else: # fetch another batch of items
            productList, cursor = PoSAutomation.getProductData(cursor=cursor);
    Trunk.data['lastUpdatedProductTime'] = lastUpdatedItemTime;
    Trunk.writeData("api_key.txt");
    print(f"Finish updating product till {Trunk.data['lastUpdatedProductTime']}");
    return;

def updateVendor():
    try:
        vendor, cursor = PoSAutomation.getVendorName(Trunk.data['lastUpdatedVendorTime']);
    except:
        vendor, cursor = PoSAutomation.getVendorName("0001-01-01");
    vendorMap = {}
    while (True):
        for v in vendor:
            vendorMap[v] = 0;
        if cursor is None:
            break;
        vendor, cursor = PoSAutomation.getVendorName(cursor=cursor);
    vendorList = vendorMap.keys();
    time = "";
    for vendor in vendorList:
        response = QBAutomation.__pushVendor(vendor).json();
        try: # extract the ID of an item if the item is already exsits
            qbId = response['Fault']['Error'][0]['Detail'].split(":")[1].split("=")[1];
            print(f'{qbId} - {vendor}\nalready exsits on QB');
        except Exception:
            qbId = response['Class']['Id'];
            print(f'{qbId} - {vendor}\ncreated');
        try:
            SQLiteController.insertVendor(qbId, vendor);
        except:
            print(f'already inside the local database');
        print();
        time = response['time'];
    Trunk.data['lastUpdatedVendorTime'] = time;
    Trunk.writeData("api_key.txt");
    print(f"Finish updateing vendor till {Trunk.data['lastUpdatedVendorTime']}");
    return;

# update the Chart of account from quickbook with local database
def updateChartOfAccount():
    for account in QBAutomation.__getChartOfAccount():
        print(f'{account["Id"]} - {account["Name"]}')
        try:
            SQLiteController.insertAccount(account['Id'], account['Name']);
            print('inserted into local DB');
        except:
            SQLiteController.updateChartOfAccount(account['Id'], account['Name']);
            print('updated');
        print();
    return;

def createOrUpdateInvoice():
    try:
        orders, cursor = PoSAutomation.getOrderData(startDate=Trunk.data['lastUpdatedInvoice']);
    except Exception:
        orders, cursor = PoSAutomation.getOrderData(startDate="2025-03-01");
    while (True):
        for order in orders:
            invoice = QBAutomation.__prepInvoiceToPush(order);
            response = QBAutomation.__pushInvoice(invoice);
            try:
                print(f"Successfully create invoice {response['Invoice']['DocNumber']}");
            except Exception:
                print(f'Invoice {response["Fault"]["Error"][0]["Detail"].split("=")[-3].split(" ")[0]} is already created');
        if cursor is not None:
            orders, cursor = PoSAutomation.getOrderData(cursor=cursor);
        else:
            break;
    try:
        lastUpdatedInvoice: str = str(orders[-1]['date']);
        Trunk.data['lastUpdatedInvoice'] = lastUpdatedInvoice;
        Trunk.writeData("api_key.txt");
    except:
        print("Up to date invoice");
    return;

def getLocation():
    print(QBAutomation.__getLocations());

def cleanupCustomSale():
    maxResult = 50; # the max number of invoice to fetch
    startPos = 0; # current starting position when fetch
    date = "2025-01-31";
    account = SQLiteController.queryAccountByName("Income Sale");
    invoices = QBAutomation.__getInvoice(maxResult, startPos, date).json()['QueryResponse']['Invoice']; # the first 5 invoices

    while (True):
        for invoice in invoices:
            flag = False;
            for line in invoice["Line"]:
                if line['DetailType'] == 'SalesItemLineDetail' and line['SalesItemLineDetail']['ItemAccountRef']['value'] == '20':
                    print(f'invoice {invoice["DocNumber"]} at line {line["LineNum"]}');
                    item = SQLiteController.queryItem(name=line['Description']);
                    if item is None:
                        item = QBAutomation.__getItem(line['Description']).json();
                        print(item);
                        item = item['QueryResponse']['Item'][0];
                        line['SalesItemLineDetail']['ItemRef']['value'] = item['Id'];
                        line['SalesItemLineDetail']['ItemRef']['name'] = line['Description'];
                        line['SalesItemLineDetail']['ItemAccountRef']['name'] = 'Income Sale';
                        line['SalesItemLineDetail']['ItemAccountRef']['value'] = account[0];
                    else:
                        line['SalesItemLineDetail']['ItemRef']['value'] = item[0];
                        line['SalesItemLineDetail']['ItemRef']['name'] = line['Description'];
                        line['SalesItemLineDetail']['ItemAccountRef']['name'] = 'Income Sale';
                        line['SalesItemLineDetail']['ItemAccountRef']['value'] = account[0];
                        line['SalesItemLineDetail']['ClassRef']['value'] = item[2];
                        del line['SalesItemLineDetail']['ClassRef']['name'];
                    flag = True;
            if flag:
                response = QBAutomation.__pushInvoice(invoice);
                print(f'Updated invoice');
        if len(invoices) < maxResult:
            break;
        startPos += maxResult;
        try:
            invoices = QBAutomation.__getInvoice(maxResult, startPos, date).json()['QueryResponse']['Invoice'];
        except:
            break;
    return;

SQLiteController.initialSetup();
#updateChartOfAccount();
updateVendor();
updateProduct();
createOrUpdateInvoice();
#getLocation();
#cleanupCustomSale();
