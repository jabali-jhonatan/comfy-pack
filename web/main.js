import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const style = `
.cpack-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: #1a1a1a;
  padding: 20px;
  border-radius: 8px;
  z-index: 1000;
  color: white;
  min-width: 360px;
}

.cpack-input {
  width: 100%;
  padding: 8px;
  background: #333;
  border: 1px solid #444;
  border-radius: 4px;
  color: white;
  box-sizing: border-box;
}

.cpack-btn {
  padding: 6px 12px;
  background: #666;
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
}

.cpack-btn.primary {
  background: #00a67d;
}

.cpack-btn-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.cpack-title {
  margin-bottom: 15px;
  font-size: 1.3em;
  font-weight: bold;
}

.cpack-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
}

.cpack-input-row {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 5px;
}

.cpack-form-item {
  margin-bottom: 15px;
}

.cpack-form-item label {
  margin-bottom: 5px;
}

#build-info {
  display: flex;
  padding: 10px;
  flex-direction: column;
  align-items: center;
}

#build-error {
  display: none;
  color: #ff8383;
  text-wrap: auto;
  overflow-x: auto;
  background: #333;
  padding: 10px;
}

.cpack-copyable {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 5px;
}

.cpack-copyable > span {
  border: 1px solid #ccc;
  padding: 3px 10px;
  border-radius: 3px;
  background: #606060;
}
`

function createModal(modal) {
  const overlay = document.createElement("div");
  overlay.className = "cpack-overlay";

  document.body.appendChild(overlay);
  document.body.appendChild(modal);

  return {
    close: () => {
      modal.remove();
      overlay.remove();
    }
  };
}

