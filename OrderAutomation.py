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
                localItem = SQLiteController.queryItemByPosId(posId);
                if localItem is None: # if the item is not found, then create a new item
                    response = QBAutomation.__pushProduct(prod);
                    try:
                        qbId = response['Item']['Id'];
                        print(f'Create new QB with ID = {qbId}');
                        SQLiteController.insertItem(qbId, posId, prod['Name']);
                        print('Create item in local database');
                    except: # there is a chance that the db is deleted and the item is already on QB
                        # the pit fall here is when the item needed to be update but there is no local DB as reference, hence we upload a new item.
                        qbId = response['Fault']['Error'][0]['Detail'].split(":")[1].split("=")[1];
                        print(f'Already exsits in QB with ID = {qbId}, but not inside local DB');
                        # make an attemp to update the item incase change;
                        prod['Id'] = qbId;
                        prod['SyncToken'] = QBAutomation.__getProductSyncToken(qbId);
                        print('Updated product on QB');
                        SQLiteController.updateItem(qbId, prod['Name']);
                        print('Updated item on local BD');
                else: # if the item is found, then update the item in case something changes
                    # why do this?
                    # i am not going to waste the memory on my laptop for insiginificant down time in query.
                    # We pay QB top money and their server better works.
                    # If i store everything on my laptop, then I simply don't need QB
                    print("product is inside local DB");
                    prod['Id'] = localItem[0];
                    response = QBAutomation.__pushProduct(prod);
                    print("Updated product on QB");
                    SQLiteController.updateItem(localItem[0], prod['Name']);
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
            print(f'{qbId} - {vendor}\nalready exsits');
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
            print("Successfully create invoice {response['Invoice']['Id']}");
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

SQLiteController.initialSetup();
#updateChartOfAccount();
#updateVendor();
#updateProduct();
createOrUpdateInvoice();
#getLocation();
