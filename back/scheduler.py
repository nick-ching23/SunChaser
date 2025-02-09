from flask import Flask, request, jsonify
from google.cloud import storage
from collections import defaultdict
from concurrent import futures
from gcs import upload_blob, delete_blob
import grpc
import scheduler_pb2
import scheduler_pb2_grpc
import json
import time
import threading
import heapq
import subprocess
import random 

app = Flask(__name__)

GCS_BUCKET_NAME = "sun-chaser-gcs"
workers = [{'name': "south_carolina", 
            'address': "104.196.151.216",
            'free': True}]
registry_name = ""
repo_name = "sunchaser"
registry_memory = {}
ids = set()

task_lock = threading.Lock()
id_lock = threading.Lock()
docker_lock = threading.Lock()
storage_client = storage.Client()

class SchedulerService(scheduler_pb2_grpc.SchedulerServiceServicer):
    def ReportStatus(self, request, context):
        #worker handling logic 
        return scheduler_pb2.StatusResponse(message="Status received")

def run_grpc_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    scheduler_pb2_grpc.add_SchedulerServiceServicer_to_server(SchedulerService(), server)

    server_address = "0.0.0.0:50052"  # Scheduler listens on port 50052 for gRPC
    server.add_insecure_port(server_address)

    server.start()
    server.wait_for_termination()

class Task:
    def __init__(self, id = "", batch = 0, dataset = None, start = 0, end = 0, partitioned = False, time = float('inf'), last = False):
        self.id = str(id)
        self.batch = batch
        self.dataset = dataset
        self.start = start
        self.end = end
        self.partitioned = partitioned
        self.time = time
        self.last = last
    
class PriorityQueue:
    def __init__(self):
        self.queue = []

    def push(self, task):
        heapq.heappush(self.queue, (task.time, task.start, task))

    def pop(self):
        if self.queue:
            return heapq.heappop(self.queue)[2]
        return None

    def __len__(self):
        return len(self.queue)

task_queues = defaultdict(PriorityQueue)
unallocated_tasks = PriorityQueue()

def run_command(command):
    """Run a shell command and handle errors."""
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"Command succeeded: {command}")
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}\nError: {e}")
        raise e
    
def send_task_to_worker(worker_address, task):
    """
    Sends a task to a worker using gRPC.
    """
    try:
        # Connect to gRPC server
        channel = grpc.insecure_channel(f"{worker_address}:50051")
        stub = scheduler_pb2_grpc.SchedulerServiceStub(channel)

        # Create task request
        request = scheduler_pb2.TaskRequest(
            id=task.id,
            batch=task.batch,
            dataset=task.dataset,
            start=task.start,
            end=task.end,
            partitioned=task.partitioned,
            time = task.time,
            last = task.last
        )

        # Send request
        response = stub.ProcessTask(request)
        print(f"Response from {worker_address}: {response.message}")

        return response.success
    except grpc.RpcError as e:
        print(f"gRPC Error: {e.details()}")
        return False
    
def dispatch_tasks():
    """
    Periodically assigns tasks to available workers.
    """
    while True:
        with task_lock:
            for worker_id in task_queues:
                if workers[worker_id]['free'] and len(task_queues[worker_id]) > 0:
                    task = task_queues[worker_id].pop(0)
                    success = send_task_to_worker(workers[worker_id]['address'], task)
                    if success:
                        workers[worker_id]['free'] = False
                        print(f"Task sent successfully to {workers[worker_id]['name']}")
                    else:
                        print(f"Failed to send task to {workers[worker_id]['name']}")
        time.sleep(10)

def schedule_tasks():
    #cyclic scheduling for now
    prev_worker_id = 0
    while True:
        with task_lock:
            while len(unallocated_tasks) > 0:
                task = unallocated_tasks.pop(0)
                task_queues[prev_worker_id].push(task)
                prev_working_id = (prev_worker_id + 1) % len(workers)
        time.sleep(10)

task_dispatch_thread = threading.Thread(target=dispatch_tasks, daemon=True)
task_dispatch_thread.start()
schedule_thread = threading.Thread(target=schedule_tasks, daemon=True)
schedule_thread.start()

def process_and_push_docker_image(docker_file, tag):
    """
    Processes a Docker .tar file, tags it, and pushes it to the specified registry.
    """
    try:
        process = subprocess.Popen(
            ["docker", "load"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate(input=docker_file.read())

        if process.returncode != 0:
            return {"error": f"Failed to load Docker image: {stderr.decode()}"}

        image_id = subprocess.check_output(
            "docker images -q | head -n 1", shell=True
        ).decode().strip()

        if not image_id:
            return {"error": "Failed to load Docker image from the tar file"}
        
        full_image_name = f"{registry_name}/{repo_name}:{tag}"
        subprocess.run(f"docker tag {image_id} {full_image_name}", shell=True, check=True)

        subprocess.run(f"docker push {full_image_name}", shell=True, check=True)

        registry_memory[tag] = full_image_name

        return {"message": "Docker image pushed successfully!", "image": full_image_name}

    except Exception as e:
        return {"error": f"Failed to process Docker image: {str(e)}"}
    
@app.route('/submit_task', methods=['POST'])
def submit_task():
    """
    API to accept JSON configuration and a Dockerfile.
    """
    if 'config' not in request.files or 'dockerfile' not in request.files:
        return jsonify({"error": "Missing files. Please upload both config.json and Dockerfile."}), 400

    config_file = request.files['config']
    docker_file = request.files['dockerfile']
    dataset_link = request.form['dataset_link']

    try:
        config_content = config_file.read().decode('utf-8')
        config_dict = json.loads(config_content)
        
        batch_size = config_dict['batch_size']
        num_executions = config_dict['num_executions']
        should_split = config_dict['should_split']
        
        num_tasks = num_executions // batch_size + 1
        cumulative_batch = 0
        with id_lock:
            id = random.randint(0, 99999999)
            while id in ids:
                id = random.randint(0, 99999999)
            ids.add(id)
            timestamp = time.time()
        with docker_lock:
            process_and_push_docker_image(docker_file, id)
        with task_lock:
            for i in range(num_tasks):
                curr_batch_size = min(batch_size, num_executions - i * batch_size) 
                if should_split:
                    task = Task(id, curr_batch_size, dataset_link, cumulative_batch / num_executions, (cumulative_batch + curr_batch_size) / num_executions, True, timestamp, i == num_tasks - 1)
                    cumulative_batch += curr_batch_size
                else:
                    task = Task(id, curr_batch_size, dataset_link, 0, 1, False, timestamp, i == num_tasks - 1)
                unallocated_tasks.push(task)
        return jsonify({"message": "Task submitted", "task_id": task.id}), 202
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 400
    
@app.route('/upload_dataset', methods=['POST'])
def upload_dataset():
    """
    API to upload a dataset to Google Cloud Storage.
    """
    if 'dataset' not in request.files:
        return jsonify({"error": "Missing dataset file"}), 400

    dataset_file = request.files['dataset']
    dataset_filename = dataset_file.filename

    try:
        upload_blob(GCS_BUCKET_NAME, dataset_filename, dataset_filename)
        return jsonify({"message": "Dataset uploaded successfully", "gcs_url" :f"gs://{GCS_BUCKET_NAME}/{dataset_filename}"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to upload dataset: {str(e)}"}), 500

def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

if __name__ == '__main__':
    grpc_thread = threading.Thread(target=run_grpc_server, daemon=True)
    grpc_thread.start()
    #test
    # task = Task()
    # send_task_to_worker("104.196.151.216", task)
    # run_flask()
    pass