# Yano · HTML 阅读书架

静态 HTML 收藏库，使用 GitHub Pages 自动部署。

- 首页：https://read.yano.blog/
- 仓库：https://github.com/LjyYano/html-library
- 页面：[原始积累的 5 条建议](https://read.yano.blog/wealth-tips/) · [买车成本分析](https://read.yano.blog/car-cost/)

## 1. 首页

首页自动生成 **Notion 风格表格**：一篇 HTML 对应一行，展示名称、分类、标签和日期；支持搜索、行点击跳转和深浅色切换，不添加宣传区或卡片网格。

## 2. 新增网页

创建 `pages/<slug>/index.html`，可选在同目录添加 `article.json`：

```json
{
  "title": "文章标题",
  "description": "简短描述",
  "category": "读书笔记",
  "tags": ["阅读", "笔记"],
  "date": "2026-10-20",
  "source": "Bilibili"
}
```

直接提交到 `main`，GitHub Actions 会生成首页索引并部署，无需手动维护目录。

## 3. 为阅读网页增加 Anki Tab

同目录添加 `anki.json` 后，构建脚本会将 **Anki** 标签嵌入已有的 tab 布局，生成可展开的原句卡片，同时提供 `anki-import.tsv` 和 `anki-cards.md` 下载。已支持本仓库两种阅读页面模板。

JSON 结构：

```json
{
  "title": "文章 · Anki 精选原句",
  "source_type": "raw_srt",
  "source_note": "根据原始字幕逐字摘录，时间为字幕原始区间。",
  "source_url": "https://www.bilibili.com/video/XXXX/",
  "cards": [
    {
      "title": "简短的中性主题",
      "front": "字幕中的完整原句。",
      "back": "包含此句的连续原文上下文。",
      "time": "03:22–03:46"
    }
  ]
}
```

请遵循原定 `subtitle-to-anki` 规则：

- **默认 6–8 张**，宁少勿凑，按视频顺序去重。
- **Anki Basic，不采用问答式**；正面是值得复习的原句，不是 AI 改写或总结。
- 背面是**连续原文上下文和可信时间戳**，不得拼接不连续句子或杜撰案例。
- 只补标点、调整换行；逐句比对原始字幕，避免替换原词。
- 缺少原始 SRT 的情况下，不把网页整理稿称为「原始字幕」，不推测时间码。
- TSV 使用 UTF-8、**无表头、两列（正面 / 背面）**；Anki 导入时选择 Basic + Tab 分隔 + HTML 字段。

`anki.json` 的选句需要根据来源人工/模型精读并完成校验；构建脚本仅负责渲染和导出，不从文章自动编造卡片。两份已配置的卡片集来自用户提供的 SRT（原始积累）和用户提供的 HTML 转录（买车分析）。

## 4. 本地预览

```bash
python3 scripts/build.py
python3 -m http.server 8000 --directory dist
```

然后打开 http://localhost:8000/ 。

## 5. 部署与域名

- Settings → Pages → Source 选择 **GitHub Actions**。
- DNS 添加 `CNAME`：主机 `read`，目标 `LjyYano.github.io`。
- Settings → Pages → Custom domain 设置 `read.yano.blog`，验证后启用 HTTPS。

**注意：** 当前仓库公开可见，不要提交个人隐私或未经授权的敏感内容；第三方视频完整转录公开转载可能存在版权问题。
