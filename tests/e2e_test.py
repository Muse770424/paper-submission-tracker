# 浏览器端到端自测：python3 tests/e2e_test.py
# 用 Playwright + Chromium 打开本地 index.html，全部样本为合成样本
import json, pathlib, sys, datetime
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / 'index.html').as_uri()
SAMPLES = ROOT / 'tests' / 'samples'
SHOTS = ROOT / 'tests' / 'screenshots'
SHOTS.mkdir(exist_ok=True)
TODAY = datetime.date.today().isoformat()

results = []
def check(tid, desc, ok, detail=''):
    results.append((tid, desc, bool(ok), detail))
    print(('  ✔ ' if ok else '  ✘ ') + tid + ' ' + desc + ('' if ok else '\n      ' + str(detail)))

def sample(name): return (SAMPLES / name).read_text(encoding='utf-8')

SEED = {
    'schemaVersion': 2, 'seeded': True, 'customStatuses': [],
    'papers': [
        {'id': 'p-tmi-0587', 'title': 'Uncertainty-guided segmentation of cardiac MRI under domain shift', 'sourceType': 'ieee',
         'venue': 'IEEE Transactions on Medical Imaging', 'manuscriptId': 'TMI-2026-0587', 'submittedDate': '2026-02-02',
         'status': 'major_revision', 'statusChangedDate': '2026-06-01', 'note': '', 'isSample': False,
         'createdAt': '2026-02-02T00:00:00.000Z', 'updatedAt': '2026-06-01T00:00:00.000Z'},
        {'id': 'p-tmi-0212', 'title': 'Diffusion priors for sparse-view photoacoustic tomography', 'sourceType': 'ieee',
         'venue': '', 'manuscriptId': 'TMI-2026-0212', 'submittedDate': '2026-02-10', 'status': 'major_revision',
         'statusChangedDate': '2026-08-12', 'note': '', 'isSample': False,
         'createdAt': '2026-02-10T00:00:00.000Z', 'updatedAt': '2026-08-12T00:00:00.000Z'},
        {'id': 'p-jclepro', 'title': 'Coupling coordination between green finance and industrial upgrading: panel evidence from 280 cities',
         'sourceType': 'elsevier', 'venue': 'Journal of Cleaner Production', 'manuscriptId': 'JCLEPRO-D-26-05110',
         'submittedDate': '2026-01-20', 'status': 'under_review', 'statusChangedDate': '2026-03-01', 'note': '', 'isSample': False,
         'createdAt': '2026-01-20T00:00:00.000Z', 'updatedAt': '2026-03-01T00:00:00.000Z'},
        {'id': 'p-access', 'title': 'Energy-aware task offloading for UAV swarms with deep reinforcement learning', 'sourceType': 'ieee',
         'venue': 'IEEE Access', 'manuscriptId': '', 'submittedDate': '2026-05-03', 'status': 'under_review',
         'statusChangedDate': '2026-05-03', 'note': '', 'isSample': False,
         'createdAt': '2026-05-03T00:00:00.000Z', 'updatedAt': '2026-05-03T00:00:00.000Z'}
    ]
}

def data(page): return json.loads(page.evaluate("localStorage.getItem('pst.data.v1')"))
def paper(page, pid): return next((p for p in data(page)['papers'] if p['id'] == pid), None)

