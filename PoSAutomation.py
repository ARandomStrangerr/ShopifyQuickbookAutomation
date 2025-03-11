import requests;
import Trunk;
from datetime import datetime;

# get call shopify graphQL end point.
def __makeRequest(query: str):
    url = f"https://{Trunk.data['posStoreName']}.myshopify.com/admin/api/2024-10/graphql.json";
    header = {
        "X-Shopify-Access-Token": Trunk.data['posAccessToken'],
        "Content-Type": "application/json"
    };
    return requests.post(url= url, headers=header, json={"query": query});

def getOrderData(startDate: str ="2025-01-01", endDate: str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), cursor="", limit: int=5):
    """
    get order data from shopify within date rage.
    if this function is supplied startDate, then it will be treated as new query to shopify, and the endDate will be default at the current moment
    if this function is supplied cursor, then it will be treated as continue previous query that return the cursor. (will ignore startDate and endDate parameters)

    PARAMS:
    startDate (str): start date of  the query
    endDate(str): end date of the query
    cursor(str): continue previous query
    limit(int): the number of return result

    RETURN:
    tuple(list[dict], str | None)
        the list is the cleaned up version of the query
        str is the cursor to continue this query
        None when there is no more result form this query
    """
    queryInfo = f'first:{limit}' + (f' after:"{cursor}"' if cursor!="" else f' query: "created_at:>={startDate} AND created_at:<={endDate}"')
    query = f"""
        query {{
            orders({queryInfo}) {{
                edges {{
                    node {{
                        name
                        createdAt
                        sourceName
                        retailLocation {{
                            name
                        }}
                        totalReceivedSet {{
                            shopMoney{{
                                amount
                            }}
                        }}
                        totalDiscountsSet {{
                            shopMoney {{
                                amount
                            }}
                        }}
                        lineItems(first: 50) {{
                            edges {{
                                node {{
                                    name
                                    quantity
                                    vendor
                                    originalUnitPriceSet {{
                                        shopMoney {{
                                            amount
                                        }}
                                    }}
                                    discountedTotalSet {{
                                        shopMoney {{
                                            amount
                                        }}
                                    }}
                                    taxLines {{
                                        priceSet {{
                                            shopMoney {{
                                                amount
                                            }}
                                        }}
                                        rate
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
                pageInfo {{
                    hasNextPage
                    endCursor
                }}
            }}
        }}
    """;
    extractedOrders = [];
    response = __makeRequest(query);
    response = response.json();
    # extract data from graphQL
    for order in response['data']['orders']['edges']: # separate order from list of orders
        order = order['node'];
        extractedOrder = {}
        extractedOrder['id'] = order['name'];
        try:
            extractedOrder['location'] = order['retailLocation']['name'];
        except:
            extractedOrder['location'] = "Online";
        extractedOrder['date']= order['createdAt'];
        extractedOrder['amount'] =  order['totalReceivedSet']['shopMoney']['amount'];
        extractedOrder['discount'] = order['totalDiscountsSet']['shopMoney']['amount'],
        extractedOrder['item'] = [];
        for item in order['lineItems']['edges']: # separate item from list of items
            item = item['node'];
            extractedItem = {};
            extractedItem['name']= item['name'];
            extractedItem['vendor'] = item['vendor'];
            extractedItem['quantity'] = item['quantity'];
            extractedItem['originalPrice'] = item['originalUnitPriceSet']['shopMoney']['amount'];
            extractedItem['discount'] = float(item['originalUnitPriceSet']['shopMoney']['amount']) - float(item['discountedTotalSet']['shopMoney']['amount']);
            extractedItem['tax'] = [];
            for taxLine in item['taxLines']: # separate tax from list of tax (5% and 7%)
                extractedItem['tax'].append({
                    'amount': taxLine['priceSet']['shopMoney']['amount'],
                    'rate': taxLine['rate']
                });
            extractedOrder['item'].append(extractedItem); # add item into list of items of this order
        extractedOrders.append(extractedOrder); # add order into list of orders
    if (bool(response['data']['orders']['pageInfo']['hasNextPage'])):
        cursor = response['data']['orders']['pageInfo']['endCursor'];
    else:
        cursor = None ;
    return extractedOrders, cursor;

