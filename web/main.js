import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
  name: "Comfy.BentoExtension",

  async setup() {
    const menu = document.querySelector(".comfy-menu");
    const separator = document.createElement("hr");

    separator.style.margin = "20px 0";
    separator.style.width = "100%";
    menu.append(separator);
    const packButton = document.createElement("button");
    packButton.textContent = "Package";
    packButton.onclick = async () => {
      packButton.disabled = true;
      try {
        const { workflow, output: workflow_api } = await app.graphToPrompt();
        const body = JSON.stringify({ workflow, workflow_api });
        const resp = await api.fetchApi("/bentoml/pack", { method: "POST", body, headers: { "Content-Type": "application/json" } });
        const downloadUrl = (await resp.json())["download_url"];
        const link = document.createElement("a");
        link.href = downloadUrl;
        link.download = "workspace.zip";
        link.click();
      } finally {
        packButton.disabled = false;
      }
    }
    menu.append(packButton);
  }
});
