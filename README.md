# Comfy-Pack

A comprehensive toolkit for standardizing, packaging and deploying ComfyUI workflows as reproducible environments and production-ready REST services.

## Features
- **Package Everything**: Create reproducible `.cpack.zip` files containing your workflow, custom nodes, model versions, and all dependencies
- **Standardize Parameters**: Define and validate workflow inputs through UI nodes for images, text, numbers and more
- **CLI Support**: Restore environment and run inference from command line
- **REST API Generation**: Auto-convert any workflow into REST service with OpenAPI docs

## Quick Start

### Installation

<details>
<summary>Search `comfy-pack` in ComfyUI Manager (Recommended)</summary>

![install_node](https://github.com/user-attachments/assets/dbfb730d-edff-4a52-b6c4-695e3ec70368)

</details>

or

```bash
git clone https://github.com/bentoml/comfy-pack.git
```


### Package ComfyUI workspace
1. Click "Package" button to create `.cpack.zip`
2. (Optional) select the models that you want to include (only model hash will be recorded)



### Unpack ComfyUI project
```bash
# Restore a ComfyUI project from cpack files.
comfy-pack unpack workflow.cpack.zip --dir ./
```



### Develop REST service
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
