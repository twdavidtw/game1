from flask import Flask, render_template, request, jsonify
import psycopg2
import psycopg2.extras
from config import load_config, save_config
from setup_db import setup_database
import subprocess
import threading

app = Flask(__name__)

def get_db_connection():
    config = load_config()
    return psycopg2.connect(
        dbname=config.get("db_name", "stock_db"),
        user=config.get("db_user", "postgres"),
        password=config.get("db_password", ""),
        host=config.get("db_host", "localhost"),
        port=config.get("db_port", "5432"),
        options="-c client_encoding=UTF8"
    )

@app.route('/')
def index():
    config = load_config()
    db_status = "Not checked"
    try:
        if config.get("db_password"):
             conn = get_db_connection()
             conn.close()
             db_status = "Connected"
        else:
             db_status = "Waiting for configuration"
    except Exception as e:
        db_status = f"Error: {e}"
    return render_template('index.html', config=config, db_status=db_status)

@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.json
    save_config(data)
    success, msg = setup_database()
    return jsonify({"success": success, "message": msg})

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/options')
def get_options():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT stock_code, stock_name FROM companies ORDER BY stock_code")
        companies = cur.fetchall()
        cur.execute("SELECT DISTINCT trade_date FROM trading_volume ORDER BY trade_date DESC LIMIT 30")
        dates = [row['trade_date'].strftime('%Y-%m-%d') for row in cur.fetchall()]
        cur.execute("SELECT DISTINCT session_time FROM trading_volume ORDER BY session_time")
        sessions = [row['session_time'] for row in cur.fetchall()]
        conn.close()
        return jsonify({"companies": companies, "dates": dates, "sessions": sessions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard/top_stocks')
def top_stocks():
    # 支援日期區間與時段區間
    start_date = request.args.get('start_date') or request.args.get('trade_date')
    end_date = request.args.get('end_date') or request.args.get('trade_date')
    start_session = request.args.get('start_session', '') or request.args.get('session_time', '')
    end_session = request.args.get('end_session', '') or request.args.get('session_time', '')

    if not start_date or not end_date:
        return jsonify({"error": "Missing start_date or end_date"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        params = [start_date, end_date]
        session_filter = ""
        if start_session:
            session_filter += " AND tv.session_time >= %s"
            params.append(start_session)
        if end_session:
            session_filter += " AND tv.session_time <= %s"
            params.append(end_session)

        query = f"""
            SELECT c.stock_code, c.stock_name,
                   SUM(tv.buy_volume + tv.sell_volume) AS total_volume,
                   SUM(tv.buy_volume - tv.sell_volume) AS net_volume
            FROM trading_volume tv
            JOIN companies c ON tv.stock_code = c.stock_code
            WHERE tv.trade_date BETWEEN %s AND %s {session_filter}
            GROUP BY c.stock_code, c.stock_name
            ORDER BY total_volume DESC
            LIMIT 30
        """
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        # 轉為整數張數
        for row in rows:
            row['total_volume'] = int(round(row['total_volume']))
            row['net_volume'] = int(round(row['net_volume']))
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard/stock_details')
def get_stock_details():
    start_date = request.args.get('start_date') or request.args.get('trade_date')
    end_date = request.args.get('end_date') or request.args.get('trade_date')
    stock_code = request.args.get('stock_code')
    start_session = request.args.get('start_session', '') or request.args.get('session_time', '')
    end_session = request.args.get('end_session', '') or request.args.get('session_time', '')

    if not start_date or not end_date or not stock_code:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 1. 股價資訊：取區間最後一天
        cur.execute("""
            SELECT close_price, open_price, high_price, low_price, trade_shares, trade_amount
            FROM stock_prices_3104
            WHERE stock_code = %s AND trade_date BETWEEN %s AND %s
            ORDER BY trade_date DESC
            LIMIT 1
        """, (stock_code, start_date, end_date))
        price_info = cur.fetchone() or {}
        if price_info and price_info.get('trade_shares'):
            # 股數 -> 張數，取整
            price_info['trade_shares'] = int(round(price_info['trade_shares'] / 1000.0))

        # 2. 券商買賣超明細（區間累計）
        params = [start_date, end_date, stock_code]
        session_filter = ""
        if start_session:
            session_filter += " AND tv.session_time >= %s"
            params.append(start_session)
        if end_session:
            session_filter += " AND tv.session_time <= %s"
            params.append(end_session)

        cur.execute(f"""
            SELECT b.broker_name,
                   SUM(tv.buy_volume) AS total_buy,
                   SUM(tv.sell_volume) AS total_sell,
                   SUM(tv.buy_volume - tv.sell_volume) AS net_buy
            FROM trading_volume tv
            JOIN brokers b ON tv.broker_code = b.broker_code
            WHERE tv.trade_date BETWEEN %s AND %s
              AND tv.stock_code = %s {session_filter}
            GROUP BY b.broker_code, b.broker_name
        """, params)
        brokers_vol = cur.fetchall()

        # 轉為整數張數
        for b in brokers_vol:
            b['total_buy'] = int(round(b['total_buy']))
            b['total_sell'] = int(round(b['total_sell']))
            b['net_buy'] = int(round(b['net_buy']))

        sorted_by_net = sorted(brokers_vol, key=lambda x: x['net_buy'], reverse=True)
        top_buyers = [r for r in sorted_by_net if r['net_buy'] > 0][:10]
        top_sellers = [r for r in sorted_by_net if r['net_buy'] < 0]
        top_sellers = sorted(top_sellers, key=lambda x: x['net_buy'])[:10]

        buy_broker_count = len([r for r in brokers_vol if r['net_buy'] > 0])
        sell_broker_count = len([r for r in brokers_vol if r['net_buy'] < 0])
        total_buy_vol = sum(r['total_buy'] for r in brokers_vol)
        total_sell_vol = sum(r['total_sell'] for r in brokers_vol)
        net_vol = total_buy_vol - total_sell_vol

        # 3. 處置股與注意股（區間內）
        cur.execute("""
            SELECT date_start, date_end, condition_desc
            FROM disposal_stocks
            WHERE stock_code = %s
              AND (date_start <= %s AND date_end >= %s)
        """, (stock_code, end_date, start_date))
        disposal_info = cur.fetchall()

        cur.execute("""
            SELECT attention_date, reason
            FROM attention_stocks
            WHERE stock_code = %s
              AND attention_date BETWEEN %s AND %s
        """, (stock_code, start_date, end_date))
        attention_info = cur.fetchall()

        conn.close()

        # 日期格式化
        for row in disposal_info:
            if not isinstance(row['date_start'], str):
                row['date_start'] = row['date_start'].strftime('%Y-%m-%d')
                row['date_end'] = row['date_end'].strftime('%Y-%m-%d')
        for row in attention_info:
            if not isinstance(row['attention_date'], str):
                row['attention_date'] = row['attention_date'].strftime('%Y-%m-%d')

        return jsonify({
            "price_info": price_info,
            "brokers": {
                "details": brokers_vol,          # 全部券商明細
                "top_buyers": top_buyers,
                "top_sellers": top_sellers,
                "buy_count": buy_broker_count,
                "sell_count": sell_broker_count,
                "total_buy_vol": total_buy_vol,
                "total_sell_vol": total_sell_vol,
                "net_vol": net_vol
            },
            "auxiliary": {
                "disposal": disposal_info,
                "attention": attention_info
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard/trend')
def get_trend():
    # 維持單日查詢（用於最後一天的走勢）
    trade_date = request.args.get('trade_date')
    stock_code = request.args.get('stock_code')
    if not stock_code or not trade_date:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT session_time,
                   SUM(buy_volume + sell_volume) AS total_volume,
                   SUM(buy_volume - sell_volume) AS net_volume
            FROM trading_volume
            WHERE trade_date = %s AND stock_code = %s
            GROUP BY session_time
            ORDER BY session_time
        """, (trade_date, stock_code))
        rows = cur.fetchall()
        conn.close()
        for row in rows:
            row['total_volume'] = int(round(row['total_volume']))
            row['net_volume'] = int(round(row['net_volume']))
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ingest', methods=['POST'])
def trigger_ingest():
    action = request.json.get('action')
    def run_script(script_name):
        subprocess.Popen(['python', f'd:\\AI\\股票\\管理系統\\{script_name}'])

    if action == '2026':
        threading.Thread(target=lambda: run_script('ingest_2026.py')).start()
    elif action == '3104':
        threading.Thread(target=lambda: run_script('ingest_3104.py')).start()
    elif action == 'aux':
        threading.Thread(target=lambda: run_script('ingest_aux_csv.py')).start()
    elif action == 'tpex_api':
        return jsonify({"message": "Triggered API fetcher", "status": "Not completely implemented yet"}), 200
    else:
        return jsonify({"error": "Unknown action"}), 400

    return jsonify({"message": f"Ingestion {action} triggered in background."})

if __name__ == '__main__':
    app.run(debug=True, port=5000)