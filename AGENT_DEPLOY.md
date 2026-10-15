# AI Agent 自动化部署指南 (AI Agent Deployment Guide)

本文档专为 AI Agent（如 Claude, Gemini, ChatGPT, Antigravity, OpenDevin 等）或运维自动化脚本编写，用于在 Ubuntu 环境中无人值守或半自动化部署网易 UU 远程（GameViewer）Ubuntu 桥接服务。

---

## 一、 Fork 修复背景 (Key Bugfixes in This Fork)

当前 Fork 仓库相比原上游仓库（`lachlanchen/uu-remote-ubuntu-bridge`）解决了以下关键阻断问题：
1. **FreeRDP CI Nightly 404**：上游 Jenkins 会清理旧构建导致旧版本（build 2064）无法下载，本仓库已更新为最新有效构建（build 2101）及对应校验。
2. **扫码登录弹窗黑框（Black Box）**：原版 `uu-remote-console` 使用 `x11vnc -id` 导致 UU 客户端弹出的模态子窗口（如扫码登录、确认框）变成黑块且无法点击。已修复为 `-sid` 进行子窗口树合成渲染。
3. **`uu-remote login` 生命周期**：修复了登录命令直接裸跑 Wine 进程导致的前台 Wayland 黑屏及桥接服务冲突，统一走轻量 console 容器模式。

---

## 二、 Agent 自动化部署标准步骤 (Standard Deployment Steps)

请作为 Agent 按顺序执行以下步骤：

### 步骤 1：检测本机屏幕物理分辨率并克隆仓库
```bash
# 1. 自动探测本机主显示器的物理分辨率（确保宽高比一致，避免画面变形或底部被裁剪）
CURRENT_RES=$(xrandr 2>/dev/null | grep -w connected | grep -oP '\d+x\d+' | head -n1 || echo "1920x1080")
echo "Detected resolution: $CURRENT_RES"

# 2. 克隆本 Fork 仓库（默认 main 分支已包含全部修复）
git clone https://github.com/dengjzy/uu-remote-ubuntu-bridge.git ~/uu-remote-ubuntu-bridge
cd ~/uu-remote-ubuntu-bridge
```

### 步骤 2：执行静默安装并启用核心选项
必须传入 `--cursor-guard on` 与对应分辨率：
```bash
./install.sh \
  --resolution "$CURRENT_RES" \
  --cursor-guard on \
  --cursor-size auto
```

> **参数说明与避坑点**：
> * `--cursor-guard on`（**至关重要**）：在 Wine 无头虚拟显示层下，Wine 不会生成真实物理鼠标句柄。原版默认关闭光标守卫，会导致 UU 服务端误判无鼠标，进而导致控制端（手机/电脑）**完全不显示鼠标光标**。开启后会注入 `uu-cursor-guard.dll` 并为 FreeRDP 开启 `/mouse:relative:off,grab:off`。
> * `--resolution "$CURRENT_RES"`：如果用户的屏幕是 16:10（如 1920x1200）或 2K/4K，不要使用默认的 1920x1080，否则串流画面底部会被截断（例如缺失底部 120 像素）。

### 步骤 3：唤起扫码登录窗口并提示用户
安装完成后，以普通用户身份执行：
```bash
uu-remote login
```
* 该命令会打开一个单一的 VNC 客户端窗口，展示网易 UU / GameViewer 客户端。
* **Agent 需提示用户**：在手机上打开“网易UU远程”App 或微信扫描窗口中的二维码进行登录。
* **登录完成后**：用户在本地关闭该扫码窗口即可，后台 systemd 服务（`uu-remote-bridge.service`）会自动维持运行并聚焦桌面中继。

### 步骤 4：验证服务健康状态
```bash
uu-remote verify --quick
```
当终端输出：
* `PASS systemd user service is active`
* `PASS opt-in relay and UU cursor guards are active`
* `All bridge verification checks passed.`
即代表全部服务与输入通道部署成功。

---

## 三、 常见问题诊断手册 (Troubleshooting)

| 现象 | 根因排查 | 解决方案 |
| :--- | :--- | :--- |
| **控制端连上后没有鼠标光标** | `UURB_CURSOR_GUARD` 处于 `off` 状态 | 运行 `./install.sh --skip-packages --skip-account-login --cursor-guard on --cursor-size auto` 开启光标守卫 |
| **控制端画面底部被切掉一截** | 屏幕分辨率与配置不一致（例如 1920x1200 误设为 1920x1080） | 使用 `--resolution <实际分辨率>` 重新运行安装脚本更新配置 |
| **扫码窗口点击无反应或弹黑块** | `uu-remote-console` 中 `x11vnc` 缺少 `-sid` 参数 | 确认使用的是本仓库修复版，检查 `uu-remote-console` 是否包含 `-sid` |
| **键盘输入无反应** | GNOME Wayland 下没有窗口获得焦点 | 在控制端用鼠标点击一下需要输入的窗口（如终端或文本框），确保有闪烁光标后再打字 |
