import requests
import json

BASE_URL = 'http://127.0.0.1:5000'

def test():
    results = []

    try:
        # Test Options
        print("Testing /api/options...")
        r_opt = requests.get(f"{BASE_URL}/api/options").json()
        print(f"Options keys: {list(r_opt.keys())}")
        print(f"Company count: {len(r_opt.get('companies', []))}")
        print(f"Dates count: {len(r_opt.get('dates', []))}")
        print(f"Sessions: {r_opt.get('sessions', [])}")

        if not r_opt.get('dates') or not r_opt.get('companies'):
             print("ERROR: missing dates or companies in options")
        else:
            recent_date = r_opt['dates'][0]
            print(f"\nTesting /api/dashboard/top_stocks (start_date={recent_date})...")
            # Test Top Stocks
            r_top = requests.get(f"{BASE_URL}/api/dashboard/top_stocks", params={
                "start_date": recent_date,
                "end_date": recent_date
            }).json()
            print(f"Top stocks count: {len(r_top)}")
            if len(r_top) > 0:
                top_stock = r_top[0]
                print(f"Top 1: {top_stock['stock_code']} {top_stock['stock_name']} (Total Vol: {top_stock.get('total_volume')})")
                code = top_stock['stock_code']
                
                print(f"\nTesting /api/dashboard/stock_details (stock={code})...")
                # Test Stock Details
                r_det = requests.get(f"{BASE_URL}/api/dashboard/stock_details", params={
                    "stock_code": code,
                    "start_date": recent_date,
                    "end_date": recent_date
                }).json()
                
                brokers = r_det.get('brokers', {})
                print(f"Price info: {r_det.get('price_info', {})}")
                print(f"Broker buy count: {brokers.get('buy_count')}, sell count: {brokers.get('sell_count')}")
                if brokers.get('top_buyers'):
                    print(f"Top buyer: {brokers['top_buyers'][0]}")
    except Exception as e:
        print(f"Network error: {e}")

if __name__ == '__main__':
    test()
