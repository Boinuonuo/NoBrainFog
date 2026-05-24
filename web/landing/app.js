const copyStatus = document.querySelector("#copy-status");
const commandButtons = document.querySelectorAll(".copy-command");
const languageButtons = document.querySelectorAll(".language-button");

const translations = {
  en: {
    "meta.description": "NoBrainFog turns fragmented thoughts from Discord, Email, WeChat Work, or CLI into one portable Markdown task vault.",
    "nav.aria": "Main navigation",
    "nav.flow": "Flow",
    "nav.features": "Features",
    "nav.exports": "Exports",
    "language.aria": "Language switcher",
    "hero.eyebrow": "AI-powered personal task intake",
    "hero.title": "Turn messy thoughts into one portable task vault.",
    "hero.text": "NoBrainFog captures fragmented ideas from Discord, Email, WeChat Work, or CLI, organizes them into structured Markdown tasks, and keeps the real data layer simple: one local <code>todo.md</code> file.",
    "hero.github": "View on GitHub",
    "hero.exports": "See exports",
    "terminal.aria": "NoBrainFog example command output",
    "terminal.flow": "Discord / Email / CLI\n        ↓\nNoBrainFog\n        ↓\nTodo.md\n        ↓\nMarkdown / Excel / Sync",
    "flow.eyebrow": "System flow",
    "flow.title": "Adapters are replaceable. <br>The vault stays yours.",
    "flow.aria": "NoBrainFog system flow",
    "flow.node1": "Discord / Email",
    "flow.node4": "Excel / Drive",
    "features.capture.title": "Capture anywhere",
    "features.capture.text": "Send text, screenshots, forwarded emails, or fragments. NoBrainFog turns them into structured task rows.",
    "features.manage.title": "Manage by command",
    "features.manage.text": "Use commands like <code>/report</code>, <code>/done</code>,<br><code>/edit</code>, <code>/pri</code>, <code>/due</code>, and <code>/memo</code>.",
    "features.email.title": "Email gateway",
    "features.email.text": "Forward important emails into your tool inbox, or ask for reports and exports by email command.",
    "exports.eyebrow": "Portable output",
    "exports.title": "Markdown first. Excel when you need a spreadsheet.",
    "exports.text": "The core vault remains a simple <code>todo.md</code>, while Discord, Email, and CLI workflows can help you export Markdown reports or formatted <code>.xlsx</code> files for sorting, filtering, archiving, or sharing.",
    "commands.report": "Show report",
    "commands.export": "Export todo.md",
    "commands.excel": "Export Excel",
    "commands.xlsx": "Excel alias",
    "support.aria": "Donate and community",
    "support.eyebrow": "Tiny support corner",
    "support.title": "Like the project? Come say hi.",
    "support.text": "No pressure, just a small community / support link for people who want to follow along.",
    "support.button": "Donate / Community",
    "footer.text": "NoBrainFog keeps the task layer local, readable, and sync-friendly.",
    "copy.copied": "Copied"
  },
  zh: {
    "meta.description": "NoBrainFog 把 Discord、Email、企业微信或 CLI 里的碎片想法整理成一个可携带的 Markdown 任务库。",
    "nav.aria": "主导航",
    "nav.flow": "流程",
    "nav.features": "功能",
    "nav.exports": "导出",
    "language.aria": "语言切换",
    "hero.eyebrow": "AI 驱动的个人任务入口",
    "hero.title": "把心血来潮<br>灵机一动，<br>变成一个真正可管理的任务库。",
    "hero.text": "NoBrainFog 从 Discord、Email、企业微信或 CLI 接收零散想法，把它们整理成结构化 Markdown 任务，并保持真正的数据层足够简单：一个本地 <code>todo.md</code> 文件。",
    "hero.github": "查看 GitHub",
    "hero.exports": "查看导出能力",
    "terminal.aria": "NoBrainFog 示例流程",
    "terminal.flow": "Discord / Email / CLI\n        ↓\nNoBrainFog\n        ↓\nTodo.md\n        ↓\nMarkdown / Excel / 同步",
    "flow.eyebrow": "系统流程",
    "flow.title": "可替换接口，共同管理同一份任务",
    "flow.aria": "NoBrainFog 系统流程",
    "flow.node1": "Discord / Email",
    "flow.node4": "Excel / 云端",
    "features.capture.title": "随手捕捉",
    "features.capture.text": "直接发送文字、截图、转发邮件或碎片想法。NoBrainFog 会把它们整理成结构化任务行。",
    "features.manage.title": "用指令管理",
    "features.manage.text": "使用 <code>/report</code>、<code>/done</code> <br><code>/edit</code>、<code>/pri</code>、<code>/due</code>、<code>/memo</code> 等指令管理任务。",
    "features.email.title": "Email 工具人入口",
    "features.email.text": "把重要邮件转发给工具人邮箱，也可以用邮件指令索取报告和导出文件。",
    "exports.eyebrow": "可携带输出",
    "exports.title": "优先保留 Markdown，需要表格时导出 Excel。",
    "exports.text": "核心任务库仍然是简单的 <code>todo.md</code>，Discord、Email 和 CLI 都可以帮你导出 Markdown 报告或格式化 <code>.xlsx</code> 文件，方便筛选、排序、归档和分享。",
    "commands.report": "查看报告",
    "commands.export": "导出 todo.md",
    "commands.excel": "导出 Excel",
    "commands.xlsx": "Excel 别名",
    "support.aria": "投喂和社群",
    "support.eyebrow": "小小投喂角落",
    "support.title": "喜欢这个项目的话，来玩呀。",
    "support.text": "欢迎加入社群，或者有乐意投喂的老板，请疯狂戳这里！",
    "support.button": "投喂 / 社群",
    "footer.text": "NoBrainFog 让任务层保持本地、可读。甚至云端同步（可选）。",
    "copy.copied": "已复制"
  }
};

