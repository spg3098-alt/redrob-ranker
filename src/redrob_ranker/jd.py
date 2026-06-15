"""
jd.py — The released job description, encoded as explicit, machine-readable
requirements.
"""

# --- Title taxonomy --------------------------------------------------------
CORE_TITLE_TERMS = [
    "machine learning engineer", "ml engineer", "ai engineer",
    "applied scientist", "applied ml", "research engineer",
    "nlp engineer", "search engineer", "ranking engineer",
    "recommendation", "recsys", "mlops engineer",
    "deep learning engineer", "ml scientist", "machine learning scientist",
]
DATA_SCIENCE_TERMS = ["data scientist", "ml researcher", "research scientist"]
ADJACENT_TECH_TERMS = [
    "data engineer", "analytics engineer", "backend engineer",
    "software engineer", "full stack", "platform engineer",
    "staff engineer", "principal engineer",
]
OTHER_TECH_TERMS = [
    "frontend", "mobile developer", "android", "ios", "devops",
    "cloud engineer", "qa engineer", "java developer", ".net",
    "web developer", "sre", "database administrator",
]

TITLE_SCORE = {
    "core": 1.00, "data_science": 0.82, "adjacent": 0.50,
    "other_tech": 0.22, "non_tech": 0.04,
}

# --- Skill concept groups --------------------------------------------------
SKILL_GROUPS = {
    "retrieval_embeddings": (1.00, [
        "embedding", "sentence-transformer", "sbert", "bge", "e5",
        "retrieval", "rag", "semantic search", "dense retrieval",
    ]),
    "vectordb_search": (1.00, [
        "faiss", "pinecone", "weaviate", "qdrant", "milvus", "opensearch",
        "elasticsearch", "bm25", "vector search", "hybrid search", "lucene", "solr",
    ]),
    "eval": (0.95, [
        "ndcg", "mrr", "map@", "a/b test", "ab test", "experimentation",
        "ranking metrics", "offline evaluation", "mlflow",
    ]),
    "ranking_recsys": (0.95, [
        "learning to rank", "ltr", "ranking", "recommendation", "recommender",
        "recsys", "collaborative filtering",
    ]),
    "ml_core": (0.65, [
        "machine learning", "deep learning", "pytorch", "tensorflow",
        "scikit", "xgboost", "lightgbm", "nlp", "natural language",
        "neural network", "classification", "regression",
    ]),
    "llm": (0.55, [
        "llm", "large language model", "fine-tuning", "lora", "qlora",
        "peft", "transformers", "hugging face", "huggingface", "bert",
    ]),
    "data_eng": (0.30, [
        "spark", "airflow", "kafka", "sql", "etl", "data pipeline",
        "snowflake", "dbt", "databricks",
    ]),
}

DOMAIN_MISMATCH_TERMS = [
    "image classification", "object detection", "segmentation", "gans",
    "computer vision", "opencv", "speech recognition", "tts", "asr",
    "robotics", "slam", "lidar", "pose estimation", "ocr",
]

CONSULTING_FIRMS = [
    "tcs", "tata consultancy", "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "tech mahindra", "hcl", "mindtree", "ltimindtree",
    "mphasis", "hexaware", "ibm services", "deloitte", "pwc",
]

PRODUCT_SIGNAL_TERMS = [
    "product company", "at scale", "real users", "production",
    "shipped", "deployed", "millions of", "recommendation system",
    "search system", "ranking system",
]

PREFERRED_CITIES = [
    "pune", "noida", "hyderabad", "mumbai", "delhi", "gurgaon", "gurugram",
    "ncr", "bengaluru", "bangalore",
]

FRAMEWORK_ENTHUSIAST_TERMS = ["langchain", "llamaindex", "autogpt", "crewai"]

# --- Eval-framework evidence (text scan) -----------------------------------
EVAL_TEXT_TERMS = [
    "ndcg", "mrr", "map@", "a/b test", "ab test", "ab testing",
    "offline evaluation", "online evaluation", "ranking evaluation",
    "offline-online", "ranking metrics", "evaluation framework",
    "recall@", "precision@", "recall at", "dcg",
]

# --- Must-have group coverage weights (sum to 1.0) -------------------------
# Replaces integer core_cov/4. Eval carries most weight — hardest to fake.
COVERAGE_WEIGHTS = {
    "eval":                  0.30,
    "retrieval_embeddings":  0.25,
    "ranking_recsys":        0.20,
    "vectordb_search":       0.15,
    "ml_core":               0.10,
}

# --- Cross-group skill redundancy correlation ------------------------------
# Candidates with both retrieval_embeddings AND vectordb_search skills were
# getting additive credit for what is partly the same capability.
SKILL_GROUP_CORR = {
    ("retrieval_embeddings", "vectordb_search"): 0.65,
    ("retrieval_embeddings", "ranking_recsys"):  0.45,
    ("vectordb_search",      "ranking_recsys"):  0.40,
    ("ml_core",              "llm"):             0.55,
    ("eval",                 "ranking_recsys"):  0.50,
}

JD_TEXT = (
    "Senior AI Engineer founding team. Own the intelligence layer: ranking, "
    "retrieval and matching systems deciding what recruiters see when they "
    "search candidates. Production experience with embeddings-based retrieval "
    "(sentence-transformers, BGE, E5), vector databases and hybrid search "
    "(FAISS, Pinecone, Weaviate, Qdrant, Milvus, Elasticsearch, OpenSearch), "
    "learning-to-rank, LLM fine-tuning, and rigorous evaluation of ranking "
    "systems with NDCG, MRR, MAP and A/B testing. Shipped end-to-end ranking, "
    "search or recommendation systems to real users at scale at product "
    "companies, not pure research and not pure services. Strong Python and "
    "code quality. Scrappy product-engineering attitude over pure research."
)
