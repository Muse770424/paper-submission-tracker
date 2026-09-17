# 自测

## 运行

```bash
# 1. 识别引擎（不需要安装任何依赖）
node tests/recognizer.test.js

# 2. 页面端到端（需要 Python 和 Playwright）
pip install playwright
playwright install chromium
python3 tests/e2e_test.py
```

`recognizer.test.js` 直接从 `index.html` 里截取 `RECOGNIZER-START` 到 `RECOGNIZER-END` 之间的代码运行，测的就是上线的代码。`e2e_test.py` 会在 `tests/screenshots/` 生成截图，这个目录不提交。

## 样本说明

`samples/` 里的文件**全部是合成样本**，依据 IEEE、Elsevier、ScholarOne 公开帮助文档中的字段和状态词编写，**不是真实页面的复制结果**。论文标题、稿号、期刊对应关系都是虚构的。

| 文件 | 模拟的页面 |
|---|---|
| synthetic-E1-elsevier-track.txt | Elsevier 稿件追踪页 |
| synthetic-E2-elsevier-em-list.txt | Editorial Manager 稿件列表（表格） |
| synthetic-E3-elsevier-single-word.txt | 只复制一个状态词 |
| synthetic-S1-scholarone-dashboard.txt | ScholarOne Author Dashboard 整页（含侧栏） |
| synthetic-S2-scholarone-multiline-cells.txt | ScholarOne 表格复制后单元格拆成多行 |
| synthetic-S3-scholarone-decisions.txt | ScholarOne「Manuscripts with Decisions」 |
| synthetic-S4-scholarone-new-id-resubmission.txt | 大修重投后换了新稿号 |
| synthetic-A1-authorportal-my-submissions.txt | Author Portal「My Submissions」整页（含筛选项） |
| synthetic-A2-authorportal-no-ids.txt | Author Portal 卡片不显示稿号 |
| synthetic-A3-authorportal-rejected-resubmit.txt | Author Portal 被拒但可重投 |

如果你愿意提供真实页面的复制文字帮助校准，请先删掉标题、姓名、邮箱等个人信息。