def do_paste(page, text):
    page.click('#btn-paste')
    page.fill('#paste-text', text)
    page.click('#paste-go')
    page.wait_for_selector('#paste-step-result:not([hidden])')

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport={'width': 1200, 'height': 900}, accept_downloads=True)
    page = ctx.new_page()
    errors, requests = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: m.type == 'error' and errors.append(m.text))
    page.on('request', lambda r: (not r.url.startswith('file:') and not r.url.startswith('data:') and not r.url.startswith('blob:')) and requests.append(r.url))

    page.goto(URL)
    page.evaluate("s => { localStorage.clear(); localStorage.setItem('pst.data.v1', s); }", json.dumps(SEED))
    page.reload()

    print('\n【UI-1 ScholarOne 整页：按稿号 .R1 匹配 + 新增】')
    do_paste(page, sample('synthetic-S1-scholarone-dashboard.txt'))
    src = page.inner_text('#paste-source')
    rows = page.query_selector_all('#paste-rows .paste-row')
    check('UI-1a', '识别到 3 篇，来源 IEEE ScholarOne', len(rows) == 3 and 'IEEE ScholarOne' in src, src)
    hint2 = rows[1].query_selector('.match-hint').inner_text()
    check('UI-1b', '第 2 条按稿号匹配（修改稿 R1），显示当前状态', '按稿号匹配（修改稿 R1）' in hint2 and '当前状态：大修' in hint2, hint2)
    check('UI-1c', '其他两条默认新增', rows[0].query_selector('select').input_value() == 'new' and rows[2].query_selector('select').input_value() == 'new')
    page.screenshot(path=str(SHOTS / 'desktop-scholarone-result.png'))
    page.click('#paste-apply')
    page.wait_for_selector('#paste-dialog', state='hidden')
    d = data(page)
    p587 = paper(page, 'p-tmi-0587')
    added = [p for p in d['papers'] if p['manuscriptId'] in ('TMI-2026-0412', 'TMI-2026-0903')]
    check('UI-1d', '匹配到的论文：大修 → 审稿中，记录最近识别', p587['status'] == 'under_review' and p587['statusChangedDate'] == TODAY
          and p587['lastRecognized']['label'] == 'Awaiting AE Recommendation' and p587['lastRecognized']['system'] == 'IEEE ScholarOne', p587)
    check('UI-1e', '新增 2 篇：来源 IEEE、期刊名、投稿日期取自粘贴内容', len(added) == 2 and all(p['sourceType'] == 'ieee' for p in added)
          and {p['submittedDate'] for p in added} == {'2026-03-14', '2026-04-21'} and added[0]['venue'] == 'IEEE Transactions on Medical Imaging', added)
    check('UI-1f', '稿号保持原样（不改成 .R1）', p587['manuscriptId'] == 'TMI-2026-0587')

    print('\n【UI-2 Elsevier EM 列表：Revise 必须选大修/小修】')
    do_paste(page, sample('synthetic-E2-elsevier-em-list.txt'))
    rows = page.query_selector_all('#paste-rows .paste-row')
    check('UI-2a', '识别到 3 篇，来源 Elsevier', len(rows) == 3 and 'Elsevier' in page.inner_text('#paste-source'))
    page.click('#paste-apply')
    err = page.inner_text('#paste-apply-error')
    check('UI-2b', '不选就应用 → 提示第 2 条要选大修还是小修，弹窗不关', '第 2 条' in err and '大修' in err and page.is_visible('#paste-dialog'), err)
    rows[1].query_selector('input[value="minor_revision"]').check()
    check('UI-2c', '选择后第 2 条匹配到已有论文（稿号 R1）', '修改稿 R1' in rows[1].query_selector('.match-hint').inner_text())
    rows[0].query_selector('[data-role="check"]').uncheck()
    rows[2].query_selector('[data-role="check"]').uncheck()
    check('UI-2d', '只勾 1 条时按钮显示「应用 1 条」', page.inner_text('#paste-apply') == '应用 1 条', page.inner_text('#paste-apply'))
    page.click('#paste-apply')
    page.wait_for_selector('#paste-dialog', state='hidden')
    pj = paper(page, 'p-jclepro')
    check('UI-2e', '审稿中 → 小修，取消勾选的没有新增', pj['status'] == 'minor_revision'
          and not any(p['manuscriptId'] == 'ENVRES-D-25-09876' for p in data(page)['papers']), pj['status'])

    print('\n【UI-3 Author Portal：Rejected + Start resubmission】')
    do_paste(page, sample('synthetic-A3-authorportal-rejected-resubmit.txt'))
    row = page.query_selector('#paste-rows .paste-row')
    notices = page.inner_text('#paste-notices')
    check('UI-3a', '显示「被拒 / 大修（重投）」选择 + 粗粒度提示', row.query_selector('input[value="rejected"]') and
          row.query_selector('input[value="major_revision"]') and '粗略状态' in notices, notices)
    check('UI-3b', '无稿号的已有论文按标题匹配', '按标题匹配' in row.query_selector('.match-hint').inner_text())
    row.query_selector('input[value="major_revision"]').check()
    page.click('#paste-apply')
    page.wait_for_selector('#paste-dialog', state='hidden')
    pa = paper(page, 'p-access')
    check('UI-3c', '状态改为大修，空稿号自动补上', pa['status'] == 'major_revision' and pa['manuscriptId'] == 'Access-2026-09921', pa)

    print('\n【UI-4 大修重投换了新稿号】')
    do_paste(page, sample('synthetic-S4-scholarone-new-id-resubmission.txt'))
    hint = page.inner_text('#paste-rows .match-hint')
    check('UI-4a', '提示「可能是重投后的新稿号」并默认更新原论文', '可能是重投后的新稿号' in hint and
          page.query_selector('#paste-rows select').input_value() == 'p-tmi-0212', hint)
    page.click('#paste-apply')
    page.wait_for_selector('#paste-dialog', state='hidden')
    p212 = paper(page, 'p-tmi-0212')
    check('UI-4b', '稿号改为 TMI-2026-1188，状态改为审稿中，没有新增重复论文', p212['manuscriptId'] == 'TMI-2026-1188' and p212['status'] == 'under_review'
          and sum(1 for p in data(page)['papers'] if 'photoacoustic' in p['title']) == 1, p212)

    print('\n【UI-5 未收录说法 → 记住 → 再次识别 → 在管理状态里删除】')
    do_paste(page, 'Awaiting Referee Scores')
    check('UI-5a', '显示「工具还不认识」并提供状态、论文选择', page.is_visible('#paste-unknown') and '还不认识' in page.inner_text('#paste-unknown'))
    page.click('#paste-apply')
    check('UI-5b', '没选状态时提示', '请选择这个说法对应的状态' in page.inner_text('#paste-apply-error'))
    page.select_option('#unknown-status', 'under_review')
    page.click('#paste-apply')
    page.wait_for_selector('#paste-dialog', state='hidden')
    check('UI-5c', '说法已保存到本地数据', data(page)['pasteAliases'] == [{'text': 'Awaiting Referee Scores', 'statusId': 'under_review'}], data(page).get('pasteAliases'))
    do_paste(page, 'Awaiting Referee Scores\tTMI-2026-0412\tSelf-supervised denoising of low-dose CT with anatomy-aware contrastive priors')
    txt = page.inner_text('#paste-rows')
    check('UI-5d', '再次粘贴能识别，标注「你记住的说法」，按稿号匹配', '你记住的说法' in txt and '按稿号匹配' in txt, txt)
    page.click('#paste-cancel')
    page.click('#btn-more'); page.click('[data-menu="statuses"]')
    check('UI-5e', '管理状态里列出记住的说法', 'Awaiting Referee Scores' in page.inner_text('#alias-list'))
    page.click('#alias-list [data-aaction="delete"]')
    check('UI-5f', '删除后数据里没有了', data(page)['pasteAliases'] == [] and '还没有记住的说法' in page.inner_text('#alias-list'))
    page.click('#status-dialog .dialog-footer [data-close]')

    print('\n【UI-6 草稿与单词粘贴】')
    do_paste(page, 'Draft')
    check('UI-6a', 'Draft → 显示为跳过，不出现应用按钮', page.query_selector('#paste-rows .is-skip') and page.is_hidden('#paste-apply'))
    page.click('#paste-back')
    check('UI-6b', '「返回修改」保留刚才的文字', page.input_value('#paste-text') == 'Draft')
    page.fill('#paste-text', 'Rescinded')
    page.click('#paste-go')
    row = page.query_selector('#paste-rows .paste-row')
    check('UI-6c', 'Rescinded → 审稿中 + 说明原决定已撤回；无标题时要求选论文', '撤回了原决定' in row.inner_text() and
          '请选择要更新的论文' in row.inner_text(), row.inner_text())
    check('UI-6d', '没选论文前「应用」按钮不可点', page.is_disabled('#paste-apply'))
    row.query_selector('select').select_option('p-access')
    check('UI-6e', '选了论文后自动勾选，按钮变为「应用 1 条」', page.inner_text('#paste-apply') == '应用 1 条' and page.is_enabled('#paste-apply'))
    page.click('#paste-apply')
    page.wait_for_selector('#paste-dialog', state='hidden')
    pa = paper(page, 'p-access')
    check('UI-6f', '大修 → 审稿中，最近识别记为 Rescinded', pa['status'] == 'under_review' and pa['lastRecognized']['label'] == 'Rescinded', pa)

    print('\n【UI-7 隐私：不保存原文、不发请求、关闭即清空】')
    raw = page.evaluate("JSON.stringify(Object.assign({}, localStorage))")
    leaks = [s for s in ['ADM: Editorial Office', 'Start resubmission', 'Action Links', 'Most Recent E-mails', 'Review decision letter', 'Author Main Menu'] if s in raw]
    check('UI-7a', 'localStorage 里没有粘贴原文中的页面文字', not leaks, leaks)
    page.click('#btn-paste')
    check('UI-7b', '重新打开弹窗时输入框是空的', page.input_value('#paste-text') == '')
    page.keyboard.press('Escape')
    check('UI-7c', '整个测试过程中没有任何网络请求', not requests, requests)

    print('\n【UI-8 Stage 2 回归：表单、追踪链接、快捷改状态、备份含说法】')
    page.click('#btn-add')
    page.fill('#f-title', '回归测试论文')
    page.check('#f-source-group input[value="other"]')
    page.fill('#f-submittedDate', '2026-09-01')
    page.fill('#f-trackingUrl', 'track.example.com/abc')
    page.click('#paper-form button[type="submit"]')
    check('UI-8a', '追踪链接不是 http(s) 开头 → 报错', 'http' in page.inner_text('#e-trackingUrl'))
    page.fill('#f-trackingUrl', 'https://track.example.com/abc?id=1')
    page.click('#paper-form button[type="submit"]')
    page.wait_for_selector('#paper-dialog', state='hidden')
    np = next(p for p in data(page)['papers'] if p['title'] == '回归测试论文')
    check('UI-8b', '保存了追踪链接', np['trackingUrl'] == 'https://track.example.com/abc?id=1')
    card = page.query_selector('.paper-card:has-text("回归测试论文")')
    card.query_selector('.title-btn').click()
    link = card.query_selector('.card-details a')
    check('UI-8c', '详情里显示为新窗口打开的链接（noopener），且没有发请求', link and link.get_attribute('rel') == 'noopener noreferrer' and not requests)
    card.query_selector('select.status-select').select_option('accepted')
    check('UI-8d', '快捷改状态仍可用', next(p for p in data(page)['papers'] if p['title'] == '回归测试论文')['status'] == 'accepted')
    card587 = page.query_selector('.paper-card:has-text("Uncertainty-guided")')
    card587.query_selector('.title-btn').click()
    check('UI-8e', '详情显示最近识别', '最近识别' in card587.inner_text() and 'Awaiting AE Recommendation' in card587.inner_text())
    page.evaluate("() => { const d = JSON.parse(localStorage.getItem('pst.data.v1')); d.pasteAliases = [{text:'Pending Assessment', statusId:'submitted'}]; localStorage.setItem('pst.data.v1', JSON.stringify(d)); }")
    page.reload()
    page.click('#btn-more')
    with page.expect_download() as dl:
        page.click('[data-menu="backup"]')
    bk = json.loads(pathlib.Path(dl.value.path()).read_text(encoding='utf-8'))
    check('UI-8f', '备份文件包含记住的说法、最近识别、追踪链接，版本号为 3', bk['schemaVersion'] == 3 and bk['pasteAliases'][0]['text'] == 'Pending Assessment'
          and any('lastRecognized' in p for p in bk['papers']) and any(p.get('trackingUrl') for p in bk['papers']))
    page.click('#btn-more')
    with page.expect_download() as dl2:
        page.click('[data-menu="export-xlsx"]')
    check('UI-8g', '导出 Excel 仍可用', dl2.value.suggested_filename.endswith('.xlsx'))
    # 覆盖恢复到清空的数据里，看说法能否带回来
    bpath = dl.value.path()
    page.evaluate("() => { localStorage.setItem('pst.data.v1', JSON.stringify({schemaVersion:3, seeded:true, papers:[], customStatuses:[], pasteAliases:[]})); }")
    page.reload()
    page.set_input_files('#restore-file', bpath)
    page.wait_for_selector('#restore-dialog[open]')
    page.check('input[name="restoreMode"][value="merge"]')
    page.click('#restore-form button[type="submit"]')
    page.wait_for_timeout(300)
    check('UI-8h', '合并恢复后论文和记住的说法都回来了', len(data(page)['papers']) == len(bk['papers']) and data(page)['pasteAliases'][0]['text'] == 'Pending Assessment')
    check('UI-8i', 'Stage 2 数据（版本 2）打开后自动升级，不丢字段', all('trackingUrl' in p for p in data(page)['papers']))

    print('\n【UI-9 手机 375px】')
    m = browser.new_context(viewport={'width': 375, 'height': 812}, device_scale_factor=2, is_mobile=True, has_touch=True)
    mp = m.new_page()
    mp.on('pageerror', lambda e: errors.append(str(e)))
    mp.goto(URL)
    mp.evaluate("s => { localStorage.clear(); localStorage.setItem('pst.data.v1', s); }", json.dumps(SEED))
    mp.reload()
    sw = mp.evaluate('document.documentElement.scrollWidth')
    btns = mp.evaluate("['#btn-more','#btn-paste','#btn-add'].map(s => { const r = document.querySelector(s).getBoundingClientRect(); return [r.left, r.right, r.height]; })")
    check('UI-9a', '顶部三个按钮都在屏幕内，页面无横向滚动，按钮高度 ≥ 44px', sw <= 375 and all(b[1] <= 375 and b[0] >= 0 and b[2] >= 44 for b in btns), (sw, btns))
    mp.screenshot(path=str(SHOTS / 'mobile-list.png'))
    mp.click('#btn-paste')
    mp.screenshot(path=str(SHOTS / 'mobile-paste-input.png'))
    mp.fill('#paste-text', sample('synthetic-A1-authorportal-my-submissions.txt'))
    mp.click('#paste-go')
    mp.wait_for_selector('#paste-step-result:not([hidden])')
    over = mp.evaluate("""() => { const b = document.querySelector('#paste-dialog .dialog-body');
      return [b.scrollWidth, b.clientWidth, [...document.querySelectorAll('#paste-dialog select, #paste-dialog .paste-row')].filter(e => e.getBoundingClientRect().right > 375).length]; }""")
    check('UI-9b', '识别结果在 375px 下无横向溢出', over[0] <= over[1] and over[2] == 0, over)
    mp.screenshot(path=str(SHOTS / 'mobile-authorportal-result.png'), full_page=False)
    mp.evaluate("document.querySelector('#paste-dialog .dialog-body').scrollTop = 400")
    mp.screenshot(path=str(SHOTS / 'mobile-authorportal-result-2.png'))
    footer = mp.evaluate("[...document.querySelectorAll('#paste-dialog .dialog-footer .btn')].filter(b => b.offsetParent).map(b => { const r = b.getBoundingClientRect(); return [b.textContent, Math.round(r.right), Math.round(r.height)]; })")
    check('UI-9c', '底部按钮在屏幕内', all(f[1] <= 375 and f[2] >= 44 for f in footer), footer)

    check('UI-10', '全程无 JavaScript 报错', not errors, errors)
    browser.close()

fails = [r for r in results if not r[2]]
print('\n合计：通过 %d，失败 %d' % (len(results) - len(fails), len(fails)))
(ROOT / 'tests' / 'e2e-results.json').write_text(json.dumps([{'id': r[0], 'desc': r[1], 'pass': r[2]} for r in results], ensure_ascii=False, indent=1), encoding='utf-8')
sys.exit(1 if fails else 0)
