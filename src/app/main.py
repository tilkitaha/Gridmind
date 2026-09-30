from fastapi import FastAPI
from pydantic import BaseModel

from app.core import baseline_forecast, dispatch

app = FastAPI(
    title="GridMind",
    version="0.1.0",
    description="AI energy autopilot for homes, batteries, EVs and prosumers.",
)


class Payload(BaseModel):
    data: dict = {}


@app.get("/health")
def health():
    return {"status": "ok", "service": "gridmind", "version": "0.1.0"}


@app.post("/v1/dispatch")
def endpoint_dispatch(payload: Payload):
    return dispatch(payload.data)


@app.post("/v1/forecast/baseline")
def endpoint_baseline_forecast(payload: Payload):
    return baseline_forecast(payload.data)
