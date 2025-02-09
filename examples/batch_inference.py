import argparse
import csv

import torch
import torchvision.models as models
import requests
from torchvision import datasets, transforms
from torchvision.models import ResNet50_Weights
from torch.utils.data import DataLoader, Dataset, Subset
from PIL import Image
import os

class ImageDataset(Dataset):
    def __init__(self, dataset_path, transform=None):
        self.image_paths = [os.path.join(dataset_path, fname) for fname in os.listdir(dataset_path) if fname.endswith(('.jpg', '.png'))]
        self.transform = transform

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        image = Image.open(img_path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image, img_path

def parse_args():
    parser = argparse.ArgumentParser(description="Batch Inference Script")
    parser.add_argument('--batch_size', type=int, required=True, help="Batch size for inference")
    parser.add_argument('--output', type=str, required=True, help="Output path")
    return parser.parse_args()

def main():
    args = parse_args()

    model = models.resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)
    model.eval()

    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    dataset = datasets.CIFAR10(root="./data", train=False, download=True, transform=transform)
    total_size = len(dataset)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False)

    results = []
    with torch.no_grad():
        for batch_idx, (batch_images, labels) in enumerate(dataloader):
            outputs = model(batch_images)
            predictions = torch.argmax(outputs, dim=1)
            results.extend(predictions.numpy())

    with open(f"{args.output}.csv", mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Index", "Predicted_Class"])
        writer.writerows(results)
        print(f"Inference results saved to: {args.output}.csv")
    with open(f"{args.output}.csv", mode='rb') as file:
        url = " https://8912-67-243-137-85.ngrok-free.app/submit_file"
        files = {"output_file": file}
        response = requests.post(url, files=files)

if __name__ == "__main__":
    main()