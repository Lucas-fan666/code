from pathlib import Path
import csv,json,math
import numpy as np
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'adaptive_screening'
def main():
 s=json.loads((HERE/'results/summary.json').read_text());v=json.loads((HERE/'results/validation.json').read_text());cfg=json.loads((HERE/'protocol/adaptive_locked.json').read_text());p=s['contrasts'][0];w=p['wall_seconds'];m=s['methods'];enabled=0;skipped=0;presolved=0
 for f in (HERE/'results/raw').glob('graph_*/h*_adaptive_screen.json'):
  r=json.loads(f.read_text());pilot=[q for q in r['events'] if q['stage']=='pilot']
  if pilot:enabled+=bool(pilot[0]['screen_enabled']);skipped+=not pilot[0]['screen_enabled']
  else:assert r['route']=='exact_extinction';presolved+=1
 lines=['# 独立试算路由与条件风险分配：锁定效率实验','', '## 1. 做了什么','',
 '新策略先用四条独立端点轨迹（八个边际副本）做计算路由；试算均值小于 ε/2 才启用筛选。试算不用于认证。跳过筛选时，竞赛使用完整 α；启用筛选时，分别为独立筛选与新轨迹回退分配 0.1α、0.9α。完整条件化证明见 theory/conditional_routing.md。该机制采用标准条件化和鞅论证，不声称一般统计工具的优先权。','',
 '比较对象是冻结的 witness_plain 强基线。两种方法共用完全相同的精确灭绝预处理：初始无谣言时直接认证零损失。全部情境保留，预处理的实测时间计入在线成本。两种方法使用对齐的竞赛种子流，但各自运行并计费全部模拟，无跨方法缓存；试算、筛选和竞赛使用相互分离的随机坐标。','',
 f"锁定时间：{cfg['locked_at_utc']}；SHA-256：`{s['lock_sha256']}`。32 张新图、四族各 8 张，每图 3 条自然历史。与上轮相同的 ε=0.1、每查询 α=0.05、共同预算 32,768；预算没有继续扩大。全部数据、失败与不利结果均保留，无比较结果驱动的改动。",'',
 '唯一确认性成本终点为 plain/adaptive_screen 的图级几何墙钟比，分族图级 bootstrap 20,000 次，使用保守的中央 97.5% 区间。两方法全部 96 次取得证书且区间下界大于 1 才通过；CPU、轨迹数、分族和总时间是描述性。α 不是 96 查询的联合错误上限；本区间也不保护全部历次研究序列。','',
 '## 2. 关键结果','', '| Method | Certified / 96 | Certified using ≤16,384 | Exact presolve | Endpoint certificates | Mean copies | Mean wall (s) | Total wall (s) |','|---|---:|---:|---:|---:|---:|---:|---:|']
 for name,r in m.items():lines.append(f"| {name} | {r['certified']} | {r['certified_by_old_cap']} | {r['presolved']} | {r['endpoint_certified']} | {r['mean_calls']:.2f} | {r['mean_wall']:.6f} | {r['total_wall']:.4f} |")
 lines+=['',f"预设几何墙钟比：**{w['ratio']:.6f} [{w['ci'][0]:.6f}, {w['ci'][1]:.6f}]**，中央 97.5% 区间；图级符号：{w['positive_graphs']} 正、{w['negative_graphs']} 负。质量门：{p['quality_gate']}；联合效率门：**{p['passed']}**。",'',
 f'试算启用筛选 {enabled} 次，跳过 {skipped} 次；精确灭绝预处理 {presolved} 次。全部试算消耗 {8*(enabled+skipped)} 个边际副本。','', '| Family | Plain/adaptive geometric wall ratio (descriptive) |','|---|---:|']
 for f,x in w['families'].items():lines.append(f'| {f} | {x:.6f} |')
 rows=list(csv.DictReader((HERE/'results/context_results.csv').open()));lookup={(int(z['graph']),int(z['history']),z['method']):z for z in rows};nonzero=[]
 for g in range(32):
  values=[math.log(float(lookup[g,h,'plain']['wall_seconds'])/float(lookup[g,h,'adaptive_screen']['wall_seconds'])) for h in range(3) if int(lookup[g,h,'plain']['initial_rumor'])>0]
  if values:nonzero.append(float(np.mean(values)))
 lines+=['',f'非灭绝情境的描述性图级几何墙钟比：{math.exp(float(np.mean(nonzero))):.6f}（{len(nonzero)} 张至少含一个非灭绝情境的图；无确认性区间或额外成功主张）。','', '| Descriptive metric | Plain/routed ratio | Interval (descriptive) |','|---|---:|---|']
 for metric in ['cpu_seconds','marginal_continuations']:
  z=p[metric];lines.append(f"| {metric} | {z['ratio']:.6f} | [{z['ci'][0]:.6f}, {z['ci'][1]:.6f}] |")
 lines+=['','## 3. 失败与不利结果','',
 ('- 本轮联合效率门通过，但不能外推到不同容差、候选结构或图规模。' if p['passed'] else '- 本轮联合效率门未通过；不能将有利点估计写成已确认优势。'),
 '- 此前固定风险分配筛选的所有不利比较仍保留；本轮不是旧实验的替代，也不是对旧实验门槛的事后改判。',
 '- 四条试算和 10% 风险分配是从既有开发材料提出并在新实验前冻结的工程选择，没有最优性证明。',
 '- 图形耦合本身没有被本轮证明普遍快于其他耦合；本轮唯一比较是同引擎、同精度的筛选策略。',
 '- 精确灭绝预处理供双方共同使用，减少了筛选从该简单捷径获益的机会。',
 '- 相同随机流不表示不同候选组合下逐种子路径必然完全一致；正确边际和新轨迹条件期望才是认证所需条件。','',
 '机制核验确认：66 个跳过筛选的情境，其竞赛动作、种子、损失及最终选择与强基线完全相同，仅额外计费 8 个试算副本；26 个启用情境的试算均未混入认证；4 个共同灭绝预处理情境无模拟调用。见 results/mechanism_audit.json。','', '## 4. 对论文主张的影响','',
 ('可以在这组锁定配置与新独立队列下，报告独立试算与条件风险分配的匹配认证质量效率收益。' if p['passed'] else '尚不能将筛选作为已确认的效率贡献；保留可选策略定位。'),
 '条件路由定理保证任意试算路由规则下的错误控制，不保证路由准确、停止、全局组合近似比或普遍加速。论文应把条件有效性与队列中的成本结果分别陈述。','',
 '## 5. 复现与建议','',f"从全部原始损失重放 {v['replayed_decisions']} 个决策通过。在线副本 {v['online_copies']:,}；独立评估副本 {v['evaluation_copies']:,}；配置、源文件哈希、种子、动作、事件及账目验证通过。",'',
 '`python reproduce_adaptive.py --analysis-only --build-paper` 重算统计、验证全部决策并编译完整稿。省略 `--analysis-only` 可运行/续跑已锁定实验，不重跑已完成图。', '',
 '建议按该结论范围整合论文，保留全部历史失败；不继续以事后调参追逐门槛。']
 (HERE/'reports/adaptive_report.md').write_text('\n'.join(lines)+'\n')
 (HERE/'results/routing_summary.json').write_text(json.dumps(dict(enabled=enabled,skipped=skipped,presolved=presolved,pilot_copies=8*(enabled+skipped)),indent=2)+'\n')
if __name__=='__main__':main()
