# Comfy-Pack

A comprehensive toolkit for standardizing, packaging and deploying ComfyUI workflows as reproducible environments and production-ready REST services.

## Features
- **Package Everything**: Create reproducible `.cpack.zip` files containing your workflow, custom nodes, model versions, and all dependencies
- **Standardize Parameters**: Define and validate workflow inputs through UI nodes for images, text, numbers and more
- **CLI Support**: Restore environment and run inference from command line
- **REST API Generation**: Auto-convert any workflow into REST service with OpenAPI docs

## Quick Start

### Installation
```bash
pip install comfy-pack
```



### Create a Pack
1. Search&Install Comfy Pack custom nodes in ComfyUI with Manager
2. Design your workflow with comfy-pack input/output nodes
3. Click "Package" button to create `.cpack.zip`

### Restore to a ComfyUI project
```bash
# Restore environment from pack, will install everything needed except the models.
comfy-pack restore workflow.cpack.zip --dir ./
```

### Run Inference
```bash
# Get the workflow input spec
comfy-pack info workflow.cpack.zip

# Run
comfy-pack run workflow.cpack.zip --src-image image.png --video video.mp4
```

### Develop REST service
![serve](https://github.com/user-attachments/assets/57b5ff75-6109-4f06-99a2-778942030236)

## Parameter Nodes

ComfyPack provides custom nodes for standardizing inputs:
- ImageInput
- StringInput
- IntInput
- AnyInput
- ImageOutput
- FileOutput
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
