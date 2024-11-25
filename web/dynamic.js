import { app } from "../../scripts/app.js";

function mimicNode(node, target, slot) {
  const getWidget = (widget) => {
    if (typeof widget.origType === "undefined") return widget;
    const newWidget = Object.assign({}, widget);
    for (const key in widget) {
      if (key.startsWith("orig") || key === "computeSize" || key === "serializeValue") {
        delete newWidget[key];
      }
    }
    newWidget.type = widget.origType;
    newWidget.name = inputName;
    return newWidget;
  }
  const input = target.inputs[slot];
  const inputName = node.inputs.length > 0 ? node.inputs[0].name : node.widgets[0].name;
  if (typeof input.widget === "undefined") {  // This is an input
    node.inputs = [{ ...input, name: inputName }];
    node.widgets = [];
  } else {  // This is a widget
    node.widgets = [getWidget(target.widgets.find(w => w.name === input.name))];
    node.inputs = [];
    node.size = node.computeSize();
    requestAnimationFrame(() => {
      if (node.onResize) {
        node.onResize(node.size);
      }
    });
  }
}

app.registerExtension({
	name: "Comfy.DynamicInput",
  extensionNodes: ["CPackInputValue", "CPackInputFile"],

	async beforeRegisterNodeDef(nodeType, nodeData) {
    if (!this.extensionNodes.includes(nodeData.name)) return;

    nodeType.prototype.onConnectOutput = function () {
      if (this.outputs[0].links?.length > 0) return false;
      const target = arguments[3];
      if (this.type === "CPackInputFile" && !["COMBO", "STRING"].includes(target.inputs[arguments[4]].type))
        return false;
      mimicNode(this, target, arguments[4]);
      this.title = target.inputs[arguments[4]].name;
    }
  },

  async setup(app) {
    app.graph.nodes.forEach((node) => {
      if (!this.extensionNodes.includes(node.type)) return;
      if (node.outputs.length > 0 && node.outputs[0].links.length > 0) {
        const link = node.graph.links[node.outputs[0].links[0]];
        mimicNode(node, app.graph.getNodeById(link.target_id), link.target_slot);
      }
    })
  },

  async init(app) {
    const originalToPrompt = app.graphToPrompt;
    const self = this;
    app.graphToPrompt = async function(graph = app.graph, clean = true) {
      const { workflow, output } = await originalToPrompt(graph, clean);
      Object.entries(output).forEach(([id, nodeData]) => {
        if (!self.extensionNodes.includes(nodeData.class_type)) return;
        const node = graph.getNodeById(parseInt(id));
        if (node.widgets.length === 0) return;
        const widget = node.widgets[0];
        nodeData["_meta"] = Object.assign({}, nodeData["_meta"] || { title: node.title }, { options: widget.options });
      });
      return { workflow, output };
    };
  }
});
