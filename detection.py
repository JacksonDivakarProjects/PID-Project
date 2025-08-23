import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torch.nn.functional as F
from PIL import Image
import math
import json

# Define the PyTorch Model
class FCN(nn.Module):
    def __init__(self, in_channels=1, num_classes=7):
        super(FCN, self).__init__()
        self.conv1 = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=32, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.BatchNorm2d(32, momentum=0.01),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels=32, out_channels=32, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.MaxPool2d(kernel_size=2),
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.BatchNorm2d(64, momentum=0.01),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels=64, out_channels=64, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.MaxPool2d(kernel_size=2),
        )
        self.conv3 = nn.Sequential(
            nn.Conv2d(in_channels=64, out_channels=64, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.BatchNorm2d(64, momentum=0.01),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels=64, out_channels=64, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.MaxPool2d(kernel_size=2),
        )
        self.fc1 = nn.Sequential(
            nn.Linear(20736, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.25),
            nn.BatchNorm1d(256)
        )
        self.fc2 = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.25),
            nn.BatchNorm1d(128)
        )
        self.fc3 = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.25),
            nn.BatchNorm1d(64)
        )
        self.fc4 = nn.Linear(64, 7)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = x.reshape(x.shape[0], -1)
        x = self.fc1(x)
        x = self.fc2(x)
        x = self.fc3(x)
        x = F.softmax(self.fc4(x), dim=1)
        return x

# Helper Functions
def recolor_crop(crop):
    for i in tqdm(range(len(crop))):
        for j in range(len(crop[0])):
            if crop[i][j] >= 120:
                crop[i][j] = 225
            else:
                crop[i][j] = 0
    return crop

def invert(x):
    for i in range(len(x)):
        for j in range(len(x[0])):
            if x[i][j] > 200:
                x[i][j] = 0
            else:
                x[i][j] = 1
    return x

def get_distance(x, y):
    xmid1, ymid1 = x
    xmid2, ymid2 = y
    return math.sqrt((ymid2 - ymid1) ** 2 + (xmid2 - xmid1) ** 2)

