# DEV RADAR --- QUALITY SERVICE DEVELOPMENT PROMPT

## 0. ROLE

You are a **Senior AI/ML Engineer + Backend Engineer + MLOps Engineer**
responsible for extending the existing `services/QualityService` of the
**DevRadar** ecosystem.

Your task is **NOT to rewrite the existing QualityService from
scratch**.

You must first inspect the existing implementation, preserve working
components, identify gaps, then incrementally implement the AI/ML and
production capabilities described below.

The implementation must be production-oriented, testable, explainable,
and compatible with the current DevRadar architecture.

------------------------------------------------------------------------

# 1. EXISTING SYSTEM --- DO NOT BREAK IT

The current QualityService is a Python 3.12 + FastAPI microservice using
a Pipeline Pattern.

Current technologies:

-   Python 3.12
-   FastAPI
-   Uvicorn
-   Pydantic v2 Settings
-   Regex
-   emoji
-   pyahocorasick
-   underthesea
-   scikit-learn
-   FastText
-   MongoDB Atlas + `motor`
-   Elasticsearch
-   Docker

Current pipeline:

``` text
Raw Content
    ↓
Content Cleaner & Protection
    ↓
Text Normalization
    ↓
Word Segmentation
    ↓
ML Classifiers
    ↓
Rule Engine
    ↓
Quality Scorer
    ↓
QualityResult
    ↓
MongoDB
```

Existing preprocessing includes:

-   Code block / inline code protection
-   URL protection
-   HTML removal
-   Whitespace normalization
-   Emoji demojization
-   Teencode / typo / abbreviation normalization
-   Technology terminology normalization
-   Aho-Corasick lookup
-   Elasticsearch fuzzy matching fallback
-   Vietnamese word segmentation using Underthesea

Existing ML capabilities:

-   IT domain classification:
    -   `is_it`
    -   `it_probability`
    -   currently TF-IDF + Logistic Regression
-   Safety classification:
    -   `safe`
    -   `suspicious`
    -   `toxic`
    -   currently FastText
-   Heuristic keyword fallback when model files are unavailable

Existing rules:

-   `LengthRule`
-   `SpamRule`
-   `EmojiRule`
-   `StructureRule`
-   `CodeRatioRule`

Existing scoring:

``` text
Relevance       25%
Readability     20%
Structure       20%
Safety          20%
Content Quality 15%
```

Existing score classes:

``` text
excellent >= 90
good      >= 75
average   >= 50
poor      < 50
```

Existing API:

``` http
POST /api/v1/quality/analyze
GET  /api/v1/quality/health
```

Existing persistence:

``` text
MongoDB
database: quality
collection: quality_results
```

Existing test suite:

``` text
tests/
```

The current implementation and its capabilities are documented in the
supplied QualityService specification. Preserve these capabilities
unless a change is explicitly required by this prompt.

------------------------------------------------------------------------

# 2. PRIMARY OBJECTIVE

Extend QualityService into a complete:

> **AI-powered Content Quality + Safety + Semantic Intelligence + User
> Reputation Service**

The service must provide four major capabilities:

1.  **Content Intelligence**
2.  **Semantic Vector Intelligence**
3.  **User Quality / Reputation**
4.  **Continuous Model Improvement**

The final architecture should be:

``` text
                         QUALITY SERVICE
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       Content AI        Semantic AI       User AI
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                        Quality Engine
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
             Content Score          User Score
                    │                     │
                    └──────────┬──────────┘
                               ▼
                       Rank / Promotion
                               │
                               ▼
                        MLOps Feedback Loop
```

------------------------------------------------------------------------

# 3. CORE REQUIREMENTS

## 3.1 Content Health Classification

The system must determine whether content is:

-   Safe
-   Suspicious
-   Toxic
-   Spam
-   Harassment
-   Hate / abusive content
-   Sexual / inappropriate content
-   Violent content
-   Scam / malicious solicitation where detectable

