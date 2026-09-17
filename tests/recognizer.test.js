// 识别引擎单元测试：node tests/recognizer.test.js
// 从 index.html 中截取 RECOGNIZER-START ~ RECOGNIZER-END 之间的代码运行，保证测的就是上线的代码
// 所有样本均为合成样本（依据公开文档中的字段和状态词构造），不是真实页面复制结果
'use strict';
var fs = require('fs');
var path = require('path');

var html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
var code = html.slice(html.indexOf('/* RECOGNIZER-START */'), html.indexOf('/* RECOGNIZER-END */'));
var PR = new Function(code + '\nreturn PasteRecognizer;')();

function sample(name) { return fs.readFileSync(path.join(__dirname, 'samples', name), 'utf8'); }

var pass = 0, fail = 0;
function check(id, desc, cond, detail) {
  if (cond) { pass++; console.log('  ✔ ' + id + ' ' + desc); }
  else { fail++; console.log('  ✘ ' + id + ' ' + desc + (detail ? '\n      实际：' + detail : '')); }
}
function brief(r) {
  return JSON.stringify({ system: r.system, records: r.records.map(function (x) {
    return [x.manuscriptId, x.kind, x.statusId, x.label, x.title.slice(0, 40)];
  }), notices: r.notices });
}
// 期望：[稿号, kind, statusId, 标题开头]
function expectRecords(id, desc, res, system, exp) {
  var ok = res.system === system && res.records.length === exp.length && exp.every(function (e, i) {
    var r = res.records[i];
    return r.manuscriptId === e[0] && r.kind === e[1] && r.statusId === e[2] && r.title.indexOf(e[3]) === 0;
  });
  check(id, desc, ok, brief(res));
}

console.log('\n【Elsevier 回归（重建的 Stage 3 三类样本）】');
expectRecords('E1', '追踪页：Status 标签优先，标题在稿号上方', PR.recognize(sample('synthetic-E1-elsevier-track.txt')), 'em',
  [['SCS-D-26-01234', 'status', 'under_review', 'Spatiotemporal evolution']]);
var e2 = PR.recognize(sample('synthetic-E2-elsevier-em-list.txt'));
expectRecords('E2', 'EM 稿件列表 3 行，Revise 需要用户选', e2, 'em', [
  ['JCLEPRO-D-26-04521', 'status', 'under_review', 'Life-cycle carbon'],
  ['JCLEPRO-D-26-05110R1', 'revise', '', 'Coupling coordination'],
  ['ENVRES-D-25-09876', 'status', 'under_review', 'Microplastic transport']]);
check('E2b', 'EM 日期按 月/日/年 解析', e2.records[0].firstDate === '2026-03-02' && e2.records[0].lastDate === '2026-07-15',
  e2.records[0].firstDate + ' ' + e2.records[0].lastDate);
check('E2c', 'R1 后缀：基础稿号为 JCLEPRO-D-26-05110', e2.records[1].baseId === 'JCLEPRO-D-26-05110' && e2.records[1].revision === 1);
expectRecords('E3', '单个状态词 Required Reviews Completed', PR.recognize(sample('synthetic-E3-elsevier-single-word.txt')), 'em',
  [['', 'status', 'under_review', '']]);
var revise = PR.recognize('Revise');
check('E4', '单词 Revise → 让用户选大修小修', revise.records.length === 1 && revise.records[0].kind === 'revise', brief(revise));

console.log('\n【T1 ScholarOne 仪表盘整页（含侧栏队列名噪声）】');
var s1 = PR.recognize(sample('synthetic-S1-scholarone-dashboard.txt'));
expectRecords('T1', '3 行状态正确，队列名不误识别', s1, 's1', [
  ['TMI-2026-0412', 'status', 'under_review', 'Self-supervised denoising'],
  ['TMI-2026-0587.R1', 'status', 'under_review', 'Uncertainty-guided'],
  ['TMI-2026-0903', 'status', 'under_review', 'Physics-informed']]);
check('T1b', '细粒度说法保留下来供展示', s1.records[1].label === 'Awaiting AE Recommendation' && s1.records[2].label === 'Awaiting EIC Decision',
  s1.records.map(function (r) { return r.label; }).join(' | '));
