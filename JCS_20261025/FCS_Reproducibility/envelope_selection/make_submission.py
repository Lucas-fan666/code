from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def main():
    s=json.loads((ROOT/'envelope_selection/results/summary.json').read_text());c=next(x for x in s['contrasts'] if x['comparator']=='paired')
    out=ROOT/'submission';out.mkdir(exist_ok=True)
    result=f"The fresh 32-graph, 96-context study gives a graphical paired-race/envelope-first wall-time ratio of {c['wall_ratio']:.3f} [{c['ci_low']:.3f}, {c['ci_high']:.3f}] at the specified tolerance and capped budget."
    if c['efficiency_gate']:result+=' Both methods certify every context, meeting the prespecified efficiency criterion.'
    else:result+=' The strict efficiency criterion is not met; this is stated explicitly in the manuscript.'
    letter=f'''Dear Editors,

Please consider the research article "Exact Coupling and Certified Portfolio Selection in Higher-Order Processes with Memory" for Frontiers of Computer Science.

The paper addresses simulation-based set selection for recurrent network processes with continuous group memory. Its computer-science contribution is an exact ordered comparison framework and a decision procedure that uses its structure. We prove a compatible augmented-state order, extend comparison to nonnested actions through intersection/union envelopes, and show that predictable local batching preserves the full joint loss law and fresh-tape adaptive-search distribution.

The additional endpoint certificate uses two auxiliary controls to constrain candidate actions that have not individually been simulated. A paired fallback controls erroneous certified returns and explicitly reports unresolved outcomes. The concentration tools are established bounded-mean betting methods; the contribution is the model-proved auxiliary-order information and its algorithmic use. We do not claim a general new coupling principle or an approximation ratio for the unrestricted objective. {result}

The study also retains the earlier locked runtime and intervention comparisons, including unfavorable incremental-reaction-path and observed-topology outcomes. Full proofs, source code, locked configurations, raw losses, seed records and accounting checks accompany the manuscript and supplementary material. Public GitHub publication is deferred.

The author confirms that the manuscript is original and is not under consideration elsewhere, subject to reconfirmation at the time of journal submission. This research received no external funding. There are no competing interests. The manuscript discloses AI-assisted drafting, coding and mathematical examination; responsibility remains with the author.

Sincerely,
Junkai Fan
School of Business Administration, Northeastern University
Shenyang 110169, China
fanjk@mails.neu.edu.cn
'''
    (out/'cover_letter_draft.md').write_text(letter)
    (out/'highlights.md').write_text('''- An augmented order couples recurrent node states and relaxing signed memory exactly.
- Auxiliary intersection/union controls certify a finite portfolio without querying every action.
- A paired fallback controls erroneous certified returns under adaptive sampling.
- Full joint-law preservation separates computational acceleration from changes in decision quality.

These are text highlights. FCS requests a separate three-page PPT highlights file; no PowerPoint file is claimed by this archive.
''')
    (out/'submission_notes.md').write_text('''The complete research-class manuscript and supplementary PDF are in manuscript/. The source uses the official bundled fcs class. Figures are embedded vector PDF; editable exports for the additional figure are in the code archive.

Before submission, the author must reaffirm originality/exclusive submission and review all proofs, references and AI disclosure. Author: Junkai FAN; correspondence: fanjk@mails.neu.edu.cn; affiliation: School of Business Administration, Northeastern University, Shenyang 110169, China; no external funding.

No GitHub repository or permanent public DOI is asserted. FCS requests three-page PPT highlights separately; this delivery includes draft text only. No journal submission or external message has been sent.
''')
if __name__=='__main__':main()
