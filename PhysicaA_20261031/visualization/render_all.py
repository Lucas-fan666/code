"""Redraw every cited figure from saved outputs without running simulations.

Run from the release root: python3 visualization/render_all.py
"""
from pathlib import Path
import hashlib
import json
import re
import shutil

from theme import R, M, OUT, REGISTER, INK, BLUE, TEAL, RED, GOLD, PURPLE, GREY, RUST
import render_physics
import render_supplement

SOURCES = {
 'mechanism_reference_vector': ['reproducibility/publication_assets/tools/draw_reference_vector.py'],
 'physicaA_memory_mediation': ['reproducibility/physicaA_physics/results/counterfactual_summary.csv'],
 'physicaA_contacts': ['reproducibility/physicaA_physics/results/counterfactual_8.npz', 'reproducibility/physicaA_physics/results/counterfactual_9.npz'],
 'memory_response': ['reproducibility/physica_a_revision/results'],
 'memory_timescales': ['reproducibility/response_extension/results'],
 'natural_memory': ['reproducibility/natural_memory/results'],
 'physicaA_triangle_crossover': ['reproducibility/physicaA_physics/results/triangle.npz'],
 'bound_diagnostics': ['reproducibility/response_extension/results/bounds.csv'],
 'physicaA_precision': ['reproducibility/physicaA_precision/results/precision_publication_curves.csv'],
 'adaptive_comparison': ['reproducibility/adaptive_screening/results'],
 'candidate_pool_sensitivity': ['reproducibility/publication_assets/visualization/data/wp4_primary_endpoints.csv'],
 'grid': ['reproducibility/publication_assets/visualization/data/wp2_all_cells_forest_data.csv'],
 'baselines': ['reproducibility/visual_style_inputs/retained_results/WP5/wp5_summary.json'],
 'complete_search_mechanisms': ['reproducibility/end_to_end_search/results/mechanism_summary.json'],
 'portfolio_efficiency': ['reproducibility/results/runtime_summary.json'],
 'portfolio_scaling': ['reproducibility/results/scaling'],
 'envelope_selection': ['reproducibility/envelope_selection/results'],
 'factorial_selection': ['reproducibility/coupling_factorial/results'],
 'witness_comparison': ['reproducibility/witness_selection/results'],
 'complete_search_comparison': ['reproducibility/end_to_end_search/results/summary.json'],
 'optimized_replay': ['reproducibility/publication_revision/optimized_replay/results'],
 'scalability_pool': ['reproducibility/publication_assets/visualization/data/wp4_trajectory_timing_raw.csv'],
 'original_memory_contexts': ['reproducibility/physica_a_revision/results'],
 'memory_contexts': ['reproducibility/response_extension/results'],
 'cost_accuracy': ['reproducibility/threshold_sensitivity/inputs/cost_quality_curves.csv'],
 'physicaA_runtime_summary': ['reproducibility/publication_assets/visualization/data/runtime_64_graph_costs.csv', 'reproducibility/publication_assets/visualization/data/runtime_32_graph_costs.csv'],
 'confirmation': ['reproducibility/publication_assets/visualization/data/wp2_family_cell_contrasts.csv', 'reproducibility/publication_assets/visualization/data/WP2_summary.json'],
 'physicaA_triangle_ensemble': ['reproducibility/physicaA_physics/results/triangle.npz'],
 'physicaA_hyperedge4': ['reproducibility/physicaA_physics/results/hyperedge4.npz'],
}


def cited_figures():
    figures = []
    for doc, designation in [('main', 'Main'), ('supplement', 'Supplement')]:
        tex = (M / (doc + '.tex')).read_text()
        blocks = re.findall(r'\\begin\{figure\*?\}.*?\\end\{figure\*?\}', tex, re.S)
        for i, block in enumerate(blocks, 1):
            files = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', block)
            assert len(files) == 1, (doc, i, files)
            name = Path(files[0]).stem
            label = re.search(r'\\label\{([^}]+)\}', block)[1]
            figures.append(dict(document=designation, number=i, name=name, label=label))
    assert sum(x['document'] == 'Main' for x in figures) == 9
    assert len(figures) == len({x['name'] for x in figures}) == 29
    return figures


def inventory():
    records = []
    for fig in cited_figures():
        name = fig['name']
        sources = SOURCES[name]
        for source in sources:
            assert (R / source).exists(), (name, source)
        files = {}
        for ext in ['pdf', 'svg', 'png']:
            p = OUT / (name + '.' + ext)
            assert p.is_file() and p.stat().st_size > 1000, p
            files[ext] = dict(path=str(p.relative_to(R)), sha256=hashlib.sha256(p.read_bytes()).hexdigest(), bytes=p.stat().st_size)
        shutil.copy2(OUT / (name + '.svg'), M / (name + '.svg'))
        records.append({**fig, **REGISTER.get(name, {}), 'sources':sources, 'files':files, 'new_simulation':False, 'new_confirmatory_inference':False})
    report = dict(descriptive_display_updates=['Figure 2 adds all eight graph-level memory gains; Figure 3 adds one conditional Monte Carlo standard error from saved replications.'], main_figures=9, supplementary_figures=20, total=29, palette=dict(ink=INK, rumor=RED, correction=TEAL, inactive=GREY, target=GOLD, RTC=BLUE, thinning=RUST, antithetic=PURPLE), figures=records)
    p = R / 'reports/visual_revision/figure_inventory.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report, indent=2))
    return report


def main():
    render_physics.main()
    render_supplement.main()
    report = inventory()
    print(f"Redrew {report['main_figures']} main and {report['supplementary_figures']} supplementary figures from saved outputs.")


if __name__ == '__main__':
    main()
