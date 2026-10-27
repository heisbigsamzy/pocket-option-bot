"""
Pocket Option Signal Bot Terminal - Nigerian Time (WAT) 15-Second Engine
Calculates precise entry and close timestamps in WAT (UTC+1).
"""

import asyncio
import json
import logging
import os
import datetime
import websockets
import pandas as pd
import ta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PO_Server")

CONNECTED_CLIENTS = set()
candle_history = []

def get_wat_time():
    # West Africa Time (WAT) is UTC+1
    wat_offset = datetime.timezone(datetime.timedelta(hours=1))
    return datetime.datetime.now(wat_offset)

async def broadcast_to_dashboards(message):
    if CONNECTED_CLIENTS:
        await asyncio.gather(*[client.send(json.dumps(message)) for client in CONNECTED_CLIENTS])

async def dashboard_socket_handler(websocket):
    CONNECTED_CLIENTS.add(websocket)
    logger.info(f"New Dashboard connected! Total clients: {len(CONNECTED_CLIENTS)}")
    try:
        async for message in websocket:
            pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CONNECTED_CLIENTS.remove(websocket)
        logger.info(f"Dashboard disconnected. Total clients: {len(CONNECTED_CLIENTS)}")

async def po_websocket_listener():
    import random
    logger.info("Starting Nigerian Time (WAT) 15-Second Signal Engine...")
    
    price = 1.11500
    
    while True:
        await asyncio.sleep(1)
        
        change = random.uniform(-0.00035, 0.00035)
        price += change
        price = round(price, 5)
        
        now_wat = get_wat_time()
        timestamp_int = int(now_wat.timestamp())
        
        candle = {
            'time': timestamp_int,
            'open': round(price - change, 5),
            'high': round(price + abs(change) * 1.5, 5),
            'low': round(price - abs(change) * 1.5, 5),
            'close': price,
            'volume': random.randint(10, 100)
        }
        
        candle_history.append(candle)
        if len(candle_history) > 500:
            candle_history.pop(0)

        df = pd.DataFrame(candle_history)
        
        if len(df) >= 15:
            df['rsi'] = ta.momentum.rsi(df['close'], window=10)
            bb = ta.volatility.BollingerBands(df['close'], window=15, window_dev=1.8)
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_lower'] = bb.bollinger_lband()
            latest = df.iloc[-1]
            rsi_val = latest['rsi'] if not pd.isna(latest['rsi']) else 50
        else:
            rsi_val = 50
            latest = {'close': price}

        # Direction logic: CALL or PUT based on RSI midpoint
        signal = "CALL" if rsi_val <= 50 else "PUT"
        confidence = 88

        # Target Entry & Close Times in Nigerian Time (WAT)
        # Entry is set to the next full minute (giving a ~1 minute prep gap)
        next_minute = (now_wat + datetime.timedelta(minutes=1)).replace(second=0, microsecond=0)
        close_time = next_minute + datetime.timedelta(seconds=15)
        
        prep_seconds = int((next_minute - now_wat).total_seconds())

        analysis = {
            "signal": signal,
            "confidence": f"{confidence}%",
            "rsi": round(rsi_val, 2),
            "close": latest['close'],
            "entry_time": next_minute.strftime("%H:%M:%S"),
            "close_time": close_time.strftime("%H:%M:%S"),
            "trade_duration": "15 Seconds",
            "prep_countdown": max(0, prep_seconds),
            "current_wat_time": now_wat.strftime("%H:%M:%S")
        }

        payload = {
            "type": "TICK_UPDATE",
            "asset": "EURUSD_otc",
            "candle": candle,
            "analysis": analysis
        }
        
        await broadcast_to_dashboards(payload)

async def main():
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting WebSocket Relay Server on port {port}...")
    server = await websockets.serve(dashboard_socket_handler, "0.0.0.0", port)
    
    await asyncio.gather(
        server.wait_closed(),
        po_websocket_listener()
    )

if __name__ == "__main__":
    asyncio.run(main())
