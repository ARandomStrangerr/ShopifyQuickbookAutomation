import requests;
import Trunk;
import urllib.parse;
import webbrowser;
import socket;
import time;
import SQLiteController;

def __openOAuth():
    redirectUri = "https://"+Trunk.data['redirectUri']+"/";
    state = Trunk.data['state'];
    authroizationUrl = f"https://appcenter.intuit.com/connect/oauth2" \
    + f"?client_id={Trunk.data['qbClientId']}" \
    + f"&redirect_uri={urllib.parse.quote(redirectUri)}" \
    + f"&response_type=code" \
    + f"&scope={urllib.parse.quote('com.intuit.quickbooks.accounting openid profile email')}" \
    + f"&state={state}";
    webbrowser.open(authroizationUrl);
    return;

def __getCode():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
        soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1);
        soc.bind(('localhost', 8000));
        soc.listen(5);
        clientSoc, clientAddr = soc.accept();
        data = clientSoc.recv(1024);
        print(data);
        data = str(data);
        data = data.split('\r\n')[0].split("=")[1].split("&")[0];
    return data;

def __exchangeCodeForToken(code: str):
    redirectUri = "https://"+Trunk.data['redirectUri']+"/";
    uri = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer';
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    };
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirectUri
    };
    response = requests.post(uri, headers=headers, data=data, auth=(Trunk.data['qbClientId'], Trunk.data['qbSlientSecret']));
    Trunk.data['accessToken'] = response.json()['access_token'];
    Trunk.data['refreshToken'] = response.json()['refresh_token'];
    Trunk.data['accessTokenExpiration'] = str(int(response.json()['expires_in']) + time.time());
    Trunk.data['refreshTokenExpiration'] = str(int(response.json()['x_refresh_token_expires_in']) + time.time());
    Trunk.writeData("./api_key.txt");
    return;

def __refreshAccessToken():
    uri = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer';
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    };
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': Trunk.data['refreshToken']
    };
    response = requests.post(uri, headers=headers, data=data, auth=(Trunk.data['qbClientId'], Trunk.data['qbSlientSecret']));
    Trunk.data['accessToken'] = response.json()['access_token'];
    Trunk.data['refreshToken'] = response.json()['refresh_token'];
    Trunk.data['accessTokenExpiration'] = str(int(response.json()['expires_in']) + time.time());
    Trunk.data['refreshTokenExpiration'] = str(int(response.json()['x_refresh_token_expires_in']) + time.time());
    Trunk.writeData("./api_key.txt");
    return;

def __authProcess():
    currentTime = time.time();
    if ("accessToken" not in Trunk.data.keys()
        or currentTime > float(Trunk.data['accessTokenExpiration'])
        and currentTime >= float(Trunk.data['refreshTokenExpiration'])):
        __openOAuth();
        code:str = __getCode();
        __exchangeCodeForToken(code);
    elif (currentTime > float(Trunk.data['accessTokenExpiration'])
          and currentTime < float(Trunk.data['refreshTokenExpiration'])):
        __refreshAccessToken();
    return;

def __makeRequest(method, uri, params, json):
    header = {
        "Authorization": f"bearer {Trunk.data['accessToken']}",
        "Accept": "application/json"
    };
    __authProcess();
    response = requests.request(method=method, url=uri, headers=header, params=params, json=json);
    return response;

def __prepProductToPush(product: dict):
    itemList: list[dict] = [];
    for variant in product['variants']:
        name:str = product["title"] + ("" if variant["title"] == 'Default Title' else f" - {variant['title']}");
        singleProduct = {
            "Name": name,
            "UnitPrice": variant['price'],
            "Type": "Inventory",
            "TrackQtyOnHand": True,
            "QtyOnHand": variant['stock'],
            "InvStartDate": "2015-01-19",
            "ExpenseAccountRef": {
                "value": 20,
                "name": "CoGS"
            },
            "AssetAccountRef": {
                "value": 1150040005,
                "name": "Inventory"
            },
            "IncomeAccountRef": {
                "value": 1150040007,
                "name": "Sale Income"
            },
        };
        itemList.append(singleProduct);
    return itemList;

