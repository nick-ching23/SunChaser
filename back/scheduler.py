from flask import Flask, request, jsonify
from utils import Task
import scheduling_utils
import time
import threading
import random 
import subprocess
import os
import shutil

app = Flask(__name__)

start_and_end_times = {}
remaining_batches_per_task = {}
ids = set()

docker_lock = threading.Lock()
file_lock = threading.Lock()

def load_and_push_docker_image(tar_path, image_tag):
    try:
        load_output = subprocess.run(["docker", "load", "-i", tar_path], check=True, capture_output=True, text=True)

        loaded_image = None
        for line in load_output.stdout.splitlines():
            if "Loaded image" in line:
                loaded_image = line.split(": ")[1].strip()
                break

        if not loaded_image:
            print("Failed to determine the loaded image name.")
            return False

        subprocess.run(["docker", "tag", loaded_image, image_tag], check=True)

        subprocess.run(["docker", "push", image_tag], check=True)

        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return False
    
@app.route('/submit_task', methods=['POST'])
def submit_task():
    """
    API to accept JSON configuration and a Dockerfile.
    """
    if 'dockerfile' not in request.files:
        return jsonify({"error": "Missing files. Please upload Dockerfile."}), 400

    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "Missing JSON configuration"}), 400
    
    docker_file = request.files['dockerfile']
    
    tar_path = os.path.join("/tmp", f"{docker_file.filename}")
    docker_file.save(tar_path)

    batch_size = json_data['batch_size']
    num_batches = json_data['num_batches']
    should_split = False

    with scheduling_utils.id_lock:
        id = random.randint(0, 99999999)
        while id in ids:
            id = random.randint(0, 99999999)
        ids.add(id)
        timestamp = time.time()
    image_tag = f"willma17/{id}:{id}"
    load_and_push_docker_image(tar_path, image_tag)
    with file_lock:
        remaining_batches_per_task[id] = num_batches
    with scheduling_utils.task_lock:
        for i in range(num_batches):
            if should_split:
                task = Task(id, batch_size, i, i / num_batches, (i + 1) / num_batches, True, timestamp)
            else:
                task = Task(id, batch_size, i, 0, 1, False, timestamp)
            scheduling_utils.unallocated_tasks.push(task)
    return jsonify({"message": "Task submitted", "task_id": task.id}), 202

    
@app.route('/submit_file', methods=['POST'])
def submit_file():
    end_time = time.time()
    output_file = request.files['output_file']
    filename = output_file.filename
    id, p_id, worker_id, _ = filename.split("_")
    time_diff = end_time - start_and_end_times[(int(id), int(p_id))] 
    #do something with this time_diff
    scheduling_utils.workers[worker_id]['free'] = True
    if not os.path.exists(f"{id}_output"):
        os.makedirs(f"{id}_output")
    with file_lock:
        remaining_batches_per_task[int(id)] -= 1
    output_file.save(f"{id}_output/{filename}")
    if remaining_batches_per_task[int(id)] == 0:
        with docker_lock:
            subprocess.run(["docker", "rmi", "-f", f"willma17/{id}:{id}"])
            #eventually want some code that cleans the dockerhub
        shutil.make_archive(f"{id}_output_archive", 'zip', f"{id}_output")
        #send this to the user 
        # shutil.rmtree(f"{id}_output")
        # os.remove(f"{id}_output_archive.zip")
    return jsonify({"message": "Got it!"}), 200

def run_flask():
    app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=False)

if __name__ == '__main__':
    task_dispatch_thread = threading.Thread(target=scheduling_utils.dispatch_tasks, daemon=True)
    task_dispatch_thread.start()
    schedule_thread = threading.Thread(target=scheduling_utils.schedule_tasks, daemon=True)
    schedule_thread.start()
    run_flask()