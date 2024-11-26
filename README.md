# ComfyPack

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
1. Install ComfyPack custom nodes in ComfyUI
2. Design your workflow with parameter nodes
3. Click "Package" button to create `.cpack.zip`

### Deploy as Service
```bash
# Restore environment from pack
comfy-pack restore workflow.cpack.zip

# Run as REST service
comfy-pack serve workflow.cpack.zip
```

### Run Inference
```bash
# CLI inference
comfy-pack run workflow.cpack.zip \
  --input_image path/to/img.png \
  --prompt "your prompt" \
  --seed 42

# REST API call
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"input_image": "base64...", "prompt": "your prompt", "seed": 42}'
```

## Parameter Nodes

ComfyPack provides custom nodes for standardizing inputs:
- ImageParameter
- TextParameter  
- NumberParameter
- SelectParameter
- ...

These nodes help define clear interfaces for your workflow.

## Docker Support

```bash
# Build image with pack
docker build -t myapp --build-arg PACK=workflow.cpack.zip .

# Run container
docker run -p 8000:8000 myapp
```

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

For detailed documentation, visit [docs.comfypack.ai](https://docs.comfypack.ai)