def main():
    # Load Model
    model_location = input("Enter model location: ")
    model = FCN()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Setting model up on {device}")

    if torch.cuda.is_available():
        model.cuda()
        model.load_state_dict(torch.load(model_location))
    else:
        model.load_state_dict(torch.load(model_location, map_location=device))

    data_transform = transforms.Compose([
        transforms.Lambda(lambda x: torch.from_numpy(np.expand_dims(np.array(x), axis=0)).float())
    ])
    model.eval()
    print("Model ready")

    # Load and Process Image
    read_location = input('Enter P&ID image file: ')
    img = cv2.imread(read_location, 0)
    plt.imshow(img, cmap='gray')
    plt.show()

    x_start = int(input("x start: "))
    x_end = int(input("x_end: "))
    y_start = int(input("y_start: "))
    y_end = int(input("y_end: "))
    ready_img = img[y_start:y_end, x_start:x_end]
    print("Image to work on:")
    plt.imshow(ready_img, cmap='gray')
    plt.show()

    colorized = recolor_crop(ready_img)
    main_img = colorized.copy()
    m, n = main_img.shape

    # Object Detection
    objects_info = {}
    object_id = 0
    for i in tqdm(range(0, m - 150, 75)):
        for j in range(0, n - 150, 75):
            x_min, x_max, y_min, y_max = j, j + 150, i, i + 150
            bounding_box = [x_min, x_max, y_min, y_max]
            centroid = [x_min + 75, y_min + 75]

            window = main_img[y_min:y_max, x_min:x_max].copy()
            black_percentage = (np.count_nonzero(window == 0) / (150 * 150)) * 100

            if black_percentage > 10:
                window = invert(window)
                im_pil = Image.fromarray(window)
                im = data_transform(im_pil)
                im_a = np.expand_dims(im.numpy(), axis=0)
                t = torch.tensor(im_a).to(device)

                with torch.no_grad():
                    score = model(t)
                    _, predictions = torch.max(score, 1)
                    class_id = predictions.item()

                    if class_id != 6:
                        objects_info[object_id] = {
                            "class_id": int(class_id),
                            "bounding_box": bounding_box,
                            "centroid": centroid
                        }
                        object_id += 1
    
    # Group Bounding Boxes
    list_of_objects = list(objects_info.keys())
    groups = []
    for i in range(len(objects_info)):
        curr_obj = objects_info[list_of_objects[i]]
        temp_grp = [i]
        for j in range(len(objects_info)):
            comp_obj = objects_info[list_of_objects[j]]
            if get_distance(curr_obj['centroid'], comp_obj['centroid']) < 80 and curr_obj['class_id'] == comp_obj['class_id']:
                temp_grp.append(j)
        groups.append(sorted(list(set(temp_grp))))

    groups_dict = {}
    been_done = {}
    for i in groups:
        if i[0] not in been_done:
            been_done[i[0]] = i[0]
        main_key = been_done[i[0]]
        if main_key not in groups_dict:
            groups_dict[main_key] = []
        for j in i:
            been_done[j] = main_key
        groups_dict[main_key].extend(i)
        groups_dict[main_key] = sorted(list(set(groups_dict[main_key])))

    # Finalize Info
    final_info = {}
    for i in groups_dict.keys():
        x_min_list, y_min_list, x_max_list, y_max_list = [], [], [], []
        for j in groups_dict[i]:
            xmin, xmax, ymin, ymax = objects_info[j]['bounding_box']
            x_min_list.append(xmin)
            x_max_list.append(xmax)
            y_min_list.append(ymin)
            y_max_list.append(ymax)

        xmin, ymin, xmax, ymax = min(x_min_list), min(y_min_list), max(x_max_list), max(y_max_list)
        xmid, ymid = xmin + ((xmax - xmin) // 2), ymin + ((ymax - ymin) // 2)
        xmin, ymin, xmax, ymax = xmid - 80, ymid - 80, xmid + 80, ymid + 80

        final_info[i] = {
            "class_id": objects_info[i]['class_id'],
            "bbox": [xmin, xmax, ymin, ymax],
            "centroid": [xmid, ymid]
        }

    # Filter similar bounding boxes
    modif_info = final_info.copy()
    keys = list(modif_info.keys())
    for i in keys:
        if i not in modif_info:
            continue
        curr_obj = modif_info[i]
        x_min, x_max, y_min, y_max = curr_obj['bbox']
        window = main_img[y_min:y_max, x_min:x_max].copy()
        curr_percentage_black = (np.count_nonzero(window == 0) / (160 * 160)) * 100

        for j in keys:
            if i != j and j in modif_info:
                comp_obj = modif_info[j]
                if get_distance(curr_obj['centroid'], comp_obj['centroid']) < 150:
                    x_min_c, x_max_c, y_min_c, y_max_c = comp_obj['bbox']
                    window_c = main_img[y_min_c:y_max_c, x_min_c:x_max_c].copy()
                    comp_percentage_black = (np.count_nonzero(window_c == 0) / (160 * 160)) * 100
                    if comp_percentage_black + 1 <= curr_percentage_black:
                        del modif_info[j]

    # Draw Bounding Boxes and Save Image
    draw_img = colorized.copy()
    for i, obj in modif_info.items():
        xmin, xmax, ymin, ymax = obj['bbox']
        cv2.rectangle(draw_img, (xmin, ymin), (xmax, ymax), (0, 225, 0), 5)
        cv2.putText(draw_img, str(i), (xmin, ymin - 7), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 225, 0), 3)

    plt.figure(figsize=(15, 30))
    plt.imshow(draw_img)
    plt.show()
    cv2.imwrite("./FINAL_P&ID.jpg", draw_img)

    # Save detection results for OCR script
    with open('detection_results.json', 'w') as f:
        json.dump({
            "image_path": read_location,
            "detections": modif_info
        }, f)
    
    print("Detection complete. Results saved to detection_results.json")

if __name__ == "__main__":
    main()