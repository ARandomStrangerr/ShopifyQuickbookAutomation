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
    while (cursor): # thy stupid language does not support do-while loop
        QBAutomation.pushInvoice(orders);
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
    try: # case weh nthe lastUpdateProductTime is in the system
        productList, cursor = PoSAutomation.getProductData(startDate=Trunk.data['lastUpdatedProductTime']);
    except: # case when the lastUpdateProductTime is not in the system
        productList, cursor = PoSAutomation.getProductData(startDate='0001-01-01');
    lastUpdatedItemTime = "";
    while (True):
        for product in productList: # list of product from PoS
            # prep each product to comply with QB standard
            readyToPushProducts = QBAutomation.__prepProductToPush(product);
            for prod in readyToPushProducts: # list of varaints of each product
                # upload an item to QB
                response = QBAutomation.__pushProduct(prod);
                try: # extract the ID of an item if the item is already exsits
                    qbId = response['Fault']['Error'][0]['Detail'].split(":")[1].split("=")[1];
                    name = prod['Name'];
                except Exception:
                    qbId = response['Item']['Id'];
                    name = response['Item']['Name'];
                print(f"product name: {name}");
                try:
                    SQLiteController.insertItem(qbId, name);
                except Exception as e:
                    print(f"response: {response}");
                    print(f"SQL record: {SQLiteController.queryItem(name)}");
                    print(f"Error msg: {e}");
                lastUpdatedItemTime = response['time'];
                # store the item in SQLite
                print(response); print();
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
        print(vendor);
        print(response);
        try: # extract the ID of an item if the item is already exsits
            qbId = response['Fault']['Error'][0]['Detail'].split(":")[1].split("=")[1];
        except Exception:
            qbId = response['Class']['Id'];
        try:
            SQLiteController.insertVendor(qbId, vendor);
        except:
            print(f"Duplication {qbId} : {vendor}")
        time = response['time'];
    Trunk.data['lastUpdatedVendorTime'] = time;
    Trunk.writeData("api_key.txt");
    print(f"Finish updateing vendor till {Trunk.data['lastUpdatedVendorTime']}");
    return;

SQLiteController.initialSetup();
#updateVendor();
#updateProduct();
updateInvoices();
