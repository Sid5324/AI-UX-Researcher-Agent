import json

with open('final_uber_output.json', encoding='utf-16') as f:
    data = json.load(f)

md = '# Uber Onboarding Improvement: AI Agent Results\n\n'

if 'data_findings' in data:
    md += '## 1. Data Analysis (data_agent)\n'
    md += data['data_findings'].get('summary', '') + '\n\n'
    
if data and data.get('competitor_analysis'):
    md += '## 2. Competitor Analysis (competitor_agent)\n'
    swot = data['competitor_analysis'].get('swot_analysis', {})
    if isinstance(swot, dict):
        for k, v in swot.items():
            md += f'### {k.upper()}\n'
            for item in v:
                md += f'- **{item.get("factor", "")}**: {item.get("description", "")}\n'
    md += '\n'

if 'product_strategy' in data:
    md += '## 3. Product Strategy (prd_agent)\n'
    prd = data['product_strategy'].get('prd_document', '')
    md += prd + '\n\n'

if 'validation_results' in data:
    md += '## 4. Validation Plan (validation_agent)\n'
    val = data['validation_results']
    if isinstance(val, list) and len(val) > 0:
        for exp in val[0].get('experiment_configs', []):
            md += f'- **{exp.get("name", "")}**: {exp.get("hypothesis_alternative", "")}\n'
    md += '\n'

if 'design_specs' in data:
    md += '## 5. UI/UX Design Specs (ui_ux_agent)\n'
    ds = data['design_specs']
    md += '### Design System\n'
    md += '```json\n' + json.dumps(ds.get('design_system', {}).get('colors', {}), indent=2) + '\n```\n'
    md += '### Screens Hand-off\n'
    for screen in ds.get('screens', []):
        md += f'- **{screen.get("name")}** ({screen.get("viewport")})\n'

with open(r'C:\Users\Siddharth\.gemini\antigravity\brain\135fbf08-f4bd-43e7-b837-8fcb05686b1a\uber_goal_result.md', 'w', encoding='utf-8') as f:
    f.write(md)
