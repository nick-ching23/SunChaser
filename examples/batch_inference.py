import requests
import time 
def main():
    time.sleep(2)
    url = " https://8912-67-243-137-85.ngrok-free.app/submit_file"  # Replace with your scheduler IP/port
    data = {"num1": 10}  # Just some JSON payload
    response = requests.post(url, json=data)
    print("POST Status Code:", response.status_code)
    print("Response Body:", response.text)
    print("Response {}".format(response))
    time.sleep(2)

if __name__ == "__main__":
    main()