Do not force all safety concepts into one hard-coded keyword list.

The ML system should support multi-label classification where
appropriate.

Example:

``` json
{
  "safety": {
    "safe": 0.97,
    "toxic": 0.01,
    "spam": 0.01,
    "harassment": 0.01
  }
}
```

The system must still maintain the existing heuristic fallback for
resilience.

------------------------------------------------------------------------

# 4. IT RELEVANCE CLASSIFICATION

The system must determine:

``` text
IT
NON_IT
UNCERTAIN
```

Additionally classify IT content into semantic technology domains where
confidence is sufficient:

``` text
Programming
Backend
Frontend
Mobile
DevOps
Cloud
Database
AI/ML
Data Engineering
Cybersecurity
Software Architecture
Testing
Embedded
Networking
Other IT
```

Example:

``` json
{
  "it_relevance": {
    "label": "IT",
    "probability": 0.97
  },
  "domain": {
    "label": "DEVOPS",
    "confidence": 0.91
  }
}
```

Do not rely only on manually hard-coded technology keywords.

Keywords may be used as auxiliary features, but semantic understanding
must eventually come from trained models.

------------------------------------------------------------------------

# 5. MODEL STRATEGY

## 5.1 No Third-Party AI API

The runtime inference path MUST NOT call:

-   OpenAI API
-   Gemini API
-   Claude API
-   Any external LLM API
-   Any third-party hosted inference API

Models must run locally inside the QualityService infrastructure.

Acceptable approach:

``` text
Open pretrained model
        ↓
DevRadar dataset
        ↓
Fine-tuning
        ↓
DevRadar model artifact
        ↓
Local inference
```

Do NOT train a large Transformer from random initialization unless there
is a strong technical justification.

Use pretrained open-source models as the initialization point and
fine-tune them using DevRadar-owned datasets.

------------------------------------------------------------------------

# 6. CONTENT MODEL ARCHITECTURE

Prefer a shared encoder with multiple classification heads when
technically appropriate:

``` text
                    Input Text
                        │
                        ▼
                Transformer Encoder
                        │
             ┌──────────┼──────────┐
             ▼          ▼          ▼
         IT Head    Safety Head   Domain Head
             │          │          │
             ▼          ▼          ▼
          IT Prob.   Safety Prob. Domain Prob.
```

Possible model families:

-   XLM-R
-   multilingual BERT
-   another suitable multilingual encoder
-   Sentence Transformers for semantic embeddings

Select the model based on:

-   Vietnamese quality
-   English quality
-   IT terminology handling
-   model size
-   inference latency
-   available CPU/GPU
-   memory usage

Do not blindly choose the largest model.

------------------------------------------------------------------------

# 7. DATASET REQUIREMENTS

Create a clear dataset schema.

Example:

``` json
{
  "text": "How can I optimize PostgreSQL indexes?",
  "language": "en",
  "is_it": true,
  "domain": "database",
  "safety": {
    "safe": true,
    "toxic": false,
    "spam": false
  }
}
```

Dataset must support:

-   Vietnamese
-   English
-   mixed Vietnamese-English IT terminology
-   code-containing content
-   short posts
-   long technical articles
-   comments
-   noisy social/community language
-   teencode
-   typo
-   abbreviations

Split datasets into:

``` text
train
validation
test
```

Never evaluate the model only on training data.

Prevent data leakage between splits.

------------------------------------------------------------------------

# 8. CODE-AWARE NLP

The existing cleaner protects code blocks and URLs.

Preserve this behavior.

Improve the system so code becomes a meaningful signal instead of being
treated as ordinary natural language.

Extract:

``` text
code_blocks
inline_code
declared_language
detected_language
code_ratio
technical_terms
```

Example:

``` json
{
  "code_analysis": {
    "has_code": true,
    "declared_language": "python",
    "detected_language": "python",
    "code_ratio": 0.31
  }
}
```

Do not delete source code before semantic analysis.

