# Pet Health AI - Data Processing Pipeline

**Author:** Rachel He
**Last Updated:** January 28, 2026

This document describes the complete data processing pipeline for the Pet Health AI vector database.

---

## Table of Contents

1. [Overview](#overview)
2. [Raw Data Sources](#raw-data-sources)
3. [Processing Scripts (Execution Order)](#processing-scripts-execution-order)
4. [Processed Data Outputs](#processed-data-outputs)
5. [Quick Start](#quick-start)
6. [Current Data Characteristics](#current-data-characteristics)

---

## Overview

This pipeline processes diverse pet health data formats (images, JSON, CSV, Excel, Parquet) into a unified JSON structure, ready for embedding generation and upload to Pinecone vector database.

**Total Records Processed:** 18,909
**Vector Database:** Pinecone (index: `pet-health-ai`)
**Embedding Model:** OpenAI text-embedding-3-small (1536 dimensions)

Note: The processing scripts and raw data files are not included in this repository. This document serves as a reference for how the vector database was built.

---

## Raw Data Sources

### Location
`1. Original pet data/`

### Data Inventory

| File Name | Format | Content | Size |
|-----------|--------|---------|------|
| **archive-2/** | Images (JPG/PNG) | Pet skin disease images organized by condition type | Multiple subdirectories |
| **Dog pain database.xlsx** | Excel | Dog pain assessment records with diagnoses and pain scores | 251 KB |
| **Full_genotype_dataset.xlsx** | Excel | Genetic health profiles by breed with disease markers | 46 MB |
| **train-00000-of-00001.parquet** | Parquet | Veterinary clinical notes and case descriptions | 91 KB |
| **ofa_data/breed_health_risks.csv** | CSV | Breed-specific health risk data from OFA | - |
| **ofa_data/breed_health_risks.json** | JSON | Same data in JSON format | - |
| **ofa_data/bloat_risk_breeds.json** | JSON | Dog breeds at risk for bloat (gastric dilatation-volvulus) | - |
| **ofa_data/brachycephalic_breeds.json** | JSON | Brachycephalic breeds and associated health issues | - |
| **openfda_data/cat_adverse_events_sample.json** | JSON | FDA adverse event reports for cats | - |
| **openfda_data/dog_adverse_events_sample.json** | JSON | FDA adverse event reports for dogs | - |

---

## Processing Scripts (Execution Order)

### Step 1-3: Data Processing (Can Run in Parallel)

#### `1_process_images.py`

**Status:** Optional (requires OpenAI API, higher cost)

**Input:**
- **Source:** `1. Original pet data/archive-2/`
- **Format:** JPG/PNG images of pet skin diseases
- **Structure:** Organized in train/test/valid directories with condition subdirectories
- **Example conditions:** Bacterial infection, fungal infection, allergic dermatitis, etc.

**Processing:**
1. Scans image directories for all condition types
2. For each image:
   - Encodes to base64
   - Sends to GPT-4 Vision API
   - Generates detailed medical description (150-300 words)
3. Creates structured JSON record with metadata

**Output:**
- **File:** `2. Processed pet data/processed/skin_disease_images.json`
- **Format:** JSON array of objects
- **Records:** Variable (configurable, currently 3 per condition for cost control)
- **Structure:**
  ```json
  {
    "id": "skin_bacterial_a1b2c3d4",
    "text": "This image shows a canine presenting with bacterial pyoderma...",
    "metadata": {
      "source": "skin_disease_images",
      "doc_type": "skin_disease_reference",
      "animal_type": ["dog"],
      "body_system": "skin",
      "credibility": "professional",
      "condition": "bacterial_infection",
      "image_path": "/path/to/image.jpg",
      "data_split": "train"
    }
  }
  ```

---

#### `2_process_json.py`

**Input Sources:**

1. **OpenFDA Adverse Events**
   - Files: `cat_adverse_events_sample.json`, `dog_adverse_events_sample.json`
   - Format: Nested JSON from FDA API
   - Content: Drug adverse event reports including medications, reactions, outcomes

2. **Breed Risk Data**
   - Files: `bloat_risk_breeds.json`, `brachycephalic_breeds.json`
   - Format: Structured JSON arrays
   - Content: Breed-specific health risk information

3. **Symptom Frequency** (if present)
   - Content: Symptom occurrence statistics

**Processing:**
1. **Adverse Events:**
   - Extracts drug names, reactions, animal species
   - Converts to natural language descriptions
   - Determines affected body system from reactions

2. **Breed Risks:**
   - Parses breed lists and associated conditions
   - Formats as informative text

**Output:**
- **Files:**
  - `2. Processed pet data/processed/adverse_events.json` (15,000 records)
  - `2. Processed pet data/processed/breed_risks.json`
  - `2. Processed pet data/processed/symptom_info.json` (1,000 records)

- **Structure:**
  ```json
  {
    "id": "ae_dog_abc123",
    "text": "Adverse event report for dog: Drug(s) involved: MSK (Oral). Reactions observed: Vomiting, Lethargy...",
    "metadata": {
      "source": "openfda_adverse_events",
      "doc_type": "adverse_event",
      "animal_type": ["dog"],
      "body_system": "gi",
      "credibility": "official",
      "original_fields": {
        "drug_names": ["MSK"],
        "reactions": ["Vomiting", "Lethargy"],
        "outcome": "recovered"
      }
    }
  }
  ```

---

#### `3_process_structured.py`

**Input Sources:**

1. **Breed Health Risks CSV**
   - File: `breed_health_risks.csv`
   - Format: CSV with columns: breed, condition, risk_level
   - Content: OFA (Orthopedic Foundation for Animals) breed health data

2. **Clinical Notes Parquet**
   - File: `train-00000-of-00001.parquet`
   - Format: Apache Parquet columnar format
   - Content: Veterinary clinical case notes and diagnoses

3. **Pain Database Excel**
   - File: `Dog pain database.xlsx`
   - Format: Excel spreadsheet
   - Content: Dog pain assessments with breed, diagnosis, pain type, severity

4. **Genotype Dataset Excel**
   - File: `Full_genotype_dataset.xlsx`
   - Format: Excel with multiple sheets
   - Content: Genetic test results aggregated by breed

**Processing:**
1. **Breed Health CSV:**
   - Converts to natural language: "Breed X has Y risk of Z condition"
   - Maps conditions to body systems

2. **Clinical Notes:**
   - Extracts condition and description
   - Standardizes format

3. **Pain Database:**
   - Combines breed, diagnosis, pain type into descriptive text

4. **Genotype Data:**
   - Aggregates by breed
   - Calculates carrier and affected percentages
   - Formats genetic risk profiles

**Output:**
- **Files:**
  - `2. Processed pet data/processed/breed_health.json` (69 records)
  - `2. Processed pet data/processed/clinical_notes.json` (2,000 records)
  - `2. Processed pet data/processed/pain_assessments.json` (594 records)
  - `2. Processed pet data/processed/genotype_profiles.json` (246 records)

- **Structure:**
  ```json
  {
    "id": "breed_dog_xyz789",
    "text": "Labrador Retriever is a dog breed. Has high risk of hip dysplasia. Has high risk of elbow dysplasia...",
    "metadata": {
      "source": "breed_health",
      "doc_type": "breed_health",
      "animal_type": ["dog"],
      "body_system": "mobility",
      "credibility": "official",
      "original_fields": {
        "breed": "Labrador Retriever",
        "conditions": ["hip_dysplasia", "elbow_dysplasia"],
        "risk_levels": ["high", "high"]
      }
    }
  }
  ```

---

### Step 4: Merge and Chunk

#### `4_chunk_and_merge.py`

**Input:**
- All JSON files from Step 1-3 (7 files total)
- Configuration from `config.py`:
  - `CHUNK_SIZE = 600` tokens (~2400 chars)
  - `CHUNK_OVERLAP = 100` tokens (~400 chars)

**Processing:**
1. **Load** all processed JSON files
2. **Validate** each record has required fields (id, text, metadata)
3. **Check text length:**
   - If text <= 2400 chars: Keep as-is (current: 100% of records)
   - If text > 2400 chars: Split using LangChain RecursiveCharacterTextSplitter
4. **Generate statistics** by doc_type, animal_type, body_system, credibility

**Output:**
- **Files:**
  - `2. Processed pet data/processed/combined_chunks.json` (18,909 records, 10.3 MB)
  - `2. Processed pet data/processed/processing_stats.json`

- **Statistics JSON:**
  ```json
  {
    "total_records": 18909,
    "by_doc_type": {
      "adverse_event": 15000,
      "clinical_notes": 2000,
      "symptom_info": 1000,
      "pain_assessment": 594,
      "genetic_risk": 246,
      "breed_health": 69
    },
    "text_length_stats": {
      "min": 20,
      "max": 536,
      "avg": 183
    }
  }
  ```

**Note:** Current dataset consists of short structured records (avg 183 chars). No chunking is performed, but the infrastructure is ready for future long documents.

---

### Step 5: Quality Evaluation

#### `5_evaluate_chunks.py`

**Input:**
- `combined_chunks.json` from Step 4

**Processing:**
1. **Size Distribution Analysis**
   - Character and token counts
   - Distribution across size ranges

2. **Semantic Quality Check**
   - Sentence completeness (ending punctuation)
   - Proper capitalization
   - Identify very short records

3. **Chunking Analysis**
   - Count documents that were split
   - Analyze overlap quality

4. **Type-based Statistics**
   - Records per document type
   - Average lengths by type

**Output:**
- **File:** `2. Processed pet data/processed/chunk_quality_report.json`
- **Console:** Detailed analysis report with quality score (0-100)

**Current Results:**
- **Score:** 75/100 (Good)
- **Semantic Integrity:** 100%
- **Chunked Documents:** 0 (all records are short)
- **Recommendations:** Data quality is good for structured medical records

---

### Step 6: Upload to Vector Database

#### `6_upload_to_pinecone.py`

**Input:**
- `combined_chunks.json` from Step 4
- OpenAI API key (for embeddings)
- Pinecone API key (for vector database)

**Processing:**
1. **Load records** from combined_chunks.json
2. **Generate embeddings:**
   - Batch size: 100 records
   - Model: text-embedding-3-small (1536 dimensions)
   - Rate limiting: 0.1s between batches
3. **Flatten metadata** for Pinecone compatibility
4. **Upsert vectors** to Pinecone index
5. **Run test queries** to verify upload

**Output:**
- **Pinecone Index:** `pet-health-ai`
  - Cloud: AWS Serverless (us-east-1)
  - Dimension: 1536
  - Metric: cosine
  - Total vectors: 18,909

- **Test Query Results:**
  - "What health problems do Labrador Retrievers have?" -- Similarity: 0.69
  - "My dog is vomiting after taking medication" -- Similarity: 0.62
  - "Skin problems in dogs" -- Similarity: 0.62

**Performance:**
- Upload time: ~5-6 minutes
- Embeddings generated: 18,909
- API calls: ~190 batches

---

## Processed Data Outputs

### Location
`2. Processed pet data/processed/`

### Final Data Inventory

| File Name | Records | Avg Length | Source Script |
|-----------|---------|------------|---------------|
| adverse_events.json | 15,000 | 190 chars | 2_process_json.py |
| breed_health.json | 69 | 239 chars | 3_process_structured.py |
| breed_risks.json | Variable | 279 chars | 2_process_json.py |
| clinical_notes.json | 2,000 | 65 chars | 3_process_structured.py |
| genotype_profiles.json | 246 | 196 chars | 3_process_structured.py |
| pain_assessments.json | 594 | 233 chars | 3_process_structured.py |
| symptom_info.json | 1,000 | 279 chars | 2_process_json.py |
| skin_disease_images.json | Variable | - | 1_process_images.py |
| **combined_chunks.json** | **18,909** | **183 chars** | **4_chunk_and_merge.py** |
| processing_stats.json | - | - | 4_chunk_and_merge.py |
| chunk_quality_report.json | - | - | 5_evaluate_chunks.py |

### Standard Record Structure

All processed records follow this consistent structure:

```json
{
  "id": "string (unique identifier with prefix)",
  "text": "string (natural language description)",
  "metadata": {
    "source": "string (data source identifier)",
    "doc_type": "string (breed_health|clinical_notes|adverse_event|etc)",
    "animal_type": ["string array (dog, cat, etc)"],
    "body_system": "string (gi|mobility|skin|respiratory|etc)",
    "credibility": "string (official|professional|community)",
    "original_fields": "object (original structured data)"
  }
}
```

---

## Quick Start

### Prerequisites
```bash
# Install dependencies
pip install -r ../requirements.txt

# Set environment variables
export OPENAI_API_KEY='your-openai-key'
export PINECONE_API_KEY='your-pinecone-key'
```

### Run Full Pipeline

```bash
# Step 1: Process JSON data (required)
python 2_process_json.py

# Step 2: Process structured data (required)
python 3_process_structured.py

# Step 3: Process images (optional, costs API credits)
# python 1_process_images.py

# Step 4: Merge all data (required)
python 4_chunk_and_merge.py

# Step 5: Evaluate data quality (optional but recommended)
python 5_evaluate_chunks.py

# Step 6: Upload to Pinecone (required)
python 6_upload_to_pinecone.py
```

### View Vector Database

```bash
# Use the utility script to query and inspect Pinecone
python view_pinecone.py
```

---

## Current Data Characteristics

**As of January 28, 2026:**

### Size Profile
- **Total Records:** 18,909
- **Average Length:** 183 characters (25 tokens)
- **Max Length:** 536 characters
- **Min Length:** 20 characters

### Why No Chunking?
All records are short, structured medical records (clinical reports, adverse events, breed data). They are well below the chunking threshold (2400 chars), so:
- Records are kept intact
- Each vector represents one complete medical event
- Better precision for retrieval

### Data Quality
- **Semantic Integrity:** 100% (all complete sentences)
- **Standardized Format:** All records follow unified schema
- **Rich Metadata:** Extensive filtering capabilities
- **Credibility Levels:** 80% official sources, 20% professional

### Known Limitations

1. **Data distribution imbalance**: Adverse event records account for 79% (15,000 / 18,909) of the dataset. This means vector similarity searches tend to return drug reaction reports disproportionately, even when the user query is about general symptoms or care guidance.
2. **Short record length**: The average record is 183 characters (25 tokens), with clinical notes averaging only 65 characters. Short texts produce embeddings with weaker semantic signal, resulting in moderate cosine similarity scores (~0.62) and reduced retrieval precision.
3. **Missing knowledge types**: The dataset lacks symptom-to-condition differential diagnosis references, home care and first-aid guidance, and triage decision criteria -- the types of content most valuable for a symptom triage system.
4. **Mitigation**: The RAG prompt is designed to treat retrieved information as supplementary context rather than the sole knowledge source. When retrieval results are incomplete, the LLM falls back on its general veterinary training knowledge.

### Future Expansion
The pipeline is designed to handle long documents (e.g., textbook chapters, medical articles > 2400 chars). When added, they will be automatically:
- Detected and split into chunks
- Overlapped for context preservation
- Linked via parent_id metadata

---

## Utility Scripts

### `view_pinecone.py`
- View Pinecone index statistics
- Browse sample vectors
- Test search queries
- Interactive query mode

---

## Configuration

### Key Settings in `config.py`

```python
# Paths
RAW_DATA_DIR = PROJECT_ROOT / "1. Original pet data"
PROCESSED_DIR = PROJECT_ROOT / "2. Processed pet data" / "processed"

# Chunking (currently not triggered due to short records)
CHUNK_SIZE = 600        # tokens
CHUNK_OVERLAP = 100     # tokens

# Vector Database
PINECONE_INDEX_NAME = "pet-health-ai"
PINECONE_DIMENSION = 1536
EMBEDDING_MODEL = "text-embedding-3-small"

# Credibility Levels
CREDIBILITY_OFFICIAL = "official"          # FDA, OFA data
CREDIBILITY_PROFESSIONAL = "professional"  # Clinical notes, vet data
CREDIBILITY_COMMUNITY = "community"        # User reports
```

---

## Troubleshooting

### Common Issues

**Issue:** "OPENAI_API_KEY not set"
**Solution:** Ensure .env file exists in project root with valid API key

**Issue:** "combined_chunks.json not found"
**Solution:** Run scripts 1-4 first before running 5 or 6

**Issue:** Pinecone index already exists
**Solution:** Either delete the old index or use a different INDEX_NAME in config.py

**Issue:** Rate limit errors
**Solution:** Increase wait time between batches in upload script

---

## Data Flow Diagram

```
Raw Data Sources
    |-- Images (archive-2/)
    |-- JSON (openfda_data/, ofa_data/)
    +-- Structured (CSV, Excel, Parquet)
          |
    Processing Scripts (1-3)
          |
    Individual JSON Files (7 files)
          |
    4_chunk_and_merge.py
          |
    combined_chunks.json (18,909 records)
          |
    5_evaluate_chunks.py --> Quality Report
          |
    6_upload_to_pinecone.py
          |
    Pinecone Vector Database
```

---

## Credits

**Data Sources:**
- OpenFDA (adverse events)
- Orthopedic Foundation for Animals (OFA - breed health)
- Veterinary clinical databases
- Pet skin disease image dataset

**Technologies:**
- OpenAI (GPT-4 Vision, text-embedding-3-small)
- Pinecone (vector database)
- LangChain (text splitting)
- Pandas, PyArrow (data processing)
