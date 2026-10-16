from dataclasses import dataclass, field
from collections.abc import Mapping
from datetime import datetime
from typing import Any
import yaml


GREEDY_PARAMS = {
    'temperature': 0.0, "max_tokens": 16384, "seed": 42,
    "top_p": 1.0,      # set to 1.0 to disable nucleus sampling
    "top_k": 1,        # choose the most likely token
    "repetition_penalty": 1.0,  # disable repetition penalty
    "length_penalty": 1.0,      # disable length penalty
    "no_repeat_ngram_size": 0,  # disable n-gram repetition penalty
}

@dataclass(frozen=True)
class LLMServerInfo:
    base_url: str = "https://uni-api.cstcloud.cn"
    api_key: str = "7868485c0ca1d66880fdb72e06b77ebfc6daf07faf61638e81e7a79adf7e309d"
    model: str = "minimax-m27"


@dataclass(frozen=True)
class ToolConfig:
    # Agent
    agent_info: LLMServerInfo = field(default_factory=LLMServerInfo)
    agent_max_tokens: int = 16384
    # General
    evaluation_date: datetime = field(default_factory=lambda: datetime.strptime("2026-06-30", "%Y-%m-%d"))
    # Sentence Transformer
    sbert_server_url: str = "http://172.18.36.90:8030"
    # external LLM
    llm_server_info: LLMServerInfo = field(default_factory=LLMServerInfo)
    fallback_llm_info: LLMServerInfo = field(default_factory=LLMServerInfo)
    sampling_params: Mapping[str, Any] = field(default_factory=lambda: GREEDY_PARAMS)
    request_concurrency: Mapping[str, int] = field(default_factory=dict)
    # citation parser
    grobid_url: str = "http://172.18.36.90:8070"
    grobid_num_workers: int = 10
    grobid_parse_mode: str = "casual"
    arxiv_source_parse_timeout: int = 90
    proxy_url: str = "http://localhost:7890"
    arxiv_proxy_url: str = "http://localhost:7890"
    # reference surveys
    reference_survey_search_limit: int = 20
    # factual correctness - reranking
    rerank_server_info: LLMServerInfo = field(default_factory=LLMServerInfo)
    rerank_n_documents: int = 5
    consistent_evidence_max_records: int = 0
    consistent_evidence_top_k: int = 8
    # topic coverage
    topic_weak_sim_threshold: float = 0.45
    topic_sim_threshold: float = 0.55
    topic_papers_search_limit: int = 10
    missing_topic_min_community_size: int = 3
    missing_topic_min_community_size_ratio: float = 0.01
    topic_coverage_search_limit: int = 10
    literature_pool_query_search_limit: int = 200
    literature_pool_neighbor_batch_size: int = 200
    literature_pool_neighbor_max_rounds: int = 2
    literature_pool_max_papers: int = 1000
    literature_pool_max_query_keywords: int = 6
    literature_pool_filter_keyword_count: int = 5
    literature_pool_filter_max_keyword_count: int = 20
    literature_pool_filter_keyword_method: str = "tfidf"
    literature_pool_use_llm_filter: bool = False
    literature_pool_use_sbert_rerank: bool = False
    literature_pool_filter_debug_path: str = ""
    literature_pool_relevance_batch_size: int = 50
    literature_pool_relevance_oversample_factor: int = 3
    missing_paper_top_k: int = 3
    missing_paper_judge_batch_size: int = 0
    missing_paper_use_llm_judge: bool = False
    missing_topic_top_k: int = 3
    missing_topic_llm_concurrency: int = 8
    missing_topic_resolutions: tuple[float, ...] = (0.5, 1.0, 2.0, 4.0, 8.0)
    missing_topic_representative_papers: int = 10
    new_paper_topic_similarity_threshold: float = 0.55
    new_paper_reference_overlap_threshold: float = 0.6
    citation_velocity_keep_ratio: float = 0.4
    minimum_reference_survey_citations: int = 10
    use_openalex_count_by_year: bool = True
    # fact check
    background_reference_similarity_threshold: float = 0.6
    mean_cov_weight: float = 0.7
    non_compat_punishment: float = 0.6
    confidence_threshold: float = 0.9
    evidence_fuzzy_min_token_length: int = 5
    evidence_ordered_min_matched_tokens: int = 5
    evidence_token_similarity_threshold: float = 0.8
    evidence_ordered_token_coverage_threshold: float = 0.8
    contribution_similarity_threshold: float = 0.65
    internal_consistency_sentence_ratio_threshold: float = 0.4
    internal_consistency_strategy: str = "parallel_unified"
    internal_consistency_conflict_batch_size: int = 120
    sentence_similarity_threshold: float = 0.6
    paragraph_similarity_threshold: float = 0.6
    redundancy_ngram: int = 10
    adequacy_thresholds_path: str = ""
    evidence_source_verification: bool = True
    no_evidence_output: bool = False
    # websearch
    websearch_url: str = "https://google.serper.dev/search"
    websearch_apikey: str = "6a58924ede5e53c3e3d72ef428236db7654b88ec"
    # openalex
    openalex_rate_limit_enabled: bool = True
    openalex_requests_per_second: float = 30
    openalex_api_keys: list[str] = field(default_factory=list)
    default_academic_search_engine: str = "semantic scholar"
    topn: int = 100
    semantic_scholar_api_key: str = ""
    semantic_scholar_retry_count: int = 5

    def is_openalex_only(self) -> bool:
        return self.default_academic_search_engine in ['openalex only', 'openalex_only', 'openalex-only']

    def use_semantic_scholar(self) -> bool:
        return not self.is_openalex_only()

    @classmethod
    def from_yaml(cls, config_path):
        with open(config_path) as f: config = yaml.safe_load(f)
        evaluation_date = config['general']['evaluation_date']
        if isinstance(evaluation_date, datetime):
            parsed_evaluation_date = evaluation_date
        else:
            parsed_evaluation_date = datetime.strptime(str(evaluation_date), "%Y-%m-%d")
        proxy_url = (
            config.get('proxy', {}).get('url')
            or config.get('general', {}).get('proxy_url')
            or config.get('citation_parser', {}).get('proxy_url')
            or config.get('citation_parser', {}).get('arxiv_proxy_url')
            or 'http://localhost:7890'
        )
        return cls(
            agent_info=LLMServerInfo(
                base_url=config['agent']['base_url'],
                api_key=config['agent']['api_key'],
                model=config['agent']['model'],
            ),
            agent_max_tokens=config['agent']['max_tokens'],
            evaluation_date=parsed_evaluation_date,
            llm_server_info=LLMServerInfo(
                base_url=config['external_llm']['base_url'],
                api_key=config['external_llm']['api_key'],
                model=config['external_llm']['model'],
            ),
            fallback_llm_info=LLMServerInfo(
                base_url=config.get('fallback_llm', {}).get('base_url', LLMServerInfo().base_url),
                api_key=config.get('fallback_llm', {}).get('api_key', LLMServerInfo().api_key),
                model=config.get('fallback_llm', {}).get('model', LLMServerInfo().model),
            ),
            request_concurrency=config.get('request_limits', {}) or {},
            sbert_server_url=config['sbert']['base_url'],
            grobid_url=config['citation_parser']['grobid_url'],
            grobid_parse_mode=config.get('citation_parser', {}).get('grobid_parse_mode', 'casual'),
            arxiv_source_parse_timeout=config.get('citation_parser', {}).get('arxiv_source_parse_timeout', 90),
            proxy_url=proxy_url,
            arxiv_proxy_url=proxy_url,
            rerank_server_info=LLMServerInfo(
                base_url=config['rerank']['base_url'],
                api_key=config['rerank']['api_key'],
                model=config['rerank']['model'],
            ),
            rerank_n_documents=config['rerank']['num_documents'],
            consistent_evidence_max_records=config.get('consistent', {}).get('evidence_max_records', 0),
            consistent_evidence_top_k=config.get('consistent', {}).get('evidence_top_k', 8),
            topic_papers_search_limit=config.get('topic_papers', {}).get('search_limit', 10),
            missing_topic_min_community_size=config.get('topic_papers', {}).get('missing_topic_min_community_size', 3),
            missing_topic_min_community_size_ratio=config.get('topic_papers', {}).get('missing_topic_min_community_size_ratio', 0.01),
            topic_coverage_search_limit=config.get('topic_coverage', {}).get('search_limit', 10),
            literature_pool_query_search_limit=config.get('literature_pool', {}).get('query_search_limit', 200),
            literature_pool_neighbor_batch_size=config.get('literature_pool', {}).get('neighbor_batch_size', 200),
            literature_pool_neighbor_max_rounds=config.get('literature_pool', {}).get('neighbor_max_rounds', 2),
            literature_pool_max_papers=config.get('literature_pool', {}).get('max_papers', 1000),
            literature_pool_max_query_keywords=config.get('literature_pool', {}).get('max_query_keywords', 6),
            literature_pool_filter_keyword_count=config.get('literature_pool', {}).get('filter_keyword_count', 5),
            literature_pool_filter_max_keyword_count=config.get('literature_pool', {}).get('filter_max_keyword_count', 20),
            literature_pool_filter_keyword_method=config.get('literature_pool', {}).get('filter_keyword_method', 'tfidf'),
            literature_pool_use_llm_filter=config.get('literature_pool', {}).get('use_llm_filter', False),
            literature_pool_use_sbert_rerank=config.get('literature_pool', {}).get('use_sbert_rerank', False),
            literature_pool_filter_debug_path=config.get('literature_pool', {}).get('filter_debug_path', ''),
            literature_pool_relevance_batch_size=config.get('literature_pool', {}).get('relevance_batch_size', 50),
            literature_pool_relevance_oversample_factor=config.get('literature_pool', {}).get('relevance_oversample_factor', 3),
            missing_paper_top_k=config.get('missing_papers', {}).get('top_k', 3),
            missing_paper_judge_batch_size=config.get('missing_papers', {}).get('judge_batch_size', 0),
            missing_paper_use_llm_judge=config.get('missing_papers', {}).get('use_llm_judge', False),
            missing_topic_top_k=config.get('topic_papers', {}).get('missing_topic_top_k', 3),
            missing_topic_llm_concurrency=config.get('topic_papers', {}).get('missing_topic_llm_concurrency', 8),
            missing_topic_resolutions=tuple(config.get('topic_papers', {}).get('missing_topic_resolutions', [0.5, 1.0, 2.0, 4.0, 8.0])),
            missing_topic_representative_papers=config.get('topic_papers', {}).get('missing_topic_representative_papers', 10),
            new_paper_topic_similarity_threshold=config.get('topic_coverage', {}).get('new_paper_topic_similarity_threshold', 0.55),
            adequacy_thresholds_path=config.get('adequacy_scoring', {}).get('thresholds_path', ''),
            background_reference_similarity_threshold=config.get('fact_check', {}).get(
                'background_reference_similarity_threshold',
                0.6,
            ),
            sentence_similarity_threshold=config['quality']['sentence_similarity_threshold'],
            paragraph_similarity_threshold=config['quality']['paragraph_similarity_threshold'],
            redundancy_ngram=config['quality']['redundancy_ngram'],
            evidence_source_verification=config.get('evaluation', {}).get('evidence_source_verification', True),
            evidence_fuzzy_min_token_length=config.get('evaluation', {}).get('evidence_fuzzy_min_token_length', 5),
            evidence_ordered_min_matched_tokens=config.get('evaluation', {}).get('evidence_ordered_min_matched_tokens', 6),
            evidence_token_similarity_threshold=config.get('evaluation', {}).get('evidence_token_similarity_threshold', 0.78),
            evidence_ordered_token_coverage_threshold=config.get('evaluation', {}).get('evidence_ordered_token_coverage_threshold', 0.85),
            no_evidence_output=config.get('evaluation', {}).get('no_evidence_output', False),
            websearch_url=config['websearch']['url'],
            websearch_apikey=config['websearch']['api_key'],
            openalex_rate_limit_enabled=config.get('openalex', {}).get('rate_limit_enabled', True),
            openalex_requests_per_second=config.get('openalex', {}).get('requests_per_second', 30.0),
            openalex_api_keys=config.get('openalex', {}).get('api_keys', []),
            topn=config.get('source_selection', {}).get('topn', 100),
            default_academic_search_engine=config.get('academic_search', {}).get(
                'default_engine',
                config.get('default_academic_search_engine', 'openalex'),
            ),
            semantic_scholar_api_key=config.get('semantic_scholar', {}).get('api_key', ''),
            semantic_scholar_retry_count=config.get('semantic_scholar', {}).get('retry_count', 5),
            reference_survey_search_limit=config.get('reference_survey', {}).get('search_limit', 20),
            internal_consistency_strategy=config.get('internal_consistency', {}).get('strategy', 'parallel_unified'),
            internal_consistency_conflict_batch_size=config.get('internal_consistency', {}).get('conflict_batch_size', 120),
        )