Use code presence and programming-language evidence as features for IT
relevance.

------------------------------------------------------------------------

# 9. SEMANTIC EMBEDDING

Introduce an embedding layer.

Pipeline:

``` text
Normalized Content
        ↓
Embedding Model
        ↓
Dense Vector
        ↓
Vector Index
```

The embedding model must produce a fixed-dimensional vector.

Example:

``` text
768-dimensional vector
```

The exact dimension must depend on the selected model.

Do not hard-code `768` if the chosen model uses another dimension.

------------------------------------------------------------------------

# 10. VECTOR INTELLIGENCE

Use vector representation for:

### 10.1 Semantic Similarity

Find semantically similar:

-   posts
-   comments
-   articles
-   questions
-   technical discussions

### 10.2 Content Clustering

Automatically discover semantic groups such as:

``` text
Backend
    ├── .NET
    ├── Node.js
    ├── Java
    └── Python

DevOps
    ├── Docker
    ├── Kubernetes
    └── CI/CD

AI
    ├── NLP
    ├── Computer Vision
    └── LLM
```

Do not require all clusters to be hard-coded.

Use clustering algorithms such as:

-   HDBSCAN
-   K-Means
-   other appropriate algorithms

Use dimensionality reduction such as PCA/UMAP only where useful for
clustering, visualization, or analysis.

------------------------------------------------------------------------

# 11. VECTOR DATABASE / INDEX

For the first implementation, FAISS is acceptable for local vector
indexing.

Architecture:

``` text
Embedding
   ↓
Vector
   ↓
FAISS Index
   ↓
Similarity / Search / Clustering
```

The implementation must abstract the vector store:

``` python
class VectorStore:
    def add(...)
    def search(...)
    def delete(...)
    def rebuild(...)
```

This allows future migration to another vector database without
rewriting business logic.

Persist and version the vector index.

Do not rebuild the entire index for every request.

------------------------------------------------------------------------

# 12. TECHNOLOGY / TAG EXTRACTION

Add automatic technology extraction.

Example input:

``` text
I built a FastAPI service with Redis and Docker.
```

Expected:

``` json
{
  "suggested_tags": [
    "FastAPI",
    "Redis",
    "Docker"
  ]
}
```

Tags should be derived from:

-   semantic model
-   normalized technology dictionary
-   code-language detection
-   known technology entities
-   context

Do not make the entire feature dependent on regex.

Return confidence where possible.

------------------------------------------------------------------------

# 13. CONTENT QUALITY SCORE

Preserve the existing scoring engine, but refactor it into a
configurable weighted scoring system.

Current baseline:

``` text
Relevance       25%
Readability     20%
Structure       20%
Safety          20%
Content Quality 15%
```

Do not silently remove these dimensions.

Create a configurable weighting system:

``` yaml
weights:
  relevance: 0.25
  readability: 0.20
  structure: 0.20
  safety: 0.20
  content_quality: 0.15
```

Weights must be validated to sum to 1.

Allow future experiments without changing business logic.

------------------------------------------------------------------------

# 14. EXTENDED CONTENT QUALITY FEATURES

Add or prepare features for:

``` text
IT Relevance
Safety
Readability
Structure
Technical Depth
Semantic Coherence
Specificity
Code Quality Signals
Spam Probability
Duplicate Probability
Community Feedback
```

Example conceptual score:

``` text
QualityScore =
    relevance
  + safety
  + readability
  + structure
  + technical_depth
  + semantic_quality
  + anti_spam
```

Normalize every feature to:

``` text
0.0 → 1.0
```

before applying weights.

The final score remains:

``` text
0 → 100
```

------------------------------------------------------------------------

# 15. TECHNICAL DEPTH

Implement a technical-depth signal.

Do NOT define technical depth simply as text length.

Possible features:

``` text
technical terminology
specificity
problem/solution structure
code presence
explanation quality
concept relationships
semantic coherence
technical vocabulary density
```

