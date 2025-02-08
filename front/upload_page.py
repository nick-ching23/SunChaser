import gradio as gr


def process_inputs(batch_size, num_batches, docker_image):
    if docker_image is None:
        return "Please upload a docker image"

    return f"batch size: {batch_size}, number of batches: {num_batches}, Uploaded Docker image: {docker_image.name}"


demo = gr.Interface(
    fn=process_inputs,
    inputs=[
        gr.Number(label="Batch Size", value=1, precision=0),
        gr.Number(label="Number of Batches", value=1, precision=0),
        gr.File(label="Upload your Docker Image", type="filepath")
    ],
    outputs=gr.Textbox(label="result")
)

if __name__ == "__main__":
    demo.launch()