


# Comfy-Pack: Package and Deploy ComfyUI Workflows
<img width="870" alt="banner" src="https://github.com/user-attachments/assets/0658e8cc-8d6b-428e-bade-c72264982a24" />


A comprehensive toolkit for reliably packing and unpacking environments for ComfyUI workflows. 


- 📦 **Pack workflow environments as artifacts:** Saves the workflow environment in a `.cpack.zip` artifact with Python package versions, ComfyUI and custom node revisions, and model hashes.
- ✨ **Unpack artifacts to recreate workflow environments:** Unpacks the `.cpack.zip` artifact to recreate the same environment with the exact Python package versions, ComfyUI and custom node revisions, and model weights.
- 🚀 **Deploy workflows as APIs:** Deploys the workflow as a RESTful API with customizable input and output parameters.

## Motivations

We learned from our community that packaging and sharing a ComfyUI workflow is currently difficult due to challenges in reliably replicating the workflow environment. To reliably replicate a workflow elsewhere, one must recreate the environment with the exact python packages, custom nodes revisions, and the identical models. This process can be tedious, error-prone, and time-consuming.

To address this, we built comfy-pack – a tool designed to simplify this process. As a ComfyUI Manager plugin, comfy-pack lets you package an entire workflow with just one click in the UI. Behind the scenes, it automatically locks and records everything you need: Python package versions, custom node revisions, model hashes, and any static assets required for the workflow. All of this is saved into a single `.cpack.zip` artifact.

The same environment can be recreated by unpacking the `.cpack.zip` artifact with a simple command:

```bash
comfy-pack unpack workflow.cpack.zip
```

Once this command completes, the environment is fully set up to reliably reproduce the original workflow.

## Quick Start

### Installation

Search `comfy-pack` in ComfyUI Manager (Recommended)

![install_node](https://github.com/user-attachments/assets/dbfb730d-edff-4a52-b6c4-695e3ec70368)

or install from Git:

```bash
git clone https://github.com/bentoml/comfy-pack.git
```


### Pack a ComfyUI workflow
1. Click "Package" button to create `.cpack.zip`
2. (Optional) select the models that you want to include (only model hash will be recorded)



### Unpack a ComfyUI workflow
```bash
# Restore a ComfyUI project from cpack files.
comfy-pack unpack workflow.cpack.zip --dir ./
```



### Deploy a workflow as an API
<details>
<summary> 1. annotate input & output </summary>
  
![input](https://github.com/user-attachments/assets/44264007-0ac8-4e23-8dc0-e60aa0ebcea2)

![output](https://github.com/user-attachments/assets/a4526661-8930-4575-bacc-33b6887f6271)
</details>

<details>
<summary> 2. serve and test locally </summary>
  
![serve](https://github.com/user-attachments/assets/8d4c92c5-d6d7-485e-bc71-e4fc0fe8bf35)
</details>

<details>
<summary> 3. (Optional) pack & run anywhere </summary>
  
```bash
# Get the workflow input spec
comfy-pack run workflow.cpack.zip --help

# Run
comfy-pack run workflow.cpack.zip --src-image image.png --video video.mp4
```
</details>

<details> 
<summary> 4. (Optional) deploy to cloud * </summary>

![image](https://github.com/user-attachments/assets/1ffa31fc-1f50-4ea7-a47e-7dae3b874273)


</details>



## Parameter Nodes

ComfyPack provides custom nodes for standardizing inputs:
- ImageInput: provides `image` type input, similar to official `LoadImage` node
- StringInput: provides `string` type input, nice for prompts
- IntInput: provides `int` type input, suitable for size or seeds
- AnyInput: provides `combo` type and more input, suitable for custom nodes
- ImageOutput: takes `image` type inputs, similar to official `SaveImage` node, take an image of a bunch of images
- FileOutput: takes file path as `string` type, save and output the file under that path
- ...

These nodes help define clear interfaces for your workflow.

## Docker Support
Under development


## Examples

Check our [examples folder](examples/) for:
- Basic workflow packaging
- Parameter configuration
- API integration
- Docker deployment

## License
MIT License

## Community
- Issues & Feature Requests: GitHub Issues
- Questions & Discussion: Discord Server

Detailed documentation: under development