Example:

``` text
"Python is good."

Technical depth ≈ low
```

versus:

``` text
"Python's GIL limits CPU-bound threading. For CPU-intensive workloads,
multiprocessing or native extensions can be used..."
```

Technical depth ≈ high

The implementation should remain explainable.

------------------------------------------------------------------------

# 16. DUPLICATE / PLAGIARISM DETECTION

Implement two complementary levels.

### Level 1 --- lexical similarity

Use:

-   MinHash
-   SimHash
-   token shingles
-   Jaccard similarity

### Level 2 --- semantic similarity

Use:

``` text
Embedding A
     ↕
Embedding B
     ↓
Cosine similarity
```

The system should distinguish:

``` text
exact duplicate
near duplicate
semantically similar
original
```

Avoid flagging all semantically similar technical posts as plagiarism.

Similarity is evidence, not proof.

------------------------------------------------------------------------

# 17. USER QUALITY MODEL

Add user-level quality analytics.

Do NOT calculate:

``` text
user_score = average(post_scores)
```

only.

Build a user feature vector.

Example:

``` json
{
  "content_quality": 0.91,
  "technical_contribution": 0.88,
  "helpfulness": 0.93,
  "community_trust": 0.86,
  "consistency": 0.82,
  "activity": 0.72,
  "toxicity": 0.01,
  "spam": 0.02,
  "moderation_penalty": 0.00
}
```

------------------------------------------------------------------------

# 18. USER SCORE

Implement a configurable reputation formula.

Baseline example:

``` text
UserScore =
    0.25 × ContentQuality
  + 0.20 × TechnicalContribution
  + 0.15 × Helpfulness
  + 0.15 × CommunityTrust
  + 0.10 × Consistency
  + 0.10 × Activity
  + 0.05 × ProfileCompleteness
  - Penalty
```

Normalize to:

``` text
0 → 1000
```

Do not allow activity alone to dominate the score.

The system must be resistant to spam farming.

------------------------------------------------------------------------

# 19. USER BEHAVIOR FEATURES

Collect time-aware features such as:

``` text
posts_count
comments_count
average_content_quality
median_content_quality
technical_depth
helpful_votes
accepted_answers
positive_feedback
negative_feedback
spam_count
toxic_count
moderation_actions
activity_consistency
account_age
```

Prefer rolling windows:

``` text
7 days
30 days
90 days
all-time
```

This prevents old behavior from permanently dominating current
reputation.

------------------------------------------------------------------------

# 20. ANTI-GAMING

The scoring system must resist:

-   spam posting
-   repeated comments
-   self-voting
-   vote manipulation
-   low-value high-frequency activity
-   copy/paste content
-   toxic behavior followed by mass activity
-   artificially generated engagement

Introduce:

``` text
rate limits
diminishing returns
duplicate penalties
trust-weighted feedback
behavior consistency
moderation penalties
```

Example:

The 100th low-quality comment must contribute substantially less than
the first high-quality contribution.

------------------------------------------------------------------------

# 21. USER RANK / LEVEL SYSTEM

Create a configurable rank system.

Example:

``` text
0–99       Newcomer
100–249    Contributor
250–449    Developer
450–649    Expert
650–799    Senior
800–899    Mentor
900–1000   Community Leader
```

Do not hard-code these values in business logic.

Use configuration.

------------------------------------------------------------------------

# 22. AUTOMATIC PROMOTION

Promotion must require more than score.

Example:

``` text
User Score
    +
Minimum Activity
    +
Quality Consistency
    +
No serious violations
    +
Minimum observation period
    ↓
Promotion Engine
```

Example:

``` json
{
  "eligible": false,
  "current_level": "Expert",
  "next_level": "Senior",
  "missing_requirements": [
    "30-day quality consistency"
  ]
}
```

The system must explain why a user was or was not promoted.

------------------------------------------------------------------------

# 23. EXPLAINABILITY

Every important score should be explainable.

