from flask import Flask, request, jsonify
from utils import Task
from docker_utils import delete_image, process_and_push_docker_image
from concurrent import futures
import os 
import scheduling_utils
import grpc
import scheduler_pb2
import scheduler_pb2_grpc
import json
import time
import threading
import shutil 
import random 

app = Flask(__name__)

remaining_batches_per_task = {}
registry_name = "sunchaser-450121"
repo_name = "sun-chaser-docker-repo"
registry_memory = {}
ids = set()

docker_lock = threading.Lock()
file_lock = threading.Lock()

class SchedulerService(scheduler_pb2_grpc.SchedulerServiceServicer):
    def ReportStatus(self, request, context):
        if not request.status:
            print("Error: task not successfully completed")
        else:
            time_diff = request.end_time - request.begin_time
            #do something with this information 
        return scheduler_pb2.StatusResponse(message="Status received")

def run_grpc_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    scheduler_pb2_grpc.add_SchedulerServiceServicer_to_server(SchedulerService(), server)

    server_address = "0.0.0.0:50052"  # Scheduler listens on port 50052 for gRPC
    server.add_insecure_port(server_address)

    server.start()
    server.wait_for_termination()


task_dispatch_thread = threading.Thread(target=scheduling_utils.dispatch_tasks, daemon=True)
task_dispatch_thread.start()
schedule_thread = threading.Thread(target=scheduling_utils.schedule_tasks, daemon=True)
schedule_thread.start()

    
@app.route('/submit_task', methods=['POST'])
def submit_task():
    """
    API to accept JSON configuration and a Dockerfile.
    """
    if 'config' not in request.files or 'dockerfile' not in request.files:
        return jsonify({"error": "Missing files. Please upload both config.json and Dockerfile."}), 400

    config_file = request.files['config']
    docker_file = request.files['dockerfile']

    try:
        config_content = config_file.read().decode('utf-8')
        config_dict = json.loads(config_content)
        
        batch_size = config_dict['batch_size']
        num_batches = config_dict['num_batches']
        should_split = config_dict['should_split']
        
        with scheduling_utils.id_lock:
            id = random.randint(0, 99999999)
            while id in ids:
                id = random.randint(0, 99999999)
            ids.add(id)
            timestamp = time.time()
        with docker_lock:
            process_and_push_docker_image(docker_file, id, registry_memory)
        with file_lock:
            remaining_batches_per_task[id] = num_batches
        with scheduling_utils.task_lock:
            for i in range(num_batches):
                if should_split:
                    task = Task(id, batch_size, i / num_batches, (i + 1) / num_batches, True, timestamp)
                else:
                    task = Task(id, batch_size, 0, 1, False, timestamp)
                scheduling_utils.unallocated_tasks.push(task)
        return jsonify({"message": "Task submitted", "task_id": task.id}), 202
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 400


    
@app.route('/submit_file', methods=['POST'])
def submit_file():
    output_file = request.files['output_file']
    filename = output_file.filename
    id, start, end, extension = filename.split("_")
    if not os.path.exists(f"{id}_output"):
        os.makedirs(f"{id}_output")
    with file_lock:
        remaining_batches_per_task[int(id)] -= 1
    output_file.save(f"{id}_output/{filename}")
    if remaining_batches_per_task[int(id)] == 0:
        with docker_lock:
            delete_image(registry_memory[int(id)])
            del registry_memory[int(id)]
        shutil.make_archive(f"{id}_output_archive", 'zip', f"{id}_output")
        #send this to the user 
        shutil.rmtree(f"{id}_output")
        os.remove(f"{id}_output_archive.zip")

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