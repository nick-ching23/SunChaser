import threading
import subprocess
import time 
import grpc
from utils import PriorityQueue
from collections import defaultdict
import scheduler_pb2
import scheduler_pb2_grpc

task_lock = threading.Lock()
id_lock = threading.Lock()

workers = [{'name': "south_carolina", 
            'address': "34.138.214.204",
            'free': True}]
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
                prev_worker_id = (prev_worker_id + 1) % len(workers)
        time.sleep(10)