function createInputModal() {
  return new Promise((resolve) => {
    const modal = document.createElement("div");
    modal.className = "cpack-modal";
    modal.id = "input-modal";

    const title = document.createElement("div");
    title.textContent = "Package Worlflow";
    title.className = "cpack-title";

    const input = document.createElement("input");
    input.type = "text";
    input.value = "package";
    input.className = "cpack-input";

    const buttonContainer = document.createElement("div");
    buttonContainer.className = "cpack-btn-container";

    const confirmButton = document.createElement("button");
    confirmButton.textContent = "Confirm";
    confirmButton.className = "cpack-btn primary";

    const cancelButton = document.createElement("button");
    cancelButton.textContent = "Cancel";
    cancelButton.className = "cpack-btn";

    buttonContainer.appendChild(cancelButton);
    buttonContainer.appendChild(confirmButton);
    modal.appendChild(title);
    modal.appendChild(input);
    modal.appendChild(buttonContainer);

    const { close } = createModal(modal);

    confirmButton.onclick = () => {
      const filename = input.value.trim();
      if (filename) {
        close();
        resolve(filename);
      }
    };

    cancelButton.onclick = () => {
      close();
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
  modal.className = "cpack-modal";
  modal.id = "download-modal";

  const title = document.createElement("div");
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

  const { close } = createModal(modal);

  return {
    updateProgress: (percent) => {
      progressBar.style.width = `${percent}%`;
    },
    close
  };
}

async function downloadPackage() {
  if (document.getElementById("input-modal")) return;
  if (document.getElementById("download-modal")) return;
  const filename = await createInputModal();
  if (!filename) return;

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
    link.download = filename + ".cpack.zip";
    link.click();

    setTimeout(() => {
      downloadModal.close();
    }, 1000);
  } catch (error) {
    console.error("Package failed:", error);
    downloadModal.close();
  }
}

async function serveBento() {
  if (document.getElementById("serve-modal")) return;
  const modal = document.createElement("div");
  modal.id = "serve-modal";
  modal.className = "cpack-modal";
  modal.style.width = "400px";

  const title = document.createElement("div");
  title.textContent = "Serve Workflow as REST API";
  title.className = "cpack-title";

  const form = document.createElement("form");
  form.innerHTML = serveForm;

  const buttonContainer = document.createElement("div");
  buttonContainer.className = "cpack-btn-container";

  const confirmButton = document.createElement("button");
  confirmButton.textContent = "Start";
  confirmButton.className = "cpack-btn primary";

  const cancelButton = document.createElement("button");
  cancelButton.textContent = "Cancel";
  cancelButton.className = "cpack-btn";

  buttonContainer.appendChild(cancelButton);
  buttonContainer.appendChild(confirmButton);

  modal.appendChild(title);
  modal.appendChild(form);
  modal.appendChild(buttonContainer);

  const { close } = createModal(modal);
  cancelButton.onclick = close;

  form.querySelector("input[name='port']").select();
  confirmButton.onclick = async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const { workflow, output: workflow_api } = await app.graphToPrompt();
    const data = {
      host: formData.get("allowExternal") === "on" ? "0.0.0.0" : "localhost",
      port: formData.get("port"),
      workflow,
      workflow_api
    };

    try {
      confirmButton.disabled = true;
      const resp = await api.fetchApi("/bentoml/serve", {
        method: "POST",
        body: JSON.stringify(data),
        headers: { "Content-Type": "application/json" }
      });
      const result = await resp.json();
      if (result.error) {
        const errorDiv = form.querySelector('.error-message');
        errorDiv.textContent = result.error;
        errorDiv.style.display = 'block';
      } else {
        close();
        createServeStatusModal(result.url);
      }
    } catch(e) {
      const errorDiv = form.querySelector('.error-message');
      errorDiv.textContent = e.message;
      errorDiv.style.display = 'block';
    } finally {
      confirmButton.disabled = false;
    }
  };
}

async function buildBento() {
  if (document.getElementById("build-modal")) return;
  if (document.getElementById("building-modal")) return;
  const data = await createBuildModal();
  console.log(data);
  await createBuildingModal(data);
};

const serveForm = `
<div class="cpack-form-item">
  <label>
    <input type="checkbox" name="allowExternal" />
    Allow External Access
  </label>
</div>
<div class="cpack-form-item">
  <label for="port">Port</label>
  <input type="number" class="cpack-input" name="port" value="3000" />
  <div class="error-message" style="color: #ff8383; margin-top: 5px; display: none"></div>
</div>
`

const buildForm = `
  <p style="font-size: 0.85em; color: #888; margin-top: 5px;">
    This feature is powered by <a href="https://www.bentoml.com/?from=comfy-pack" target="_blank" style="color: #00a67d;">BentoCloud</a>, our managed cloud platform.
  </p>
<div class="cpack-form-item">
  <label for="bentoName">Service Name</label>
  <input type="text" class="cpack-input" name="bentoName" value="comfy-pack" />
</div>
<div class="cpack-form-item">
  <label for="systemPackages">System Packages</label>
  <div id="system-packages-array">
    <button class="cpack-btn" id="add-button" style="margin: 5px 0px">Add</button>
  </div>
</div>
<div id="credentials-group">
  <div class="cpack-form-item">
    <label for="bentoName">BentoCloud Endpoint</label>
    <input type="text" class="cpack-input" name="endpoint" placeholder="https://<your_org>.cloud.bentoml.com" />
  </div>
  <div class="cpack-form-item">
    <label for="bentoName">BentoCloud API Key</label>
    <input type="password" class="cpack-input" name="apiKey" />
    <p style="font-size: 0.85em; color: #888; margin-top: 5px;">
      Get your API credentials at <a href="https://cloud.bentoml.com/signup?from=comfy-pack" target="_blank" style="color: #00a67d;">cloud.bentoml.com</a>
    </p>
  </div>
</div>
`

function createBuildModal() {
  const modal = document.createElement("div");
  modal.id = "build-modal";
  modal.className = "cpack-modal";
  modal.style.width = "400px";

  const title = document.createElement("div");
  title.textContent = "Deploy Workflow to Cloud";
  title.className = "cpack-title";

  const form = document.createElement("form");
  form.innerHTML = buildForm;

  const addButton = form.querySelector("#add-button");
  const systemPackagesArray = form.querySelector("#system-packages-array");
  addButton.addEventListener("click", (e) => {
    e.preventDefault();
    const row = document.createElement("div");
    row.className = "cpack-input-row";
    row.innerHTML = `
      <div style="flex: 1"><input type="text" class="cpack-input" name="systemPackages" /></div>
      <button class="cpack-btn" style="margin-left: 10px">Remove</button>
    `
    systemPackagesArray.appendChild(row);
    row.querySelector("button").onclick = (e) => {
      e.preventDefault();
      row.remove();
    }
  });

  
  const buttonContainer = document.createElement("div");
  buttonContainer.className = "cpack-btn-container";

  const confirmButton = document.createElement("button");
  confirmButton.textContent = "Push";
  confirmButton.className = "cpack-btn primary";

  const cancelButton = document.createElement("button");
  cancelButton.textContent = "Cancel";
  cancelButton.className = "cpack-btn";

  buttonContainer.appendChild(cancelButton);
  buttonContainer.appendChild(confirmButton);

  modal.appendChild(title);
  modal.appendChild(form);
  modal.appendChild(buttonContainer);

  const { close } = createModal(modal);
  cancelButton.onclick = close;
  return new Promise((resolve) => {
    form.querySelector("input[name='bentoName']").select();
    confirmButton.onclick = async (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      const { workflow, output: workflow_api } = await app.graphToPrompt();
      const data = {
        bento_name: formData.get("bentoName"),
        system_packages: Array.from(formData.getAll("systemPackages").filter(Boolean)),
        push: true,
        api_key: formData.get("apiKey"),
        endpoint: formData.get("endpoint"),
        workflow,
        workflow_api
      };
      close();
      resolve(data);
    }
  });
}

async function createServeStatusModal(url) {
  const modal = document.createElement("div");
  modal.className = "cpack-modal";
  modal.style.width = "400px";

  const title = document.createElement("div");
  title.textContent = "Serve Workflow as REST API";
  title.className = "cpack-title";

  const info = document.createElement("div");
  const urlObj = new URL(url);
  const currentHost = window.location.hostname;
  const port = urlObj.port;
  const displayUrl = `${currentHost}:${port}`;
  info.innerHTML = `
    <div style="margin-bottom: 15px">
      <div style="text-align: center; margin-bottom: 15px; color: #00a67d">
        🎉 Service is online! Click below to open:
      </div>
      <div style="text-align: center; margin-top: 15px">
        <a href="http://${displayUrl}" target="_blank" style="color:#00a67d;text-decoration:none;font-weight:bold;font-size:1.2em">
          ${displayUrl}
          <span style="color:#00a67d;font-size:1em">↗</span>
        </a>
      </div>
    </div>
    <div id="status-info" style="display:flex;justify-content:center;align-items:center">
      ${spinner}
    </div>
  `;

  const buttonContainer = document.createElement("div");
  buttonContainer.className = "cpack-btn-container";

  const cancelButton = document.createElement("button");
  cancelButton.textContent = "Stop Server";
  cancelButton.className = "cpack-btn";
  cancelButton.style.cssText = "background: #a63d3d; color: white; font-weight: bold";

  buttonContainer.appendChild(cancelButton);

  modal.appendChild(title);
  modal.appendChild(info);
  modal.appendChild(buttonContainer);

  const { close } = createModal(modal);
  
  

  cancelButton.onclick = async () => {
    try {
      await api.fetchApi("/bentoml/serve/terminate", { method: "POST" });
    } catch(e) {
      console.error("Failed to stop server:", e);
    }
    clearInterval(checkInterval);
    close();
  };

  const statusInfo = info.querySelector("#status-info");
  
  // Start status checking
  const checkInterval = setInterval(async () => {
    try {
      const resp = await api.fetchApi("/bentoml/serve/heartbeat", { method: "POST" });
      const status = await resp.json();
      if (status.error) {
        title.textContent = "Server Error";
        statusInfo.innerHTML = `<div style="color:#ff8383">${status.error}</div>`;
        clearInterval(checkInterval);
      }
    } catch(e) {
      title.textContent = "Status Check Error";
      statusInfo.innerHTML = `<div style="color:#ff8383">${e.message}</div>`;
      clearInterval(checkInterval);
    }
  }, 1000);
}

const spinner = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24">
  <path fill="currentColor" d="M12,1A11,11,0,1,0,23,12,11,11,0,0,0,12,1Zm0,19a8,8,0,1,1,8-8A8,8,0,0,1,12,20Z" opacity=".25"/>
  <path fill="currentColor" d="M10.14,1.16a11,11,0,0,0-9,8.92A1.59,1.59,0,0,0,2.46,12,1.52,1.52,0,0,0,4.11,10.7a8,8,0,0,1,6.66-6.61A1.42,1.42,0,0,0,12,2.69h0A1.57,1.57,0,0,0,10.14,1.16Z">
    <animateTransform attributeName="transform" dur="0.75s" repeatCount="indefinite" type="rotate" values="0 12 12;360 12 12"/>
  </path>
</svg>`

async function createBuildingModal(data) {
  const modal = document.createElement("div");
  modal.className = "cpack-modal";
  modal.style.width = "400px";
  modal.id = "building-modal";

  const title = document.createElement("div");
  title.textContent = "Building...";
  title.className = "cpack-title";

  const body = document.createElement("div");
  body.innerHTML = `
    <div id="build-info"></div>
    <pre id="build-error"></pre>
  `;

  const buttonContainer = document.createElement("div");
  buttonContainer.className = "cpack-btn-container";

  const closeButton = document.createElement("button");
  closeButton.textContent = "Close";
  closeButton.className = "cpack-btn";
  buttonContainer.appendChild(closeButton);

  modal.appendChild(title);
  modal.appendChild(body);
  modal.appendChild(buttonContainer);

  const { close } = createModal(modal);
  closeButton.onclick = close;
  closeButton.disabled = true;

  const info = body.querySelector("#build-info");
  const setError = (error) => {
    title.textContent = "Build Failed";
    info.style.display = "none";
    const pre = body.querySelector("#build-error");
    pre.textContent = error;
    pre.style.display = "block";
  }
  info.innerHTML = spinner;
  try {
    const resp = await api.fetchApi("/bentoml/build", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" }
    });
    const respData = await resp.json();
    if (respData.error) {
      setError(respData.error);
    } else {
      title.textContent = "Build Completed";
      info.innerHTML = `<div class="cpack-copyable"><span style="flex:1">${respData.bento}</span><button class="cpack-btn"><i class="mdi mdi-content-copy" /></button></div>`;
      const copyButton = info.querySelector("button");
      copyButton.onclick = () => {
        navigator.clipboard.writeText(respData.bento);
        const icon = copyButton.querySelector("i");
        icon.classList.remove("mdi-content-copy");
        icon.classList.add("mdi-check");
        setTimeout(() => {
          icon.classList.remove("mdi-check");
          icon.classList.add("mdi-content-copy");
        }, 2000);
      }
    }
  } catch(e) {
    setError(e.message);
  } finally {
    closeButton.disabled = false;
  }
}

app.registerExtension({
  name: "Comfy.CPackExtension",

  async setup() {
    const styleTag = document.createElement("style");
    styleTag.innerHTML = style;
    document.head.appendChild(styleTag);
    const menu = document.querySelector(".comfy-menu");
    const separator = document.createElement("hr");

    separator.style.margin = "20px 0";
    separator.style.width = "100%";
    menu.append(separator);

    const serveButton = document.createElement("button");
    serveButton.textContent = "Serve";
    serveButton.onclick = serveBento;
    menu.append(serveButton);

    const packButton = document.createElement("button");
    packButton.textContent = "Package";
    packButton.onclick = downloadPackage;
    menu.append(packButton);

    const buildButton = document.createElement("button");
    buildButton.textContent = "Deploy";
    buildButton.onclick = buildBento;
    menu.append(buildButton);


    try {
			// new style Manager buttons

			// unload models button into new style Manager button
			let cmGroup = new (await import("../../scripts/ui/components/buttonGroup.js")).ComfyButtonGroup(
			  new(await import("../../scripts/ui/components/button.js")).ComfyButton({
			    icon: "api",
			    action: serveBento,
			    tooltip: "Comfy-Pack",
			    content: "Serve",
			    classList: "comfyui-button comfyui-menu-mobile-collapse primary"
			  }).element,
				new(await import("../../scripts/ui/components/button.js")).ComfyButton({
					icon: "package-variant-closed",
					action: downloadPackage,
					tooltip: "Comfy-Pack",
					content: "Package",
					classList: "comfyui-button comfyui-menu-mobile-collapse"
				}).element,
				new(await import("../../scripts/ui/components/button.js")).ComfyButton({
					icon: "cloud-upload",
					action: buildBento,
					tooltip: "Comfy-Pack",
          content: "Deploy",
          classList: "comfyui-button comfyui-menu-mobile-collapse"
        }).element,
      );

			app.menu?.settingsGroup.element.before(cmGroup.element);
		}
		catch(exception) {
			console.log('ComfyUI is outdated. New style menu based features are disabled.');
		}
  }
});
