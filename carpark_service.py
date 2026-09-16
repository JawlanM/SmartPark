import os
import random
from yolo_service import find_parking

imgs_folder = "./images"

NUM_carparks = 10

carparks = []

for i in range(1, NUM_carparks + 1):
    carparks.append({
        "carpark_id": f"CBD_{i:03}",
        "name": f"CBD Car Park {i}"
    })

def take_photo():
    img_files = [
        f for f in os.listdir(imgs_folder)
        if f.lower().endswith(".jpg")
    ]

    random_image = random.choice(img_files)

    return os.path.join(imgs_folder, random_image)

def analyse_carpark(carpark):
    img_path = take_photo()
    parking_result = find_parking(img_path)

    return{
        "carpark_id": carpark["carpark_id"],
        "name": carpark["name"],
        "available_parking": parking_result["available_parking"],
        "occupied_parking": parking_result["occupied_parking"],
        "total_parking": parking_result["total_parking"],
        "occupied_percentage": parking_result["occupied_percentage"]
    }

def find_best_carparks(n):

    SUM_target_carparks = 2 * n

    selected_carparks = random.sample(carparks, SUM_target_carparks)

    target_carparks = []

    for carpark in selected_carparks:
        result = analyse_carpark(carpark)
        target_carparks.append(result)

    target_carparks.sort(
        key=lambda carpark: carpark["available_parking"],
        reverse=True
    )

    return target_carparks[:n]

def get_carpark_by_id(carpark_id):
    for carpark in carparks:
        if carpark["carpark_id"] == carpark_id:
            return carpark

    return None


    


