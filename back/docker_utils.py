import subprocess
import json

registry_name = "sunchaser-450121"
repo_name = "sun-chaser-docker-repo"
def get_image_digest(image_name):
    """
    Retrieves the digest for a given image.
    """
    try:
        result = subprocess.run(
            f"gcloud artifacts docker images list {registry_name}/{repo_name} --format=json",
            shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        images = json.loads(result.stdout)
        
        for image in images:
            if image["name"].endswith(image_name):
                return image["digest"]
        
        return None
    except subprocess.CalledProcessError as e:
        print(f"Failed to retrieve image digest: {e}")
        return None

def delete_image(image_name):
    """
    Deletes an image from Google Artifact Registry.
    """
    digest = get_image_digest(image_name)
    if not digest:
        print(f"Image {image_name} not found.")
        return
    
    print(f"Deleting image {image_name} with digest {digest}...")
    subprocess.run(
        f"gcloud artifacts docker images delete {registry_name}/{repo_name}/{image_name}@{digest} --quiet",
        shell=True, check=True
    )
    print(f"Image {image_name} deleted successfully.")

def process_and_push_docker_image(docker_file, tag, registry_memory):
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