function currentDictionary() {
  const lang = document.documentElement.lang === "zh" ? "zh" : "en";
  return translations[lang];
}

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
  const dictionary = currentDictionary();

  try {
    await navigator.clipboard.writeText(command);
    setCopyStatus(`${dictionary["copy.copied"]} ${command}`);
  } catch (error) {
    console.warn("Clipboard copy failed:", error);
    setCopyStatus(command);
  }
}

function applyLanguage(lang) {
  const safeLang = lang === "zh" ? "zh" : "en";
  const dictionary = translations[safeLang];

  document.documentElement.lang = safeLang;
  document.title = safeLang === "zh"
    ? "NoBrainFog — AI 任务入口系统"
    : "NoBrainFog — AI Task Intake System";

  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    if (dictionary[key]) {
      element.textContent = dictionary[key];
    }
  });

  document.querySelectorAll("[data-i18n-html]").forEach((element) => {
    const key = element.dataset.i18nHtml;
    if (dictionary[key]) {
      element.innerHTML = dictionary[key];
    }
  });

  document.querySelectorAll("[data-i18n-attr]").forEach((element) => {
    const pairs = element.dataset.i18nAttr.split(";");
    pairs.forEach((pair) => {
      const [attribute, key] = pair.split(":");
      if (attribute && key && dictionary[key]) {
        element.setAttribute(attribute, dictionary[key]);
      }
    });
  });

  languageButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.lang === safeLang);
  });

  window.localStorage.setItem("nbf_landing_lang", safeLang);
}

commandButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const command = button.dataset.command;
    if (command) {
      copyCommand(command);
    }
  });
});

languageButtons.forEach((button) => {
  button.addEventListener("click", () => {
    applyLanguage(button.dataset.lang);
  });
});

const savedLanguage = window.localStorage.getItem("nbf_landing_lang");
const browserLanguage = navigator.language && navigator.language.toLowerCase().startsWith("zh") ? "zh" : "en";
applyLanguage(savedLanguage || browserLanguage);