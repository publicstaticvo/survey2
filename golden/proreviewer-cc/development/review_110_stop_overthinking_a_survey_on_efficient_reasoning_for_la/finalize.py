import json

with open('review_log.json', 'r', encoding='utf-8') as f:
    log = json.load(f)

# Add outline points
log['outline'] = [
    {
        'section': 'Strengths',
        'content': "First structured survey on efficient reasoning for LLMs with comprehensive taxonomy covering model-based, output-based, and input-prompt-based approaches. Clear organization with good use of comparison tables.",
        'claims': ['C1', 'C3'],
        'notes': ['N1', 'N2']
    },
    {
        'section': 'Strengths',
        'content': "Well-structured taxonomy (Figure 3) that clearly categorizes ~60+ methods across three main categories with detailed comparison tables. Good coverage of both RL-based and SFT-based approaches for efficient reasoning.",
        'claims': ['C3', 'C4'],
        'notes': ['N2']
    },
    {
        'section': 'Weaknesses',
        'content': "Many empirical claims lack quantification. RL methods are claimed to achieve 'nearly lossless alignment' without specific accuracy degradation numbers (C5). LIMO claims outperforming '100,000+ examples' without naming baselines (C6). s1-32B 'exceeds o1-preview' without accuracy scores (C7). Quantization claim lacks specific bit-widths and metrics (C8).",
        'claims': ['C2', 'C5', 'C6', 'C7', 'C8'],
        'notes': []
    },
    {
        'section': 'Weaknesses',
        'content': "No standardized evaluation framework or benchmark leaderboard exists. Paper acknowledges (§8.2) that comparing methods is difficult due to varying architectures, inconsistent datasets, and training resource disparities. This limits the survey's utility for practitioners.",
        'claims': [],
        'questions': ['Q4'],
        'notes': []
    },
    {
        'section': 'Weaknesses',
        'content': "Safety-efficiency tradeoff is inadequately addressed. While §8.2 mentions H-CoT attacks that exploit reasoning models, the survey does not provide comprehensive analysis of how efficient reasoning affects safety properties.",
        'claims': ['C5'],
        'questions': ['Q3'],
        'notes': []
    },
    {
        'section': 'Summary',
        'content': 'This survey provides the first comprehensive overview of efficient reasoning techniques for LLMs, organizing ~60+ methods into a clear taxonomy. The paper is well-structured with good illustrations and comparison tables. However, many empirical claims are understated without quantitative support, and the lack of standardized benchmarks limits comparative analysis.',
        'claims': ['C1', 'C3', 'C4'],
        'questions': [],
        'notes': ['N1', 'N2']
    },
    {
        'section': 'overall_score',
        'content': '3'
    }
]

with open('review_log.json', 'w', encoding='utf-8') as f:
    json.dump(log, f, indent=2, ensure_ascii=False)

print('Added outline')
print(str(len(log['outline'])) + ' outline points')