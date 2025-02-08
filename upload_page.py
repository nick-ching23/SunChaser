import gradio as gr
from gcs import upload_blob, download_blob

def process_inputs(batch_size, num_batches, docker_image, dataset):
    if docker_image is None:
        return "Please upload a docker image"
    upload_to_gcs(dataset)
    return f"batch size: {batch_size}, number of batches: {num_batches}, Uploaded Docker image: {docker_image.name}"

def upload_to_gcs(dataset):
    bucket_name = "sun-chaser-gcs"
    dataset_name = dataset.name.split("/")[-1]
    source_file_name = dataset.name
    destination_blob_name = f"dataset/{dataset_name}"
    upload_blob(bucket_name, source_file_name, destination_blob_name)

demo = gr.Interface(
    fn=process_inputs,
    inputs=[
        gr.Number(label="Batch Size", value=1, precision=0),
        gr.Number(label="Number of Batches", value=1, precision=0),
        gr.File(label="Upload your Docker Image", type="filepath"),
        gr.File(label="Dateset", type="filepath")
    ],
    outputs=gr.Textbox(label="result")
)

if __name__ == "__main__":
    demo.launch()
