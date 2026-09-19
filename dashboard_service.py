import io
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

def create_dashboard(carpark_status):

    carpark_ids = []
    available_spaces = []

    for carpark in carpark_status:
        carpark_ids.append(carpark["carpark_id"])
        available_spaces.append(carpark["available_parking"])


    plt.figure(figsize=(10, 6))
    plt.bar(carpark_ids, available_spaces, color='skyblue')

    plt.title('Available Parking Spaces by Car Park')
    plt.xlabel('Car Park ID')
    plt.ylabel('Available Spaces')

    plt.tight_layout()

    img_buffer = io.BytesIO()

    plt.savefig(img_buffer, format='png')

    plt.close()

    img_buffer.seek(0)

    return img_buffer