Content:

``` json
{
  "quality_score": 87.4,
  "score_breakdown": {
    "relevance": 0.96,
    "safety": 0.99,
    "readability": 0.81,
    "structure": 0.84,
    "technical_depth": 0.79
  }
}
```

User:

``` json
{
  "score": 824,
  "breakdown": {
    "content_quality": 0.91,
    "technical_contribution": 0.88,
    "helpfulness": 0.93,
    "community_trust": 0.86
  },
  "penalties": {
    "spam": 12,
    "toxicity": 8
  }
}
```

Do not return only a black-box number.

------------------------------------------------------------------------

# 24. ACTIVE LEARNING

Introduce uncertainty-based active learning.

Example:

``` text
IT probability = 0.51
NON_IT probability = 0.49
```

This is an uncertain sample.

Send it to:

``` text
Human Review Queue
```

After labeling:

``` text
Human Label
    ↓
Training Dataset
    ↓
Retraining
```

Prioritize samples with:

-   low confidence
-   disagreement between models
-   disagreement between rules and model
-   high production impact
-   new vocabulary
-   new technology terminology

------------------------------------------------------------------------

# 25. CONTINUOUS TRAINING

Do not let the production model train directly from raw user activity.

Correct pipeline:

``` text
Production Data
      ↓
Candidate Samples
      ↓
Validation / Cleaning
      ↓
Human Labeling
      ↓
Versioned Dataset
      ↓
Training
      ↓
Validation
      ↓
Evaluation
      ↓
Model Comparison
      ↓
Model Registry
      ↓
Deployment
```

Never automatically replace a production model just because a new model
was trained.

The new model must outperform or satisfy predefined acceptance criteria.

------------------------------------------------------------------------

# 26. MODEL EVALUATION

For classifiers, report at minimum:

``` text
Accuracy
Precision
Recall
F1
Confusion Matrix
```

For imbalanced safety classification, prioritize:

``` text
Macro F1
Per-class Precision
Per-class Recall
```

For embedding:

``` text
Semantic similarity evaluation
Clustering quality
Retrieval precision@k
```

For user scoring:

``` text
Correlation with trusted human evaluation
Rank stability
Promotion precision
Promotion false-positive rate
```

Store evaluation results per model version.

------------------------------------------------------------------------

# 27. MODEL VERSIONING

Every trained model must have:

``` text
model_name
version
training_dataset_version
training_date
metrics
configuration
framework_version
tokenizer_version
```

Example:

``` text
it-classifier/
  v1.0.0/
  v1.1.0/

safety-classifier/
  v1.0.0/

embedding-model/
  v1.0.0/
```

Do not overwrite production models blindly.

------------------------------------------------------------------------

# 28. MLOPS

Introduce:

-   MLflow for experiment tracking / model registry
-   DVC or equivalent dataset versioning
-   Git for code
-   Docker for reproducible environments
-   GitHub Actions for CI
-   optional scheduled retraining

Recommended lifecycle:

``` text
Dataset
  ↓
Experiment
  ↓
Training
  ↓
Evaluation
  ↓
MLflow
  ↓
Candidate Model
  ↓
Approval
  ↓
Production
```

------------------------------------------------------------------------

# 29. BATCH / ASYNC PROCESSING

Preserve the synchronous API:

``` http
POST /api/v1/quality/analyze
```

Add:

``` http
POST /api/v1/quality/analyze-batch
```

For large-scale processing, support asynchronous jobs through one
suitable queue:

-   Redis Streams
-   RabbitMQ
-   Kafka

Do not introduce all three.

Select one based on existing DevRadar infrastructure.

Example:

``` text
Crawler
   ↓
Queue
   ↓
Quality Worker
   ↓
AI Pipeline
   ↓
MongoDB
```

The API should return a job identifier for long-running batches.

------------------------------------------------------------------------

# 30. CACHING

Use Redis or LRU caching where beneficial.

Cache:

