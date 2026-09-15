from ultralytics import YOLO


model = YOLO("./model/model.pt")

def find_parking(image_path):
    results = model.predict(image_path, verbose =False)
    result = results[0]

    empty_count = 0
    occupied_count = 0
    occupied_percentage = []

    for box in result.boxes:
        label = result.names[int(box.cls[0].item())]
        percentage = float(box.conf[0].item())

        occupied_percentage.append(percentage)

        if label == "empty":
            empty_count +=1 

        elif label == "occupied":
            occupied_count += 1

    total_parking = empty_count + occupied_count

    avg_percentage = (
        sum(occupied_percentage) / len(occupied_percentage)
        if occupied_percentage
        else 0
    )

    return {
        "available_parking": empty_count,
        "occupied_parking": occupied_count,
        "total_parking": total_parking,
        "occupied_percentage": round(avg_percentage, 4)
    }