def getProductData(startDate:str | None = None, cursor: str | None = None, limit = 5):
    """
    get product data from shopify.
    if startDate is provided then it will look for updated products after the specifed date to now.
    if this function is supplied cursor, then it will be treated as continue previous query that return the cursor. (will ignore startDate parameter)
    if neither startDate or cursor is supplied, then the query will fetch all data within the product

    PARAM:
    startDate (str): starting date of this query
    endDate (str): end date of this query
    cursor (str): continue previous query
    limit (int): number of result return

    RETURN:
    tuple[list[dict], str | None]
        the list is the cleaned up version of the query
        str is the cursor to continue this query
        None when there is no more result form this query
    """
    queryCondition = f"first: {limit}";
    if cursor:
        queryCondition += f', after: "{cursor}"';
    elif startDate:
        queryCondition += f', query: "created_at:>={startDate}"';
    else:
        raise ValueError("either cursor or startDate must be provided");
    query = f'''
        query {{
            products({queryCondition}) {{
                edges {{
                    cursor
                    node {{
                        id
                        title
                        vendor
                        productType
                        createdAt
                        updatedAt
                        variants(first: 250) {{
                            edges {{
                                node {{
                                    id
                                    title
                                    price
                                    inventoryQuantity
                                }}
                            }}
                        }}
                    }}
                }}
                pageInfo {{
                    hasNextPage
                    endCursor
                }}
            }}
        }}
    ''';
    extractedProducts: list[dict[str, object]] = [];
    response = __makeRequest(query).json();
    # extract data from GraphQL
    for product in response['data']['products']['edges']:
        product = product['node'];
        extractedProduct = {}
        extractedProduct['id']= product['id'];
        extractedProduct['title']= product['title'];
        extractedProduct['vendor']= product['vendor'];
        extractedProduct['type']= product['productType'];
        extractedProduct['variants']= [];
        for variant in product['variants']['edges']:
            variant = variant["node"];
            extractedVariant = {};
            extractedVariant["id"] = variant['id'];
            extractedVariant["title"] = variant["title"];
            extractedVariant["price"] = variant["price"];
            extractedVariant["stock"] = variant["inventoryQuantity"];
            extractedProduct['variants'].append(extractedVariant);
        extractedProducts.append(extractedProduct);
    if bool(response['data']['products']['pageInfo']['hasNextPage']):
        cursor = response['data']['products']['pageInfo']['endCursor'];
    else:
        cursor=None;
    return extractedProducts, cursor;

def getVendorName(startDate: str | None = None,cursor:str | None = None, limit=5):
    queryCondition = f"first: {limit}";
    if cursor:
        queryCondition += f', after: "{cursor}"';
    elif startDate:
        queryCondition += f', query:"updated_at:>={startDate}"';
    else:
        raise ValueError ("either cursor or startDate must be provided");
    query = f'''
        query {{
            products({queryCondition}) {{
                edges {{
                    node {{
                        id
                        vendor
                    }}
                }}
                pageInfo {{
                    hasNextPage
                    endCursor
                }}
            }}
        }}''';
    m = {};   
    response = __makeRequest(query).json();
    if (response['data']['products']['pageInfo']['hasNextPage']):
        cursor = response['data']['products']['pageInfo']['endCursor'];
    else:
        cursor = None;
    for res in response['data']['products']['edges']:
        m[res['node']['vendor']] = 0;
    return list(m.keys()), cursor;

def getNetSaleByDate(date:str):
    query = f'''
        {{
            orders(first: 100, query: "processedAt:>={"date"}T00:00:00Z processedAt:<={"date"}T23:59:59Z") {{
                edges {{
                    node {{
                        id
                        processedAt
                        totalNetAmount {{
                            amount
                            currencyCode
                        }}
                    }}
                }}
            }}
        }}
    '''
    print(__makeRequest(query).json());
    return;
