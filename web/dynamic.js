import { app } from "../../scripts/app.js";

function mimicNode(node, target, slot) {
  const getWidget = (widget) => {
    if (typeof widget.origType === "undefined") return widget;
    const newWidget = Object.assign({}, widget);
    for (const key in widget) {
      if (key.startsWith("orig") || key === "computeSize") {
        delete newWidget[key];
      }
    }
    newWidget.type = widget.origType;
    newWidget.name = "input";
    return newWidget;
  }
  const input = target.inputs[slot];
  if (typeof input.widget === "undefined") {  // This is an input
    node.inputs = [input];
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
	async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "BentoInputDynamic") return;

    nodeType.prototype.onConnectOutput = function () {
      if (this.outputs[0].links?.length > 0) return false;
      const target = arguments[3];
      mimicNode(this, target, arguments[4]);
      this.title = target.inputs[arguments[4]].name;
    }
  },

  async setup(app) {
    app.graph.nodes.forEach((node) => {
      if (node.type !== "BentoInputDynamic") return;
      if (node.outputs.length > 0 && node.outputs[0].links.length > 0) {
        const link = node.graph.links[node.outputs[0].links[0]];
        mimicNode(node, app.graph.getNodeById(link.target_id), link.target_slot);
      }
    })
  }
});