check('T1c', '期刊名从页面识别为 IEEE Transactions on Medical Imaging',
  s1.records[0].venue === 'IEEE Transactions on Medical Imaging', s1.records[0].venue);

console.log('\n【T2 稿号 .R1 后缀匹配已有论文】');
var papers = [
  { id: 'p1', title: 'Uncertainty-guided segmentation of cardiac MRI under domain shift', manuscriptId: 'TMI-2026-0587' },
  { id: 'p2', title: 'Diffusion priors for sparse-view photoacoustic tomography', manuscriptId: 'TMI-2026-0212' },
  { id: 'p3', title: '另一篇无关论文，用来确认不会误匹配', manuscriptId: '' }
];
var m2 = PR.matchRecord(s1.records[1], papers);
check('T2', 'TMI-2026-0587.R1 → 按稿号匹配到 p1', m2.type === 'id' && m2.paper.id === 'p1', m2.type);
var m2b = PR.matchRecord(s1.records[0], papers);
check('T2b', '没有对应论文的记录 → 新增', m2b.type === 'new', m2b.type);

console.log('\n【T3 决定词陷阱】');
var s3 = PR.recognize(sample('synthetic-S3-scholarone-decisions.txt'));
expectRecords('T3', 'Reject/Resubmit: Major → 大修；Accept with Minor → 小修', s3, 's1', [
  ['TMI-2026-0212', 'status', 'major_revision', 'Diffusion priors'],
  ['TMI-2026-0355', 'status', 'minor_revision', 'Cross-modal registration']]);
var trap1 = PR.recognize('Reject/Resubmit: Major Revisions Required');
var trap2 = PR.recognize('Accept with Minor Revisions');
check('T3b', '单独粘贴决定词也不被误判为被拒/已接收',
  trap1.records[0].statusId === 'major_revision' && trap2.records[0].statusId === 'minor_revision', brief(trap1) + brief(trap2));
var rr = PR.recognize('Reject & Resubmit');
check('T3c', 'Reject & Resubmit（未写明大修）→ 让用户选', rr.records[0].kind === 'reject_or_resubmit', brief(rr));

console.log('\n【T4 Assignment 区分（多行单元格布局）】');
expectRecords('T4', 'Reviewer Assignment → 审稿中；AE Assignment → 已投稿（编辑处理）',
  PR.recognize(sample('synthetic-S2-scholarone-multiline-cells.txt')), 's1', [
    ['TVT-2025-03310', 'status', 'under_review', 'Graph neural networks'],
    ['TVT-2026-00127', 'status', 'submitted', 'Federated split learning']]);

console.log('\n【T5 Author Portal 整页（含 10 个状态词的筛选项、Submitted 日期标签）】');
var a1 = PR.recognize(sample('synthetic-A1-authorportal-my-submissions.txt'));
expectRecords('T5', '3 张卡片正确；筛选项和日期标签不误判', a1, 'ap', [
  ['Access-2026-18342', 'status', 'under_review', 'Lightweight transformer'],
  ['TII-26-2217', 'revise', '', 'Digital twin'],
  ['JSEN-2026-11809', 'status', 'accepted', 'Flexible strain sensor']]);
check('T5b', '提示已忽略筛选项、提示 Author Portal 状态粗',
  a1.notices.join('').indexOf('筛选') >= 0 && a1.notices.join('').indexOf('粗略') >= 0, a1.notices.join(' / '));
check('T5d', '卡片上方的期刊名归属正确（不会错位到上一张卡片）',
  a1.records[0].venue === 'IEEE Access' && a1.records[1].venue === 'IEEE Transactions on Industrial Informatics' && a1.records[2].venue === 'IEEE Sensors Journal',
  a1.records.map(function (r) { return r.venue; }).join(' | '));
check('T5e', 'ScholarOne 页面顶部的期刊名适用于每一行', s1.records.every(function (r) { return r.venue === 'IEEE Transactions on Medical Imaging'; }),
  s1.records.map(function (r) { return r.venue; }).join(' | '));
