from ultralytics import YOLO


model = YOLO("./model/model.pt")

def find_carpark(image_path):
    results = model.predict(image_path, verbose =False)
    result = results[0]

    empty_count = 0
    occupied_count = 0
    occupied_percentage = []

    for box in results.boxes:
        label = result.names[int(box.cls[0].item())]
        percentage = float(box.conf[0].item())

        occupied_percentage.append(percentage)

        if label == "empty":
            empty_count +=1 

        elif label == "occupied":
            occupied_pe