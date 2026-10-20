# Yano · HTML 阅读书架

使用 GitHub Pages 托管的静态 HTML 文章库，自动生成目录和搜索首页。

**仓库**：https://github.com/LjyYano/html-library

**计划域名**：https://read.yano.blog

## 启用 GitHub Pages

1. 仓库打开 **Settings → Pages → Build and deployment → Source**，选择 **GitHub Actions**。
2. 如 Actions 部署没有自动触发，打开 **Actions → Build and deploy HTML library → Run workflow**，选 main。
3. GitHub Pages 站点启用后，在 **Settings → Pages → Custom domain** 填写 read.yano.blog。
4. 到 yano.blog 的 DNS 托管平台添加 `CNAME`：主机记录 `read`，目标 `LjyYano.github.io`（不带 https:// 和仓库路径）。
5. 验证域名后，在 GitHub Pages 设置开启 **Enforce HTTPS**。

配置完成后，首页 https://read.yano.blog/ ，文章 https://read.yano.blog/wealth-tips/ 和 https://read.yano.blog/car-cost/ 。

## 后续新增 HTML

将文章存为 `pages/<slug>/index.html` 即可；可选创建同目录的 `article.json` 设置标题、摘要、分类、标签及日期。

```json
{
  "title": "示例文章",
  "description": "简短介绍",
  "category": "读书笔记",
  "tags": ["阅读", "笔记"],
  "date": "2026-10-20"
}
```

提交到 `main` 后，GitHub Actions 运行 `python scripts/build.py` 自动扫描文章、生成首页与 `articles.json`，并部署到 GitHub Pages。支持独立 HTML 里的原有 CSS 和 JavaScript。

也可以直接添加 `pages/<slug>.html` 文件。若无 article.json，使用 HTML 的 `<title>` 和 `meta description`。

## 本地预览

```bash
python3 scripts/build.py
python3 -m http.server 8000 --directory dist
```

然后打开 http://localhost:8000/ 。

## 提醒

- 这是公开网站，请勿上传私密信息或未经许可的内容。
- 公共发布第三方视频的完整字幕可能涉及版权，请确认授权和使用范围。
- GitHub Pages 仅支持静态 HTML/CSS/JS，在部分地区可访问性可能随网络状况变化。
