import json
import os

try:
    with open('final_uber_output.json', encoding='utf-16') as f:
        data = json.load(f)
except UnicodeError:
    with open('final_uber_output.json', encoding='utf-8') as f:
        data = json.load(f)

# 1. Data Agent
if data.get('data_findings'):
    with open('1_data_findings.md', 'w', encoding='utf-8') as f:
        f.write('# Data Agent Findings\n\n')
        f.write(data['data_findings'].get('summary', ''))
        f.write('\n\n## Insights\n')
        for i in data['data_findings'].get('data_collected', {}).get('insights', []):
            f.write(f'- {i}\n')

# 2. Competitor Agent
if data.get('competitor_analysis'):
    with open('2_competitor_analysis.md', 'w', encoding='utf-8') as f:
        f.write('# Competitor Analysis\n\n')
        for k, v in data['competitor_analysis'].get('swot_analysis', {}).items():
            f.write(f'## {k.upper()}\n')
            if isinstance(v, list):
                for item in v:
                    f.write(f'- **{item.get("factor", "")}**: {item.get("description", "")}\n')

# 3. PRD Agent
if data.get('product_strategy'):
    with open('3_product_strategy.md', 'w', encoding='utf-8') as f:
        f.write(data['product_strategy'].get('prd_document', '# Product Strategy\nNo PRD generated.'))

# 4. Validation Agent
if data.get('validation_results'):
    with open('4_validation_plan.md', 'w', encoding='utf-8') as f:
        f.write('# Validation & Experiment Plan\n\n')
        val = data['validation_results']
        if isinstance(val, list) and len(val) > 0:
            for exp in val[0].get('experiment_configs', []):
                f.write(f"### {exp.get('name', 'Experiment')}\n")
                f.write(f"- **Null Hypothesis**: {exp.get('hypothesis_null', '')}\n")
                f.write(f"- **Alt Hypothesis**: {exp.get('hypothesis_alternative', '')}\n")
                f.write(f"- **Metric**: {exp.get('primary_metric', '')}\n\n")

# 5. UI/UX Agent
if data.get('design_specs'):
    with open('5_design_specs.md', 'w', encoding='utf-8') as f:
        f.write('# UI/UX Design System & Specs\n\n')
        ds = data['design_specs']
        f.write('## Design Tokens\n```json\n')
        f.write(json.dumps(ds.get('design_system', {}).get('colors', {}), indent=2))
        f.write('\n```\n\n## Screens Required\n')
        for screen in ds.get('screens', []):
            f.write(f"- **{screen.get('name')}** (Screen ID: {screen.get('screen_id')})\n")
        
        f.write('\n## Accessibility Audit\n')
        f.write(f"- Level: {ds.get('accessibility_audit', {}).get('wcag_level')}\n")
        f.write(f"- Score: {ds.get('accessibility_audit', {}).get('compliance_score')}\n")

print("Successfully generated all 5 markdown deliverables.")