def __pushProduct(product: dict):
    response = __makeRequest("POST",
                             f'https://quickbooks.api.intuit.com/v3/company/{Trunk.data["qbCompanyId"]}/item',
                             {"minorversion": 73},
                             product);
    return response.json();
def __getProductSyncToken(id):
    response = __makeRequest("GET",
                             f'https://quickbooks.api.intuit.com/v3/company/{Trunk.data["qbCompanyId"]}/query',
                             {'query': f"SELECT SyncToken FROM Item WHERE Id='{id}'"},
                             {});
    return response.json()['QueryResponse']['Item'][0]['SyncToken'];

def __prepInvoiceToPush(orderList: list[dict]):
    invoiceList = [];
    for order in orderList:
        # declare general information of an invoice
        prepOrder = {};
        prepOrder['DocNumber'] = order['id'];
        prepOrder['TxnDate'] = order['date'];
        prepOrder['DueDate'] = order['date'];
        prepOrder['GlobalTaxCalculation'] = 'TaxExcluded';
        prepOrder['CustomerRef'] = {};
        prepOrder['CustomerRef']['value'] = 2;
        prepOrder['DepartmentRef'] = {};
        try:
            if (order['location'] == "Churi"):
                prepOrder['DepartmentRef']["value"] = '2';
                prepOrder['DepartmentRef']["name"] = 'CHURI - New Westminster';
        except:
            prepOrder['DepartmentRef']['name'] = "Online";
        prepOrder['Line'] = [];
        # declare each item of the invoice
        for item in order['item']:
            totalTaxRate = 0;
            lineItem = {};
            itemQuery = SQLiteController.queryItem(item['name']);
            if (itemQuery):
                vendorQuery = SQLiteController.queryVendor(item['vendor']);
            else:
#                itemQuery = SQLiteController.queryItem("Custom Sale");
#                vendorQuery = SQLiteController.queryVendor("Custom Sale");
                itemQuery = ["1437", "Custom Sale"];
                vendorQuery = ["886379", "Custom Sale"];
                lineItem['Description'] = item['name'];
            lineItem['DetailType'] = 'SalesItemLineDetail';
            lineItem['SalesItemLineDetail'] = {};
            lineItem['SalesItemLineDetail']['ItemRef'] = {};
            lineItem['SalesItemLineDetail']['ItemRef']['value'] = itemQuery[0];
            lineItem['SalesItemLineDetail']['ItemRef']['name'] = itemQuery[1];
            lineItem['SalesItemLineDetail']['ClassRef'] = {};
            lineItem['SalesItemLineDetail']['ClassRef']['value'] = vendorQuery[0];
            lineItem['SalesItemLineDetail']['ClassRef']['name'] = vendorQuery[1];
            lineItem['SalesItemLineDetail']['Qty'] = item['quantity'];
            lineItem['Amount'] = float(item['originalPrice']) * int(item['quantity']);
            lineItem['SalesItemLineDetail']['TaxCodeRef'] = {};
            for tax in item['tax']:
                totalTaxRate += float(tax['rate']);
            if totalTaxRate == 0:
                lineItem['SalesItemLineDetail']['TaxCodeRef']['value'] = 3;
            elif totalTaxRate - 0.05 < 0.01 :
                lineItem['SalesItemLineDetail']['TaxCodeRef']['value'] = 4;
            elif totalTaxRate - 0.07 < 0.01:
                lineItem['SalesItemLineDetail']['TaxCodeRef']['value'] = 10;
            elif totalTaxRate - 0.12 < 0.01:
                lineItem['SalesItemLineDetail']['TaxCodeRef']['value'] = 8;
            prepOrder['Line'].append(lineItem);
        # declare discount of an invoice
        discount = float(order['discount'][0]);
        if (discount!= 0.0):
            discountLine = {};
            discountLine['DetailType'] = 'DiscountLineDetail';
            discountLine['DiscountLineDetail'] = {};
            discountLine['DiscountLineDetail']['DiscountAccountRef'] = {};
            discountLine['DiscountLineDetail']['DiscountAccountRef']['value'] = "1150040008";
            discountLine['DiscountLineDetail']['DiscountAccountRef']['name'] = "Discount";
            discountLine['Amount'] = str(discount);
            prepOrder['Line'].append(discountLine);
        invoiceList.append(prepOrder);
    return invoiceList;

