import os
import shutil
import random
from ultralytics import YOLO
from PIL import Image
from yolo_service import find_parking
from carpark_service import carparks, analyse_carpark
from carpark_service import take_photo


# This python script just provides the bear minimum on how to load and use the model.
# You shall use the python best practices for exception handling/logging in your own code.



result = find_parking("./images/img305.jpg")

print(result)
print(carparks[0])
print(take_photo())
result1 = analyse_carpark(carparks[0])

print(result1)