import argparse
import random

from fastapi import requests


def parse_args():
    parser = argparse.ArgumentParser(description="Batch Inference Script")
    parser.add_argument('--batch_size', type=int, required=True, help="Batch size for inference")
    parser.add_argument('--output', type=str, required=True, help="Output path")
    return parser.parse_args()

def main():
    args = parse_args()
    random_numbers = [random.randint(0, 100) for _ in range(args.batch_size)]
    with open(f"{args.output}.txt", 'w') as f:
        for number in random_numbers:
            f.write(f"{number}\n")
    print(f"Generated {args.batch_size} random numbers and saved to {args.output}")
    with open(f"{args.output}.csv", mode='rb') as file:
        url = "https://b830-67-243-137-85.ngrok-free.app/submit_file"
        files = {"output_file": file}
        response = requests.post(url, files=files)
        if response.status_code == 200:
            print("File uploaded successfully")
        else:
            print("Failed to upload file")

if __name__ == "__main__":
    main()