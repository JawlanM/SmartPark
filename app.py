from fastapi import FastAPI
from yolo_service import find_parking

app = FastAPI()

@app.get("/")
def root():
    return {"Message": "SmartPark API running"}

@app.get("/api/test")
def test_parking():
    result = find_parking("./images/img305.jpg")
    return result