from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'witness_selection'
def main():
 s=json.loads((HERE/'results/summary.json').read_text());v=json.loads((HERE/'results/validation.json').read_text());c=json.loads((HERE/'protocol/witness_locked.json').read_text())
 names={'old_screen':'Original screened race','witness_screen':'Fixed-witness screened race','witness_plain':'Fixed-witness unscreened race'}
 lines=['# 固定最优见证的认证机制优化：独立锁定实验','', '## 1. 做了什么','',
 '只改进回退竞赛的多重比较上界：用一个固定真实最优动作作为证明中的见证，控制其被错误淘汰和错误认证其他动作两类事件。模拟引擎、候选生成、32 条批次、混合下注、筛选的风险对半分配及无效筛选退出规则均保持不变。', '',
 '筛选版回退阈值从 8.407378 降到 6.327937；不筛选版使用 5.634790。精度 ε=0.1、每查询错误概率上限 α=0.05 均保持不变。完整证明见 theory/witness_bound.md。该结论属于标准固定见证论证的收紧，不声称优先权或最优样本复杂度。','',
 f"锁定 SHA-256：`{s['lock_sha256']}`。时间：{c['locked_at_utc']}。32 张新图、四族各 8 张、每图 3 条历史，共 96 情境。全部预设比较与所有图均保留；无结果驱动重跑。",'',
 '**预算变化须单独解释：** 所有方法共同上限改为 32,768 个边际轨迹副本，是此前上限的两倍。机制效果由本轮同预算对照估计；不能把与旧队列的认证率差异全部归因于机制。旧预算列仅记录本轮在耗费不超过 16,384 副本时已认证的情境数，并非独立重跑旧上限。','',
 'α=0.05 是每查询错误上限，不是 96 个查询的联合错误上限。','', '## 2. 关键结果','', '| Method | Certified / 96 | Certified using ≤16,384 copies | Endpoint certificates | Mean copies | Mean wall (s) | Total wall (s) |','|---|---:|---:|---:|---:|---:|---:|']
 for m,r in s['methods'].items():lines.append(f"| {names[m]} | {r['certified']} | {r['certified_by_old_cap']} | {r['endpoint_certified']} | {r['mean_calls']:.2f} | {r['mean_wall']:.5f} | {r['total_wall']:.3f} |")
 lines+=['','两个墙钟比均预先声明，图级分族 bootstrap 20,000 次，给出 Bonferroni 校正的 97.5% 区间。比值大于 1 表示分母方法更快。CPU 与轨迹副本区间仅作描述。','', '| Contrast | Geometric wall ratio [97.5% CI] | Graphs favor denominator | All-query quality gate | Overall gate |','|---|---|---:|---|---|']
 for r in s['contrasts']:
  t=r['wall_seconds'];lines.append(f"| {r['numerator']} / {r['denominator']} | {t['ratio']:.5f} [{t['ci'][0]:.5f}, {t['ci'][1]:.5f}] | {t['positive_graphs']}/32 | {r['quality_gate']} | {r['passed']} |")
 lines+=['','### 分族方向（描述性）','', '| Contrast | ER | WS | SBM | PA + closure |','|---|---:|---:|---:|---:|']
 for r in s['contrasts']:lines.append('| '+r['name']+' | '+' | '.join(f"{x:.5f}" for x in r['wall_seconds']['families'].values())+' |')
 lines+=['','## 3. 失败与不利结果','']
 for r in s['contrasts']:
  lines.append(f"- {r['name']}: {'通过预设门槛' if r['passed'] else '未通过预设门槛'}。质量门={r['quality_gate']}；校正成本下界={r['wall_seconds']['ci'][0]:.5f}。")
 lines+=['- 此前两轮 94/96、95/96 的失败结论保持有效，不由本轮替换。','- 采用更高共同预算，不能声称在原上限下普遍解决所有认证问题。','- 若几何比值有利，仍应同时查看算术平均和总耗时，不能将其等同为总时间缩减。','- 独立 256 条评估轨迹只能给出噪声评估，不能证明本轮所有认证都正确或估计罕见错误率。','- 本次只覆盖同一固定八动作、一换节点的候选结构，不能外推至所有组合搜索或任意图规模。','',
 '## 4. 对论文主张的影响','',
 ('本轮支持在该预设队列、共同预算和相同认证标准下，相对原筛选实现的成本改善。' if s['contrasts'][0]['passed'] else '本轮尚不支持相对原筛选实现的匹配认证质量成本优势。'),
 ('独立的筛选政策对照也通过，因此可以在本轮范围内报告筛选政策的成本收益。' if s['contrasts'][1]['passed'] else '筛选相对改进后不筛选竞赛的优势仍未通过门槛，不应把阈值优化收益写成包络筛选的独立收益。'),
 '新增理论保证最终返回动作的 ε-精度错误概率；不承诺所有内部成对断言同时正确。这与本实验原有的最终选择质量门一致。它不保证固定预算必然认证，不保证每条随机路径更早停止，也不提升组合目标的近似比。此轮没有改变 FEX/NEX 的历史结果。','',
 '## 5. 复现与下一步','',f"原始数据逐项重放 {v['replayed_decisions']} 个决策，种子、动作、损失范围、事件、认证、调用数、配置及源文件哈希核对通过。在线副本 {v['online_copies']:,}；独立评估副本 {v['evaluation_copies']:,}。",'',
 '`python reproduce_witness.py --analysis-only` 从已保存原始输出重新统计、重放验证并生成报告与图。去掉 `--analysis-only` 可以运行/续跑固定实验；已完成图不会重跑。', '',
 '建议保留新机制及全部负面证据，按本轮判定范围修订论文；不增加事后确认性比较。']
 (HERE/'reports/witness_report.md').write_text('\n'.join(lines)+'\n')
 (HERE/'reports/paper_insertion.tex').write_text(r'''\subsection{A fixed-witness refinement of portfolio certification}
For a fixed portfolio of $M$ actions, fix a deterministic true minimizer
$j^\star$ in the proof. Only $M-1$ exact tests can incorrectly remove
$j^\star$; conditional on retaining it, an $\epsilon$-bad output must pass
one of at most $M-1$ approximate tests against $j^\star$. A union bound
therefore gives total error at most $r$ with race threshold
$\log(2(M-1)/r)$, rather than $\log(2M(M-1)/r)$.
The argument accommodates ties and adaptive elimination, with fresh tapes
and predictable sampling. It provides an error guarantee, not universal
termination or an approximation ratio for the combinatorial objective.
'''+'\n% Numerical insertion is generated only from the independent locked cohort.\n'+
 f"In a new locked cohort of 32 graphs and 96 contexts, the refined screened race certified {s['methods']['witness_screen']['certified']}/96 queries under the common 32,768-copy cap. "+
 f"The original-to-refined geometric wall-time ratio was {s['contrasts'][0]['wall_seconds']['ratio']:.3f} "+
 f"(multiplicity-adjusted 97.5\\% interval [{s['contrasts'][0]['wall_seconds']['ci'][0]:.3f}, {s['contrasts'][0]['wall_seconds']['ci'][1]:.3f}]). "+
 'This cap is twice that of the earlier studies; their unresolved outcomes remain reported.\n')
if __name__=='__main__':main()