var a2 = PR.recognize(sample('synthetic-A2-authorportal-no-ids.txt'));
expectRecords('T5c', '卡片不显示稿号时按状态分段', a2, 'ap', [
  ['', 'status', 'under_review', 'Lightweight transformer'],
  ['', 'status', 'accepted', 'Flexible strain sensor']]);

console.log('\n【T6 Author Portal：Rejected + Start resubmission】');
expectRecords('T6', '→ 让用户选「被拒 / 大修（重投）」', PR.recognize(sample('synthetic-A3-authorportal-rejected-resubmit.txt')), 'ap',
  [['Access-2026-09921', 'reject_or_resubmit', 'rejected', 'Energy-aware task offloading']]);
var plainRej = PR.recognize('My Submissions\nRejected\nSome sufficiently long title about sensor networks\nManuscript ID: Access-2026-00001');
check('T6b', '没有 Start resubmission 的 Rejected → 直接被拒', plainRej.records[0].kind === 'status' && plainRej.records[0].statusId === 'rejected', brief(plainRej));

console.log('\n【T7 大修重投换了新稿号】');
var s4 = PR.recognize(sample('synthetic-S4-scholarone-new-id-resubmission.txt'));
var m7 = PR.matchRecord(s4.records[0], papers);
check('T7', '新稿号 TMI-2026-1188 + 相同标题 → 提示可能是重投（title_newid）', m7.type === 'title_newid' && m7.paper.id === 'p2', m7.type);

console.log('\n【T8 单词粘贴】');
[['Rescinded', 'rescinded', 'under_review'], ['Draft', 'draft', ''], ['Withdrawn', 'status', 'withdrawn'],
  ['Replaced', 'replaced', ''], ['In Revision', 'revise', ''], ['Awaiting Reviewer Assignment', 'status', 'under_review'],
  ['Awaiting AE Assignment', 'status', 'submitted'], ['Under Review', 'status', 'under_review'],
  ['Status: Accepted', 'status', 'accepted']].forEach(function (c, i) {
  var r = PR.recognize(c[0]);
  check('T8.' + (i + 1), c[0] + ' → ' + (c[2] || c[1]), r.records.length === 1 && r.records[0].kind === c[1] && r.records[0].statusId === c[2], brief(r));
});

console.log('\n【T9 未收录说法 + 记住】');
var t9a = PR.recognize('Awaiting Referee Scores');
check('T9', '未收录时识别不到', t9a.records.length === 0 && !t9a.hasAnyHit, brief(t9a));
var t9b = PR.recognize('Awaiting Referee Scores', { aliases: [{ text: 'Awaiting Referee Scores', statusId: 'under_review' }] });
check('T9b', '记住后能识别，且标记为「你记住的说法」', t9b.records.length === 1 && t9b.records[0].statusId === 'under_review' && t9b.records[0].viaAlias, brief(t9b));
var t9c = PR.recognize('Awaiting Referee Scores\tTMI-2026-0777\tA reasonably long manuscript title for alias testing', { aliases: [{ text: 'awaiting referee scores', statusId: 'cs_abc' }] });
check('T9c', '记住的说法可以对应自定义状态，大小写不敏感', t9c.records[0].statusId === 'cs_abc', brief(t9c));

console.log('\n【T10 来源识别】');
check('T10', 'EM / ScholarOne / Author Portal 各自识别正确',
  e2.system === 'em' && s1.system === 's1' && a1.system === 'ap', [e2.system, s1.system, a1.system].join(','));
var mixedTitle = PR.recognize('Under Review\tSOME-2026-1234\tAn evaluation of ISO-9001 adoption and ResNet-101 models in factories');
check('T10b', '标题里的 ISO-9001、ResNet-101 不会被当成稿号', mixedTitle.records.length === 1 && mixedTitle.records[0].manuscriptId === 'SOME-2026-1234', brief(mixedTitle));
var dates = ['2026-03-12', '12-Mar-2026', 'Mar 12, 2026', '12 Mar 2026', '03/12/2026', '2026年3月12日'].map(PR.parseDate);
check('T10c', '6 种日期写法都解析为 2026-03-12', dates.every(function (d) { return d === '2026-03-12'; }), dates.join(','));

console.log('\n合计：通过 ' + pass + '，失败 ' + fail);
process.exit(fail ? 1 : 0);
