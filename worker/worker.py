import grpc
from concurrent import futures
from gcs import download_blob
import scheduler_pb2
import scheduler_pb2_grpc
import time
import os
import shutil
import subprocess

SCHEDULER_ADDRESS = os.getenv("SCHEDULER_ADDRESS", "192.168.119.1:50052") 
registry_name = ""
repo_name = "sunchaser"

def do_task(request):
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists(f'data/{request.dataset}'):
        if os.listdir('data'):
            shutil.rmtree('data')
            os.makedirs('data')
        download_blob("sun-chaser-gcs", request.dataset, f'data/{request.dataset}')
    docker_img_path = f'{registry_name}/{repo_name}:{request.id}'
    try:
        subprocess.run(f"docker pull {docker_img_path}", shell=True, check=True)

        command = f"docker run --rm {docker_img_path} --batch {request.batch} --dataset {request.dataset} 
                --start {request.start} --end {request.end} 
                --partitioned {request.partitioned} --output outputfile_{request.id}"
        subprocess.run(command, shell=True, check=True)
        return 1
    except subprocess.CalledProcessError as e:
        return 0
    
    
class WorkerService(scheduler_pb2_grpc.SchedulerServiceServicer):
    def ProcessTask(self, request, context):
        """
        Receives and processes a task from the scheduler.
        """
        begin = time.time()
        do_task(request)
        end = time.time()

        report_status_to_scheduler(worker_name="worker-node", task_id=request.id, status="completed")

        return scheduler_pb2.TaskResponse(
            message=f"Task {request.id} processed successfully.",
            success=True
        )

def report_status_to_scheduler(worker_name, task_id, status):
    """
    Worker reports task status to the scheduler.
    """
    try:
        channel = grpc.insecure_channel(SCHEDULER_ADDRESS)
        stub = scheduler_pb2_grpc.SchedulerServiceStub(channel)

        request = scheduler_pb2.StatusRequest(
            worker_name=worker_name,
            id=task_id,
            status=status,
            runtime_info={"cpu_usage": "25%", "memory": "1.5GB"}  # Example stats
        )

        response = stub.ReportStatus(request)
        print(f"Scheduler Response: {response.message}")

    except grpc.RpcError as e:
        print(f"gRPC Error: {e.details()}")

def run_worker():
    """
    Starts the gRPC server for the worker.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    scheduler_pb2_grpc.add_SchedulerServiceServicer_to_server(WorkerService(), server)

    worker_address = "[::]:50051"  # Bind to all interfaces
    server.add_insecure_port(worker_address)

    print(f"Worker gRPC server running on {worker_address}...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    run_worker()
