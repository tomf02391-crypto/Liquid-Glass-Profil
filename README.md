# Telegram Mini App 部署指南

## 概述

本项目将 Telegram 个人资料页 Liquid Glass 设计概念制作为可在 Telegram 中直接打开使用的 **Mini App**。

文件：`telegram-mini-app.html`

---

## 部署步骤

### 第 1 步：创建 Telegram Bot

1. 打开 Telegram，搜索并打开 **@BotFather**
2. 发送 `/newbot`
3. 输入 Bot 名称（如 `Liquid Glass Profile`）
4. 输入 Bot 用户名（如 `LiquidGlassProfileBot`）
5. 保存 BotFather 返回的 **API Token**

### 第 2 步：托管 HTML 文件

Mini App 必须通过 **HTTPS** 访问。选择任一方式：

**方式 A：GitHub Pages（免费）**
```
1. 创建 GitHub 仓库
2. 上传 telegram-mini-app.html
3. Settings → Pages → Source: main 分支
4. 获得 URL: https://用户名.github.io/仓库名/telegram-mini-app.html
```

**方式 B：Vercel / Netlify（免费）**
```
1. 注册 vercel.com 或 netlify.com
2. 拖拽上传 telegram-mini-app.html
3. 获得自动分配的 HTTPS URL
```

**方式 C：自有服务器**
```
1. 将文件放到 Web 服务器
2. 配置 SSL 证书（HTTPS 必须）
```

### 第 3 步：配置 Mini App URL

回到 @BotFather：

```
1. 发送 /newapp
2. 选择你的 Bot
3. 输入 App 名称：Liquid Glass Profile
4. 输入简短描述：Liquid Glass 设计的个人资料页
5. 输入长描述
6. 上传一张 640x360 的宣传图
7. 输入你的 HTTPS URL
8. 输入简短名称（用于菜单按钮）：Profile
```

### 第 4 步：设置菜单按钮（可选但推荐）

```
1. 发送 /setmenubutton
2. 选择你的 Bot
3. 输入 HTTPS URL
4. 输入按钮文字：打开资料页
```

用户在 Bot 聊天界面点击左下角菜单按钮即可打开 Mini App。

### 第 5 步：测试

1. 在 Telegram 中搜索你的 Bot
2. 点击 `启动` 或菜单按钮
3. Mini App 在 Telegram 内全屏打开
4. 体验触觉反馈、弹窗、返回按钮等原生功能

---

## 集成的 Telegram 原生功能

| 功能 | 说明 |
|------|------|
| `WebApp.ready()` | 通知 Telegram Mini App 已加载 |
| `WebApp.expand()` | 全屏展开 |
| `WebApp.themeParams` | 读取用户 Telegram 主题颜色，自动适配明暗模式 |
| `WebApp.setHeaderColor()` | 设置 WebView 顶部状态栏颜色 |
| `BackButton` | 原生返回按钮，点击关闭 Mini App |
| `MainButton` | 底部主操作按钮，根据当前标签页动态切换文字 |
| `HapticFeedback` | 触觉反馈（轻触、中击、成功、警告等） |
| `showPopup()` | 原生弹窗（屏蔽用户、举报等操作） |
| `switchInlineQuery()` | 原生分享到其他聊天 |
| `themeChanged` 事件 | 监听用户切换明暗模式，实时更新配色 |
| `viewportChanged` 事件 | 监听视口变化，重新计算标签指示器位置 |

---

## 本地预览

直接用浏览器打开 `telegram-mini-app.html` 可预览界面布局。
顶部会显示「预览模式」提示条，Telegram API 功能不可用（显示 Toast 提示）。

完整功能需在 Telegram 客户端内打开。

---

## 文件说明

```
telegram-mini-app.html    ← Mini App 主文件（部署此文件）
telegram-profile-redesign.html  ← 设计概念对比原型（仅展示用）
```
