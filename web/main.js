import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

function createInputModal() {
  return new Promise((resolve) => {
    const modal = document.createElement("div");
    modal.style.cssText = `
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: #1a1a1a;
      padding: 20px;
      border-radius: 8px;
      z-index: 1000;
      min-width: 300px;
    `;

    const title = document.createElement("h3");
    title.textContent = "Package Worlflow";
    title.style.cssText = `
      margin-bottom: 15px;
      color: #fff;
    `;

    const input = document.createElement("input");
    input.type = "text";
    input.value = "package";
    input.style.cssText = `
      width: 100%;
      padding: 8px;
      margin-bottom: 15px;
      background: #333;
      border: 1px solid #444;
      border-radius: 4px;
      color: #fff;
      box-sizing: border-box;
    `;

    const buttonContainer = document.createElement("div");
    buttonContainer.style.cssText = `
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    `;

    const confirmButton = document.createElement("button");
    confirmButton.textContent = "Confirm";
    confirmButton.style.cssText = `
      padding: 6px 12px;
      background: #00a67d;
      border: none;
      border-radius: 4px;
      color: white;
      cursor: pointer;
    `;

    const cancelButton = document.createElement("button");
    cancelButton.textContent = "Cancel";
    cancelButton.style.cssText = `
      padding: 6px 12px;
      background: #666;
      border: none;
      border-radius: 4px;
      color: white;
      cursor: pointer;
    `;

    const overlay = document.createElement("div");
    overlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      z-index: 999;
    `;

    buttonContainer.appendChild(cancelButton);
    buttonContainer.appendChild(confirmButton);
    modal.appendChild(title);
    modal.appendChild(input);
    modal.appendChild(buttonContainer);
    document.body.appendChild(overlay);
    document.body.appendChild(modal);

    const cleanup = () => {
      modal.remove();
      overlay.remove();
    };

    confirmButton.onclick = () => {
      const filename = input.value.trim();
      if (filename) {
        cleanup();
        resolve(filename);
      }
    };

    cancelButton.onclick = () => {
      cleanup();
      resolve(null);
    };

    input.addEventListener("keyup", (e) => {
      if (e.key === "Enter") {
        confirmButton.click();
      }
    });

    input.select();
  });
}

function createDownloadModal() {
  const modal = document.createElement("div");
  modal.style.cssText = `
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: #1a1a1a;
    padding: 20px;
    border-radius: 8px;
    z-index: 1000;
    min-width: 300px;
  `;

  const title = document.createElement("h3");
  title.textContent = "Packaging...";
  title.style.marginBottom = "15px";
  title.style.color = "#fff";

  const progress = document.createElement("div");
  progress.style.cssText = `
    width: 100%;
    height: 20px;
    background: #333;
    border-radius: 10px;
    overflow: hidden;
  `;

  const progressBar = document.createElement("div");
  progressBar.style.cssText = `
    width: 0%;
    height: 100%;
    background: #00a67d;
    transition: width 0.3s ease;
  `;

  progress.appendChild(progressBar);
  modal.appendChild(title);
  modal.appendChild(progress);

  const overlay = document.createElement("div");
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 999;
  `;

  document.body.appendChild(overlay);
  document.body.appendChild(modal);

  return {
    modal,
    overlay,
    progressBar,
    updateProgress: (percent) => {
      progressBar.style.width = `${percent}%`;
    },
    close: () => {
      modal.remove();
      overlay.remove();
    }
  };
}

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
      const filename = await createInputModal();
      if (!filename) return;
      
      packButton.disabled = true;
      const downloadModal = createDownloadModal();
      
      try {
        downloadModal.updateProgress(20);
        const { workflow, output: workflow_api } = await app.graphToPrompt();
        
        downloadModal.updateProgress(40);
        const body = JSON.stringify({ workflow, workflow_api });
        
        downloadModal.updateProgress(60);
        const resp = await api.fetchApi("/bentoml/pack", { method: "POST", body, headers: { "Content-Type": "application/json" } });
        
        downloadModal.updateProgress(80);
        const downloadUrl = (await resp.json())["download_url"];

        downloadModal.updateProgress(100);
        const link = document.createElement("a");
        link.href = downloadUrl;
        link.download = filename + ".cpack";
        link.click();

        setTimeout(() => {
          downloadModal.close();
        }, 1000);
      } catch (error) {
        console.error("Package failed:", error);
        downloadModal.close();
      } finally {
        packButton.disabled = false;
      }
    }
    menu.append(packButton);
  }
});
