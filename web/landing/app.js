const copyStatus = document.querySelector("#copy-status");
const commandButtons = document.querySelectorAll(".copy-command");

function setCopyStatus(message) {
  if (!copyStatus) {
    return;
  }

  copyStatus.textContent = message;
  window.clearTimeout(setCopyStatus.timer);
  setCopyStatus.timer = window.setTimeout(() => {
    copyStatus.textContent = "";
  }, 1800);
}

async function copyCommand(command) {
  try {
    await navigator.clipboard.writeText(command);
    setCopyStatus(`Copied ${command}`);
  } catch (error) {
    console.warn("Clipboard copy failed:", error);
    setCopyStatus(command);
  }
}

commandButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const command = button.dataset.command;
    if (command) {
      copyCommand(command);
    }
  });
});
