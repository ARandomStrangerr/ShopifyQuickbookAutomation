import PoSAutomation
import QBAutomation;
import Trunk;
import SQLiteController;

def changeNameInBulk():
    items, nextPos = QBAutomation.downloadProduct();
    while (nextPos):
        for item in items:
            item['Name'] = item['Name'].replace('~', '-');
            item['FullyQualifiedName'] = item['FullyQualifiedName'].replace('~', '-');
            QBAutomation.updateProduct(item);
        item, nextPos = QBAutomation.downloadProduct(nextPos);

def seeProduct ():
    index = 1;
    while (index) :
        response, index = QBAutomation.downloadProduct(index);
        print(response);
        if len(response) < 50: 
            break;
        
def checkInventory():
    PoSAutomation.getStockChange();
    return;

Trunk.readData('api_key.txt');
checkInventory();