def __pushInvoice(invoiceList: list[dict]):
    uri: str = f'https://quickbooks.api.intuit.com/v3/company/{Trunk.data["qbCompanyId"]}/invoice';
    headers = {
        "Authorization": f"bearer {Trunk.data['accessToken']}",
        "Accept": "application/json"
    };
    for invoice in invoiceList:
        response = requests.post(uri, headers=headers, json=invoice);
    return;

def __pushVendor(vendor):
    __authProcess();
    uri = f'https://quickbooks.api.intuit.com/v3/company/{Trunk.data["qbCompanyId"]}/class?minorversion=40';
    headers = {
        "Authorization": f"bearer {Trunk.data['accessToken']}",
        "Accept": "application/json"
    };
    jsonBody = {
        "Name": vendor
    };
    response = requests.post(uri, headers=headers, json=jsonBody);
    return response;

def getAccountInfo():
    __authProcess();
    uri = f'https://quickbooks.api.intuit.com/v3/company/{Trunk.data["qbCompanyId"]}/query';
    headers = {
        "Authorization": f"bearer {Trunk.data['accessToken']}",
        "Accept": "application/json"
    };
    params = {
        "query": "SELECT * FROM Account"
    }
    response = requests.get(url=uri, headers=headers, params=params);
    print(response.text);
    return;

def downloadProduct(start=1, max=50):
    __authProcess();
    uri = f'https://quickbooks.api.intuit.com/v3/company/{Trunk.data["qbCompanyId"]}/query';
    headers = {
        "Authorization": f"bearer {Trunk.data['accessToken']}",
        "Accept": "application/json"
    };
    params = {
        'query': f"select * from Item STARTPOSITION {start} MAXRESULTS {max}"
    };
    response = requests.get(url=uri, headers=headers, params=params);
    response = response.json()['QueryResponse']['Item'];
    return response, (start + max) if (len(response) == max) else None;

def updateProduct(updateJson):
    __authProcess();
    uri = f'https://quickbooks.api.intuit.com/v3/company/{Trunk.data["qbCompanyId"]}/item?minorversion=4';
    headers = {
        "Authorization": f"bearer {Trunk.data['accessToken']}",
        "Accept": "application/json"
    };
    response = requests.post(uri, headers=headers, json=updateJson);
    print(response.json());

def updateItem(posData: dict):
    __authProcess();
    uri = f'https://quickbooks.api.intuit.com/v3/company/9341453809626652/item?minorversion=75';
    
    return;

def downloadClass(start=1, max=50):
    __authProcess();
    uri = f'https://quickbooks.api.intuit.com/v3/company/{Trunk.data["qbCompanyId"]}/query';
    headers = {
        "Authorization": f"bearer {Trunk.data['accessToken']}",
        "Accept": "application/json"
    };
    params = {
        'query': f"select Id, name from Class STARTPOSITION {start} MAXRESULTS {max}"
    };
    response = requests.get(url=uri, headers=headers, params=params);
    response = response.json()['QueryResponse']['Class'];
    return response;

def pushInvoice(invoiceList):
    __authProcess();
    invoiceList = __prepInvoiceToPush(invoiceList)
    __pushInvoice(invoiceList);
    return;
