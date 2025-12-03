# backend/server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse
import joblib
import numpy as np
import uvicorn
import asyncio
import pathlib

app = FastAPI()

# -----------------------
# Serve live dashboard
# -----------------------
ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE_HTML_PATH = ROOT / "live.html"

@app.get("/live")
async def live_page():
    if LIVE_HTML_PATH.exists():
        return FileResponse(str(LIVE_HTML_PATH))
    return {"error": "live.html not found"}


# -----------------------
# WebSocket setup
# -----------------------
connected_clients = set()

async def broadcast_event(data: dict):
    """Send events to all connected WebSocket clients."""
    remove_list = []
    for ws in connected_clients:
        try:
            await ws.send_json({"type": "event", "payload": data})
        except:
            remove_list.append(ws)

    # Remove dead/broken websocket clients
    for ws in remove_list:
        connected_clients.discard(ws)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    print("Client connected to WebSocket")

    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print("Client disconnected from WebSocket")


# -----------------------
# ML Model Load
# -----------------------
MODEL_PATH = "models/iforest.joblib"
SCALER_PATH = "models/scaler.joblib"

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)


# -----------------------
# ML scoring endpoint
# -----------------------
@app.post("/score")
async def score(req: Request):
    payload = await req.json()
    X = np.array([[payload.get("connection_duration", 0.0),
                   payload.get("packet_size", 0.0),
                   payload.get("port_number", 0)]])
    Xs = scaler.transform(X)
    score = float(model.decision_function(Xs)[0])
    label = "Anomaly" if model.predict(Xs)[0] == -1 else "Normal"
    return {"score": score, "label": label}


# -----------------------
# EVENT endpoint — IMPORTANT
# -----------------------
@app.post("/events")
async def receive_event(payload: dict):

    # broadcast to all connected WebSocket clients
    await broadcast_event(payload)

    return {"status": "ok"}


# -----------------------
# Server start
# -----------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005, reload=False)