-   repeated text normalization
-   embeddings
-   frequent terminology lookups
-   duplicate similarity calculations
-   repeated content analysis where content hash matches

Use a stable content hash.

Never cache unsafe mutable user state indefinitely.

------------------------------------------------------------------------

# 31. DYNAMIC DICTIONARY

Move hard-coded dictionaries out of Python source code.

Support:

``` text
JSON
YAML
MongoDB
```

Dictionary categories:

``` text
teencode
typo
abbreviation
technology_alias
technology_name
domain_term
```

Example:

``` json
{
  "dotnet": ".NET",
  "js": "JavaScript",
  "ko": "không",
  "mik": "mình"
}
```

The system should be able to update terminology without redeploying
application code.

Add dictionary versioning.

------------------------------------------------------------------------

# 32. API DESIGN

Maintain backward compatibility.

Existing:

``` http
POST /api/v1/quality/analyze
GET  /api/v1/quality/health
```

Add APIs such as:

``` http
POST /api/v1/quality/analyze-batch

POST /api/v1/quality/embedding

POST /api/v1/quality/similarity

POST /api/v1/quality/duplicate-check

GET /api/v1/quality/users/{user_id}

GET /api/v1/quality/users/{user_id}/score

GET /api/v1/quality/users/{user_id}/rank

GET /api/v1/quality/models

GET /api/v1/quality/models/{model}/version
```

Only add endpoints when the underlying functionality is actually
implemented.

Use Pydantic schemas for every request/response.

------------------------------------------------------------------------

# 33. SECURITY

Replace:

``` text
allow_origins=["*"]
```

with an appropriate internal-service security model.

Support one of:

``` text
Internal API Key
Internal JWT
Service-to-service authentication
```

Do not expose model management or training endpoints publicly.

Separate:

``` text
inference API
admin/model API
training pipeline
```

------------------------------------------------------------------------

# 34. PERSISTENCE

Preserve:

``` text
MongoDB
quality
quality_results
```

Extend the result schema carefully.

Possible structure:

``` json
{
  "content_id": "...",
  "user_id": "...",

  "quality_score": 87.4,

  "classification": {
    "is_it": true,
    "it_probability": 0.98,
    "safety": {},
    "domain": {}
  },

  "semantic": {
    "embedding_model": "devradar-embedding-v1",
    "cluster_id": "database-performance"
  },

  "code_analysis": {},
  "suggested_tags": [],
  "duplicate_analysis": {},
  "score_breakdown": {},
  "model_versions": {},
  "created_at": "..."
}
```

Do not store huge raw vectors in MongoDB unless there is a clear reason.

Prefer vector index/object storage for large vector data.

------------------------------------------------------------------------

# 35. OBSERVABILITY

Add metrics for:

``` text
request_count
request_latency
model_latency
preprocessing_latency
embedding_latency
classification_latency
error_count
cache_hit_rate
queue_depth
model_version
prediction_distribution
low_confidence_rate
```

Monitor model drift indicators:

``` text
language distribution
IT/non-IT distribution
safety distribution
embedding distribution
unknown technology terms
confidence distribution
```

------------------------------------------------------------------------

# 36. TESTING

Do not reduce existing test coverage.

Add:

### Unit tests

-   cleaner
-   normalizer
-   Aho-Corasick
-   tokenizer
-   classifiers
-   embedding
-   scoring
-   penalty
-   rank
-   promotion
-   duplicate detection

### Integration tests

``` text
API
 ↓
Pipeline
 ↓
Model
 ↓
MongoDB
```

### ML tests

-   dataset validation
-   model loading
-   inference shape
-   label consistency
-   regression evaluation
-   model compatibility

### Security tests

-   authentication
-   unauthorized model access
-   malformed payloads
-   oversized input
-   abuse / rate limits

------------------------------------------------------------------------

# 37. PROJECT STRUCTURE

Prefer a structure similar to:

