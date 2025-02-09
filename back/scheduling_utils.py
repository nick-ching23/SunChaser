import threading
import subprocess
import time 
from utils import PriorityQueue
from collections import defaultdict
import scheduler

task_lock = threading.Lock()
id_lock = threading.Lock()

workers = [{'name': "south_carolina", 
            'context': "gke_sunchaser-450121_us-east1-b_sun-chaser-south-carolina",
            'free': True}, 
            {'name': "texas", 
            'context': "gke_sunchaser-450121_us-south1-a_sun-chaser-texas",
            'free': True}, 
            {'name': "oregon", 
            'context': "gke_sunchaser-450121_us-west1-a_sun-chaser-oregon",
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
    
def send_task_to_worker(worker_id, task):
    cluster_switch = ["kubectl", "config", "use-context" , workers[worker_id]['context']]
    run_command(cluster_switch)
    command = ["kubectl", "create", "job", "worker-job", f"--image=willma17/{task.id}:{task.id}", 
               "--", "--batch_size", str(task.batch), "--output", f"{task.id}_", "--pid", str(task.p_id),
               "--worker", str(worker_id)]
    run_command(command)
    scheduler.start_and_end_times[(task.id, task.p_id)] = time.time()
    
def dispatch_tasks():
    """
    Periodically assigns tasks to available workers.
    """
    while True:
        with task_lock:
            for worker_id in task_queues:
                if workers[worker_id]['free'] and len(task_queues[worker_id]) > 0:
                    task = task_queues[worker_id].pop()
                    success = send_task_to_worker(worker_id, task)
                    if success:
                        workers[worker_id]['free'] = False
                        print(f"Task sent successfully to {workers[worker_id]['name']}")
                    else:
                        print(f"Failed to send task to {workers[worker_id]['name']}")
        time.sleep(2)

def schedule_tasks():
    #cyclic scheduling for now
    prev_worker_id = 0
    while True:
        with task_lock:
            while len(unallocated_tasks) > 0:
                task = unallocated_tasks.pop()
                task_queues[prev_worker_id].push(task)
                prev_worker_id = (prev_worker_id + 1) % len(workers)
        time.sleep(2)