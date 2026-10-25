from pathlib import Path
import csv,json,math,re
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'envelope_selection'
def main():
    s=json.loads((HERE/'results/summary.json').read_text());cfg=json.loads((HERE/'protocol/selection_locked.json').read_text())
    p=next(c for c in s['contrasts'] if c['comparator']=='paired');r=next(c for c in s['contrasts'] if c['comparator']=='rtc')
    rows=['| 方法 | 认证/96 | 端点直接认证 | 平均在线轨迹副本 | 平均墙钟秒 |','|---|---:|---:|---:|---:|']
    for m,v in s['methods'].items():rows.append(f"| {m} | {v['certified']} | {v['envelope_certified']} | {v['mean_calls']:.1f} | {v['mean_wall']:.4f} |")
    comparisons=['| 比较对象/Envelope-first | 墙钟比 | 区间 | 图级正/负 | 同认证门 | 效率门 |','|---|---:|---|---|---|---|']
    for c in s['contrasts']:
        gate=str(c['efficiency_gate']) if c['comparator']!='uniform' else '不适用（描述性）'
        comparisons.append(f"| {c['comparator']} | {c['wall_ratio']:.4f} | [{c['ci_low']:.4f}, {c['ci_high']:.4f}] ({c['interval']}) | {c['positive_graphs']}/{c['negative_graphs']} | {c['quality_gate']} | {gate} |")
    families=['| 网络族 | 图式配对/新方法 | RTC配对/新方法 |','|---|---:|---:|']
    for f in cfg['families']:families.append(f"| {f} | {p['families'][f]['wall_ratio']:.4f} | {r['families'][f]['wall_ratio']:.4f} |")
    adverse=[]
    for c in s['contrasts']:
        if c['comparator']!='uniform' and not c['efficiency_gate']:adverse.append(f"- {c['comparator']}比较未通过严格效率门；不能声称相同认证质量下更快。")
        for f,v in c['families'].items():
            if v['wall_ratio']<1:adverse.append(f"- {c['comparator']}比较在{f}族的描述性比值为{v['wall_ratio']:.4f}，方向不利。")
    for m,v in s['methods'].items():
        if v['certified']<96:adverse.append(f"- {m}有{96-v['certified']}个未决结果，全部保留。")
    if not adverse:adverse=['- 本队列中所有方法均认证，所列总体比值无不利方向；这不排除其他容差、候选池或模型上的失败。']
    adverse+=['- 容差仅测试0.1（H的1%），候选仅为共享三节点的8个单交换集合；不能推广为任意搜索任务。','- RTC可以配备同样的期望端点筛查；本轮RTC基线为候选配对竞赛，未评估RTC端点筛查，故未证明最佳端点耦合引擎。','- 六分量固定投注未证明对所有分布均有限时终止；回退和未决机制不可删除。','- 最终256路径的样本最优值有噪声，不能据此报告真实误选率。','- 旧WP3效率门失败、旧30图主终点不确定、增量RTC大图更快及观测拓扑限制仍保留在正文。']
    gate='通过' if p['efficiency_gate'] else '未通过'
    text=f'''# 包络驱动有限候选选择：完整报告

## 1. 做了什么与锁定一致性

新增端点近似等价证书和独立配对回退；不把随机包络代入未经证明的Bernstein公式。完整证明见theory/envelope_selection.tex。新增8项测试和继承8项测试均通过。

锁定SHA-256：`{s['design_sha256']}`。32张新图、每图3历史、四网络族、8候选、epsilon=0.1、alpha=0.05、最大16,384在线轨迹副本。无结果驱动的图数、容差或预算调整。两个非比较性开发轮廓使用独立种子并单独保留。该锁定不是公开预注册。

## 2. 关键结果

'''+ '\n'.join(rows)+'\n\n'+ '\n'.join(comparisons)+'\n\n'+ '\n'.join(families)+f'''

全部384个方法/历史账本已逐条与原始种子和损失核对。在线总计{s['total_marginal_continuations']:,}轨迹副本，独立最终评估{s['evaluation_marginal_continuations']:,}副本；自然历史中{s['extinct_contexts']}个谣言灭绝上下文仍计入。

## 3. 失败与适用边界

'''+ '\n'.join(adverse)+f'''

## 4. 对论文主张的影响

主效率门{gate}。可保留的无条件数学主张是：在固定候选集内，错误认证事件概率不超过alpha；端点可约束未逐一模拟的候选；不能证明时返回未决。零宽度成本命题只比较指定程序，不是所有选择算法的最小最大下界。多组压缩是有证明的扩展，未实现、未实验。

序贯投注和相关候选选择已有直接先例。新增贡献应归于有序辅助控制带来的信息与决策使用，而不能称为新通用集中不等式。主文仅使用既有ref.bib条目；最近邻检索与区别见positioning.md。

## 5. 下一步建议

先审读新定理、容差含义与完整分族结果，再决定投稿。不以本队列的通过与否替代期刊创新性判断。GitHub暂不发布。无需为了继续优化而删除旧不利证据。
'''
    (HERE/'reports/envelope_selection_report.md').write_text(text)
    flat=[]
    def walk(v,path):
        if isinstance(v,dict):
            for k,x in v.items():walk(x,path+'/'+k)
        elif isinstance(v,(int,float)) and not isinstance(v,bool):flat.append(dict(quantity=path,value=v,source='envelope_selection/results/summary.json',raw='envelope_selection/results/raw',analysis='envelope_selection/analyze.py',configuration=s['design_sha256']))
    walk(s,'summary')
    with (HERE/'results/number_lineage_complete.csv').open('w') as f:w=csv.DictWriter(f,list(flat[0]));w.writeheader();w.writerows(flat)
    # Explicit post-hoc diagnostic for the analytically rumor-free case. The
    # locked primary population and gate are not changed by this calculation.
    rr=list(csv.DictReader((HERE/'results/context_results.csv').open()));lookup={(int(x['graph']),int(x['history']),x['method']):x for x in rr}
    active=[]
    for g in range(32):
        values=[]
        for h in range(3):
            a=lookup[g,h,'paired'];b=lookup[g,h,'envelope']
            if int(b['initial_rumor'])>0:values.append(math.log(float(a['wall_seconds'])/float(b['wall_seconds'])))
        if values:active.append(sum(values)/len(values))
    diag=dict(scope='post-hoc descriptive, outside the locked comparison family',active_graphs=len(active),active_contexts=sum(int(x['initial_rumor'])>0 for x in rr if x['method']=='envelope'),active_only_graph_mean_wall_ratio=math.exp(sum(active)/len(active)),active_endpoint_certificates=sum(int(x['initial_rumor'])>0 and x['route']=='envelope' for x in rr if x['method']=='envelope'),note='A common zero-rumor presolve could return without simulation in extinct contexts; it was not implemented in this locked comparison. The primary population is unchanged.')
    (HERE/'results/active_context_diagnostic.json').write_text(json.dumps(diag,indent=2)+'\n')
    with (HERE/'results/number_lineage_complete.csv').open('a') as f:
        w=csv.DictWriter(f,list(flat[0]))
        for k,v in diag.items():
            if isinstance(v,(int,float)):w.writerow(dict(quantity='active_diagnostic/'+k,value=v,source='envelope_selection/results/active_context_diagnostic.json',raw='envelope_selection/results/raw',analysis='envelope_selection/make_report.py',configuration=s['design_sha256']))
    with (HERE/'reports/envelope_selection_report.md').open('a') as f:f.write(f"\n\n## 附加事后诊断：解析灭绝情形\n\n{diag['active_contexts']}个非灭绝上下文中，端点直接认证{diag['active_endpoint_certificates']}次；排除初始谣言为0的上下文后，图级平均墙钟比为{diag['active_only_graph_mean_wall_ratio']:.4f}。该计算为事后描述，不属于锁定比较族，不替换主终点。初始无谣言的情形可用所有方法共同的解析预处理直接返回；本轮锁定程序未使用该预处理。\n")
    claims=[
        dict(claim='Anytime endpoint epsilon certificate',status='proved and implemented',evidence='envelope_selection/theory/envelope_selection.tex:thm:endpoint_certificate',scope='finite fixed portfolio; auxiliary per-node controls; independent tapes'),
        dict(claim='Erroneous certified return probability <= alpha',status='proved and implemented',evidence='envelope_selection/theory/envelope_selection.tex:thm:envelope_selection',scope='per query, not conditional on certification; unresolved is allowed'),
        dict(claim='Zero-width two-copy sample cost independent of portfolio size',status='proved',evidence='envelope_selection/theory/envelope_selection.tex:prop:zero_width_cost',scope='specified procedures; sufficient cap; not minimax or total-input-work independence'),
        dict(claim='Multigroup additive-tolerance compression',status='proved, not implemented or evaluated',evidence='envelope_selection/theory/envelope_selection.tex:Certified portfolio compression',scope='fixed partition and sum of allocated errors'),
        dict(claim='Primary matched-certified-quality cost improvement',status='confirmed' if p['efficiency_gate'] else 'not confirmed',evidence='envelope_selection/results/summary.json:contrasts/paired',scope='locked 32-graph, eight-action, epsilon=.1 task only'),
        dict(claim='RTC matched-certified-quality cost improvement',status='confirmed' if r['efficiency_gate'] else 'not confirmed',evidence='envelope_selection/results/summary.json:contrasts/rtc',scope='adjusted secondary comparison, same task'),
        dict(claim='General correlated-arm selection or betting is new',status='not claimed',evidence='envelope_selection/reports/positioning.md',scope='established prior work; new component is model-proved endpoint construction'),
        dict(claim='Original failures remain in manuscript',status='retained',evidence='envelope_selection/results/validation.json',scope='old WP3 gate, original primary, large-n RTC, observed topology, WP6 zero switches')]
    with (HERE/'results/claim_evidence_matrix.csv').open('w') as f:w=csv.DictWriter(f,list(claims[0]));w.writeheader();w.writerows(claims)
    env=json.loads((HERE/'results/environment.json').read_text())
    durations=[float(x) for x in re.findall(r'complete; ([0-9.]+)s',(HERE/'results/progress.log').read_text())]
    with (HERE/'reports/envelope_selection_report.md').open('a') as f:
        f.write(f"\n\n## 环境与时间\n\nPython：{env['python'].splitlines()[0]}；NumPy：{env['numpy']}；编译器：{env['compiler']}。CPU配额：{env.get('cpu_quota','not recorded').strip()}。单进程顺序运行。日志内32图累计运行时间约{sum(durations)/60:.1f}分钟（含历史、独立最终评估及文件写入；编译另计）；表中在线选择耗时不包含这些共同离线成本。精确计时与平台记录见environment.json及context_results.csv。\n")
        f.write('\n\n## 归档恢复与核验\n\n已从原始JCS_New_Experiment_Raw_Results.zip恢复3,216个运行时/扩展文件；现有哈希清单的全部3,217项逐字节验证通过。恢复记录见inherited_archive_recovery.json。inherited_manifest_discrepancies.json仅保留恢复前的差异历史，所列缺失已经解决。此项是归档字节核验，不是重新运行旧模拟；新选择实验的完整原始输出另行包含。\n')
if __name__=='__main__':main()
