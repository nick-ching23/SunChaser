# import argparse
# import csv
import requests

# import torch
# import torchvision.models as models
# from torchvision import datasets, transforms
# from torchvision.models import ResNet50_Weights
# from torch.utils.data import DataLoader, Dataset, Subset
# from PIL import Image
# import os

# class ImageDataset(Dataset):
#     def __init__(self, dataset_path, transform=None):
#         self.image_paths = [os.path.join(dataset_path, fname) for fname in os.listdir(dataset_path) if fname.endswith(('.jpg', '.png'))]
#         self.transform = transform

#     def __len__(self):
#         return len(self.image_paths)

#     def __getitem__(self, idx):
#         img_path = self.image_paths[idx]
#         image = Image.open(img_path).convert("RGB")
#         if self.transform:
#             image = self.transform(image)
#         return image, img_path

# def parse_args():
#     parser = argparse.ArgumentParser(description="Batch Inference Script")
#     parser.add_argument('--batch_size', type=int, required=True, help="Batch size for inference")
#     parser.add_argument('--output', type=str, required=True, help="Output path")
#     parser.add_argument('--start', type=float, default=0.0,
#                         help="Start percentage of dataset (0.0 - 1.0)")
#     parser.add_argument('--end', type=float, default=1.0,
#                         help="End percentage of dataset (0.0 - 1.0)")
#     return parser.parse_args()

def main():
    # args = parse_args()
    # if not (0.0 <= args.start < args.end <= 1.0):
    #     raise ValueError(
    #         "Start and end percentages must be in range 0.0 - 1.0 and start < end")

    # model = models.resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)
    # model.eval()

    # transform = transforms.Compose([
    #     transforms.Resize(256),
    #     transforms.CenterCrop(224),
    #     transforms.ToTensor(),
    #     transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    # ])

    # dataset = datasets.CIFAR10(root="./data", train=False, download=True, transform=transform)
    # total_size = len(dataset)
    # start_idx = int(total_size * args.start)
    # end_idx = int(total_size * args.end)

    # subset_dataset = Subset(dataset, range(start_idx, end_idx))
    # dataloader = DataLoader(subset_dataset, batch_size=args.batch_size, shuffle=False)

    # results = []
    # with torch.no_grad():
    #     for batch_idx, (batch_images, labels) in enumerate(dataloader):
    #         outputs = model(batch_images)
    #         predictions = torch.argmax(outputs, dim=1)
    #         results.extend(zip(range(start_idx + batch_idx * args.batch_size,
    #                                  start_idx + batch_idx * args.batch_size + len(
    #                                      predictions)), predictions.numpy()))

    # with open(f"{args.output}.csv", mode='w', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerow(["Index", "Predicted_Class"])
    #     writer.writerows(results)

    # print(f"Inference results saved to: {args.output}.csv")

    url = " https://196a-67-243-144-239.ngrok-free.app/submit_file"  # Replace with your scheduler IP/port
    data = {"num1": 10}  # Just some JSON payload
    response = requests.post(url, json=data)
    print("POST Status Code:", response.status_code)
    print("Response Body:", response.text)

    
    print("Response {}".format(response))


if __name__ == "__main__":
    main()