``` text
services/QualityService/
│
├── app/
│   ├── api/
│   │   ├── analyze.py
│   │   ├── batch.py
│   │   ├── users.py
│   │   ├── semantic.py
│   │   └── health.py
│   │
│   ├── pipeline/
│   │   └── pipeline.py
│   │
│   ├── preprocessing/
│   │   ├── cleaner.py
│   │   ├── normalizer.py
│   │   ├── tokenizer.py
│   │   ├── aho_corasick.py
│   │   └── code_analyzer.py
│   │
│   ├── classifiers/
│   │   ├── it_classifier.py
│   │   ├── safety_classifier.py
│   │   └── domain_classifier.py
│   │
│   ├── embeddings/
│   │   ├── encoder.py
│   │   └── service.py
│   │
│   ├── vector/
│   │   ├── interface.py
│   │   ├── faiss_store.py
│   │   └── clustering.py
│   │
│   ├── rules/
│   │   ├── length_rule.py
│   │   ├── spam_rule.py
│   │   ├── emoji_rule.py
│   │   ├── structure_rule.py
│   │   └── code_ratio_rule.py
│   │
│   ├── scoring/
│   │   ├── scorer.py
│   │   ├── weighting.py
│   │   └── penalties.py
│   │
│   ├── users/
│   │   ├── feature_extractor.py
│   │   ├── user_scorer.py
│   │   ├── rank_engine.py
│   │   └── promotion.py
│   │
│   ├── similarity/
│   │   ├── minhash.py
│   │   ├── simhash.py
│   │   └── semantic_similarity.py
│   │
│   ├── tags/
│   │   └── tag_extractor.py
│   │
│   ├── persistence/
│   │   └── repositories/
│   │
│   ├── config/
│   │
│   └── models/
│
├── training/
│   ├── datasets/
│   ├── train.py
│   ├── evaluate.py
│   ├── active_learning.py
│   └── export_model.py
│
├── mlops/
│   ├── experiments/
│   ├── model_registry/
│   └── monitoring/
│
├── models/
│   └── saved/
│
├── vector_store/
│
├── tests/
│
├── Dockerfile
├── requirements.txt
└── README.md
```

Adapt this structure to the actual repository instead of blindly
recreating it.

------------------------------------------------------------------------

# 38. IMPLEMENTATION ORDER

Do NOT implement everything in one pass.

Use these phases.

## Phase 0 --- Repository Audit

First inspect:

-   existing source tree
-   pipeline
-   models
-   rules
-   API
-   schemas
-   persistence
-   configuration
-   Docker
-   tests

Produce a short implementation report:

``` text
Existing
Missing
Needs Refactor
Needs New Module
Potential Breaking Change
```

Do not modify code during the audit phase.

------------------------------------------------------------------------

## Phase 1 --- Real ML Models

Implement:

-   dataset schema
-   dataset validation
-   training scripts
-   IT classifier training
-   safety classifier training
-   model loading
-   model versioning
-   evaluation

Keep heuristic fallback.

Acceptance:

``` text
Model exists
Model loads
Inference works
Metrics are recorded
Fallback still works
```

------------------------------------------------------------------------

## Phase 2 --- Semantic Layer

Implement:

-   embedding model
-   vector interface
-   FAISS index
-   similarity search
-   clustering
-   technology/tag extraction

Acceptance:

``` text
content → embedding
embedding → similarity
embedding → cluster
content → suggested_tags
```

------------------------------------------------------------------------

## Phase 3 --- Advanced Quality Scoring

Add:

-   technical depth
-   semantic quality
-   duplicate detection
-   configurable weighting
-   score breakdown
-   explainability

Do not break existing scoring API.

------------------------------------------------------------------------

## Phase 4 --- User Reputation

Implement:

-   user feature extraction
-   user score
-   penalties
-   rank
-   promotion
-   explainability
-   anti-gaming

------------------------------------------------------------------------

## Phase 5 --- Continuous Learning

