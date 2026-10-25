from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'coupling_factorial'
LABEL={'envelope':'Graphical + screen','paired':'Graphical race','rtc_envelope':'RTC + screen','rtc':'RTC race'}
def main():
 s=json.loads((HERE/'results/summary.json').read_text());c=json.loads((HERE/'protocol/factorial_locked.json').read_text());L=[]
 L+=['# 四组归因确认实验报告','', '## 1. 做了什么','',f"锁定配置 SHA-256：`{s['lock_sha256']}`。32 张新图 × 3 条未条件筛选的历史，ER/WS/SBM/PA+闭合各 8 图。使用与上一轮相同的模型参数、8 候选构造、容差 0.1、每查询风险 0.05 和 16,384 在线副本上限。所有方法逐个顺序运行，随机化顺序，RTC 端点差保留符号。计时在候选规范化和最初接口检查后开始；逐调用模拟器校验、检验更新、分配与轨迹收集计入。配置中的 Python 校验指该逐调用过程，未重新将入口预处理补计进旧时钟。所有辅助副本计费。四个成本对比采用图级分族 bootstrap 的 98.75% 区间。该哈希为本地运行前锁定，不是独立公证的公开预注册。",'', '筛选组各用一半风险做筛选及回退；无筛选组使用全部风险。对比评估完整筛选策略，不能把风险预留成本与信息作用完全分离。没有引入灭绝预处理，没有测试其他候选重叠结构。引擎对比同时包含图形批处理与逐动作增量 RTC 的计算组织差异，不能解释为纯粹的耦合方差效应。','', '## 2. 关键结果','', '| 方法 | 已认证/96 | 仅端点认证 | 平均副本 | 平均在线秒数 | 负端点差/端点样本 |','|---|---:|---:|---:|---:|---:|']
 for m,z in s['methods'].items():L.append(f"| {LABEL[m]} | {z['certified']}/96 | {z['endpoint_certified']} | {z['mean_calls']:.2f} | {z['mean_wall']:.4f} | {z['negative_endpoint_samples']}/{z['endpoint_samples']} |")
 L+=['','比值大于 1 表示分母方法成本较低；**包含未解决输出的成本**。','', '| 对比（分子/分母） | 墙钟比及调整区间 | 图级正/负 | 严格质量门 | 同质量效率通过 |','|---|---:|---:|---|---|']
 for z in s['contrasts']:
  q=z['wall_seconds'];L.append(f"| {LABEL[z['numerator']]}/{LABEL[z['denominator']]} | {q['ratio']:.5f} [{q['ci'][0]:.5f}, {q['ci'][1]:.5f}] | {q['positive_graphs']}/{q['negative_graphs']} | {z['quality_gate']} | {z['matched_quality_efficiency']} |")
 L+=['','### 分族结果（描述性墙钟比）','', '| 对比 | ER | WS | SBM | PA+闭合 |','|---|---:|---:|---:|---:|']
 for z in s['contrasts']:L.append('| '+z['name']+' | '+' | '.join(f"{z['wall_seconds']['families'][f]:.4f}" for f in c['families'])+' |')
 L+=['', '### 成本口径', '', f"RTC 筛选的预设几何比通过了效率门，但有筛选/无筛选的算术平均耗时分别为 {s['methods']['rtc_envelope']['mean_wall']:.5f}/{s['methods']['rtc']['mean_wall']:.5f} 秒。因此，这个通过结果不等于整个等权工作负载的总耗时下降。图级相对成本与算术平均成本衡量不同对象，两者同时报告。"]
 L+=['','## 3. 失败与不利结果','', '每种方法的未解决数量和所有区间均见上表。任何对比若严格质量门未通过，即使成本区间下界大于 1，也不构成同等认证质量下的效率优势。上一轮 94/96 及其失败门保留，不被本轮结果替换。独立有限样本评估不是已知最优值，不能拿来估计证书错误率。四种家族的相反方向不作隐藏或排除。','', '## 4. 对论文主张的影响','', '端点检验可应用于 RTC 的有符号端点差，因此不能声称端点筛选是图形耦合独有能力。图形耦合的独特性质仍是逐路径序及其非负宽度界；更紧的支持范围提供更强的分布无关充分界，而不证明每个实例的实际方差或耗时更小。新证明给出不提前放弃筛选时的有限预算充分条件；固定预留回退预算时另有成本收支条件。它们不自动覆盖当前带 futility 和剩余预算重分配的实现。受限黑盒检验中，非负零宽情形下界与已有上界在小容差下具有相同采样阶；有符号双点参考分布则给出平方阶下界。这不是实际 RTC 引擎或整个网络优化问题的下界。','', '## 5. 下一步','', '以公平四组对照决定经验定位，继续保留原始失败。候选重叠程度与分组压缩若继续研究，应另立新种子、锁定配置和预算，不复用本轮来事后挑选优势区域。']
 # Every empirical number interpolated into the article comes from summary.
 lineage=[]
 def walk(x,path):
  if isinstance(x,dict):
   for k,v in x.items():walk(v,path+'/'+str(k))
  elif isinstance(x,list):
   for k,v in enumerate(x):walk(v,path+'/'+str(k))
  elif isinstance(x,(int,float)) and not isinstance(x,bool):
   lineage.append(dict(quantity=path,value=x,summary='coupling_factorial/results/summary.json#'+path,source='coupling_factorial/results/context_results.csv',raw_mapping='coupling_factorial/results/accounting.csv',analysis='coupling_factorial/analyze.py',lock_sha256=s['lock_sha256']))
 walk(s,'')
 with (HERE/'results/number_lineage_complete.csv').open('w') as f:
  w=csv.DictWriter(f,list(lineage[0]));w.writeheader();w.writerows(lineage)
 matrix=[
  dict(claim='finite screening count',status='proved under stated conditions',evidence='coupling_factorial/theory/screen_cost.tex:thm:screen_power',scope='iid bounded endpoint contrasts, positive chord drift, no earlier futility'),
  dict(claim='expected screening count',status='proved under stated conditions',evidence='coupling_factorial/theory/screen_cost.tex:prop:screen_drift',scope='positive drift, uncapped screen; correct block-inspection bound'),
  dict(claim='copy-cost break-even',status='proved under stated conditions',evidence='coupling_factorial/theory/screen_cost.tex:prop:screen_break_even',scope='fixed reservation and fresh fallback; not implemented reallocation policy'),
  dict(claim='zero-width matching sampling order',status='proved in restricted oracle class',evidence='coupling_factorial/theory/screen_cost.tex:prop:screen_lower_bound',scope='distribution-free endpoint-only screens; not network-model optimality'),
  dict(claim='signed-class quadratic lower bound',status='proved in restricted oracle class',evidence='coupling_factorial/theory/screen_cost.tex:eq:signed_screen_lower_bound',scope='symmetric two-point reference; not a lower bound for actual RTC'),
  dict(claim='implicit/adaptive action regions',status='proved, not implemented',evidence='coupling_factorial/theory/screen_cost.tex:cor:implicit_region',scope='fresh tapes after proposals, predictable summable risk allocations')]
 for i,z in enumerate(s['contrasts']):
  matrix.append(dict(claim=z['name']+' matched-certified-quality cost',status='confirmed on locked cohort' if z['matched_quality_efficiency'] else 'not confirmed',evidence='coupling_factorial/results/summary.json#/contrasts/'+str(i),scope='32 new graphs, fixed eight-action region, all queries certified and adjusted interval gate required'))
 with (HERE/'results/claim_evidence_matrix.csv').open('w') as f:
  w=csv.DictWriter(f,list(matrix[0]));w.writeheader();w.writerows(matrix)
 (HERE/'reports/factorial_report.md').write_text('\n'.join(L)+'\n')
if __name__=='__main__':main()
