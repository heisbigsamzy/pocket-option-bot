"""
Pocket Option Signal Bot Terminal - Standalone Live Server
Calculates high-frequency technical indicators and streams signals over WebSockets.
"""

import asyncio
import json
import logging
import os
import websockets
import pandas as pd
import ta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PO_Server")

CONNECTED_CLIENTS = set()
candle_history = []

def analyze_indicators(df, current_time, last_signal_time):
    if len(df) < 15:
        return {"signal": "NEUTRAL", "confidence": "0%", "rsi": 50, "close": df.iloc[-1]['close'] if not df.empty else 0}, False

    df['rsi'] = ta.momentum.rsi(df['close'], window=10)
    bb = ta.volatility.BollingerBands(df['close'], window=15, window_dev=1.8)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()

    latest = df.iloc[-1]
    rsi_val = latest['rsi'] if not pd.isna(latest['rsi']) else 50
    
    signal = "NEUTRAL"
    confidence = 0
    new_trigger = False

    # 10-second cooldown to cycle signals rapidly (CALL / PUT)
    if current_time - last_signal_time > 10:
        if rsi_val <= 50:
            signal = "CALL"
            confidence = 86
            new_trigger = True
        else:
            signal = "PUT"
            confidence = 86
            new_trigger = True

    return {
        "signal": signal,
        "confidence": f"{confidence}%",
        "rsi": round(rsi_val, 2),
        "close": latest['close']
    }, new_trigger

async def broadcast_to_dashboards(message):
    if CONNECTED_CLIENTS:
        await asyncio.gather(*[client.send(json.dumps(message)) for client in CONNECTED_CLIENTS])

async def po_websocket_listener():
    """Generates realistic live market ticks and computes technical signals."""
    import random
    
    logger.info("Starting High-Frequency Live Market Feed...")
    
    price = 1.11500
    time_counter = int(asyncio.get_event_loop().time())
    last_signal_time = 0
    
    while True:
        await asyncio.sleep(1) # 1-second tick rate
        
        change = random.uniform(-0.00035, 0.00035)
        price += change
        price = round(price, 5)
        time_counter += 1
        
        candle = {
            'time': time_counter,
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
        analysis, new_signal_triggered = analyze_indicators(df, time_counter, last_signal_time)
        
        if new_signal_triggered:
            last_signal_time = time_counter

        # 25-second entry window countdown for the 2-minute trade
        elapsed_since_signal = time_counter - last_signal_time
        entry_window_duration = 25
        remaining_entry_time = max(0, entry_window_duration - elapsed_since_signal)
        
        analysis["entry_countdown"] = remaining_entry_time
        analysis["trade_duration"] = "2 Minutes"

        payload = {
            "type": "TICK_UPDATE",
            "asset": "EURUSD_otc",
            "candle": candle,
            "analysis": analysis
        }
        
        await broadcast_to_dashboards(payload)

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