Implement:

-   confidence tracking
-   active learning queue
-   labeling schema
-   dataset versioning
-   retraining pipeline
-   MLflow
-   model evaluation
-   model registry

------------------------------------------------------------------------

## Phase 6 --- Production Hardening

Implement:

-   async batch
-   queue
-   Redis caching
-   authentication
-   observability
-   rate limiting
-   model health checks
-   performance tests
-   security tests

------------------------------------------------------------------------

# 39. ACCEPTANCE CRITERIA

The implementation is considered successful only when:

### Content

-   Can identify IT vs non-IT
-   Can estimate confidence
-   Can identify safety problems
-   Can classify major IT domains
-   Can detect spam signals
-   Can analyze technical depth
-   Can extract technology tags

### Semantic

-   Can generate embeddings locally
-   Can perform similarity search
-   Can cluster content
-   Can identify semantically related content
-   Can detect duplicate / near-duplicate content

### User

-   Can calculate user quality score
-   Can calculate component-level score
-   Can apply penalties
-   Can automatically determine rank
-   Can determine promotion eligibility
-   Can explain promotion decisions

### ML

-   Models run locally
-   No third-party AI inference API
-   Training scripts exist
-   Dataset is versioned
-   Evaluation metrics exist
-   Model versions are tracked
-   Active learning is supported

### Engineering

-   Existing functionality remains operational
-   Existing tests continue to pass
-   New functionality has tests
-   Configuration is externalized
-   Docker build works
-   Healthcheck reports model status
-   APIs are documented
-   No secrets are hard-coded

------------------------------------------------------------------------

# 40. IMPORTANT ENGINEERING RULES

1.  **Inspect before modifying.**
2.  **Do not rewrite working modules without reason.**
3.  **Do not introduce unnecessary frameworks.**
4.  **Do not call external AI APIs.**
5.  **Do not train a Transformer from scratch unless justified.**
6.  **Do not let keyword rules become the primary intelligence layer.**
7.  **Do not let activity dominate user reputation.**
8.  **Do not allow production data to automatically overwrite the
    production model.**
9.  **Do not store giant embeddings unnecessarily in MongoDB.**
10. **Do not hard-code scoring weights or rank thresholds.**
11. **Do not break existing API contracts.**
12. **Every important AI score must be explainable.**
13. **Every model must have a version.**
14. **Every dataset used for training must be versioned.**
15. **Every model change must have evaluation evidence.**

------------------------------------------------------------------------

# 41. EXPECTED FINAL DELIVERABLE

After implementation, provide:

``` text
1. Architecture summary
2. Changed files
3. New files
4. New dependencies
5. Model architecture
6. Dataset format
7. Training procedure
8. Evaluation metrics
9. API changes
10. Database changes
11. Vector storage design
12. User scoring formula
13. Rank/promotion rules
14. MLOps workflow
15. Docker changes
16. Test results
17. Known limitations
18. Next recommended improvements
```

Do not claim a feature is complete if only a stub, mock, heuristic, or
placeholder exists.

Clearly distinguish:

``` text
Implemented
Partially Implemented
Planned
```

------------------------------------------------------------------------

# 42. FINAL PRINCIPLE

The goal is not to build a generic AI chatbot.

The goal is to build a **specialized machine-learning quality
intelligence system for DevRadar**:

``` text
Content
   ↓
Understand
   ↓
Classify
   ↓
Vectorize
   ↓
Cluster
   ↓
Score
   ↓
Explain
   ↓
Aggregate into User Reputation
   ↓
Rank
   ↓
Learn from reviewed production data
   ↓
Improve future models
```

The system should become more accurate over time through:

``` text
Production Data
      ↓
Human Feedback
      ↓
Active Learning
      ↓
Versioned Dataset
      ↓
Retraining
      ↓
Evaluation
      ↓
Approved Model
      ↓
Production
```

This is the target architecture for the next generation of **DevRadar
QualityService**.
