# The Unofficial Guide: Professor and Course Guidance RAG

## Project Overview

**The Unofficial Guide** is a Retrieval-Augmented Generation (RAG) system that answers student questions using collected student-generated documents. My chosen domain is **Unofficial Professor and Course Guidance at Springfield College**.

The goal is to make informal academic knowledge searchable: professor review patterns, course difficulty, workload expectations, feedback style, exam preparation advice, and registration guidance. This type of knowledge is valuable because official course catalogs describe course content, but they usually do not explain how a class actually feels to students.

---

## Domain and Document Sources

**Domain:** Unofficial Professor and Course Guidance at Springfield College

This domain includes student-generated information about professors, course workload, grading expectations, exam style, class size, professor accessibility, and course selection. The knowledge is hard to find through official channels because it is scattered across Rate My Professors, college review pages, Reddit-style discussions, and informal student advice files.

| # | Source Document | Source Type | URL or Local File |
|---|---|---|---|
| 1 | Rate My Professors - Carol Ligarski | Professor review | `https://www.ratemyprofessors.com/professor/1265479` / `data/rmp_professor_a.txt` |
| 2 | Rate My Professors - Carl Fetteroll | Professor review | `https://www.ratemyprofessors.com/professor/2757587` / `data/rmp_professor_b.txt` |
| 3 | Rate My Professors - Fabio Valenti Possamai | Professor review | `https://www.ratemyprofessors.com/professor/2795946` / `data/rmp_professor_c.txt` |
| 4 | Reddit thread about CS teaching quality | Student discussion thread | `https://www.reddit.com/r/CSEducation/comments/j9fpeo/why_is_computer_science_education_so_bad/` / `data/reddit_cs_professors.txt` |
| 5 | Reddit thread about easiest and hardest college classes | Student discussion thread | `https://www.reddit.com/r/college/comments/3y21h0/what_is_the_easiest_class_you_took_in_college_the/` / `data/reddit_easy_classes.txt` |
| 6 | Niche Springfield College academics reviews | College review page | `https://www.niche.com/colleges/springfield-college-massachusetts/academics/` / `data/niche_academics_reviews.txt` |
| 7 | Unigo Springfield College academics reviews | College review page | `https://www.unigo.com/colleges/springfield-college` / `data/unigo_academics.txt` |
| 8 | Student course advice page/forum | Course advice | Local file: `data/course_advice.txt` |
| 9 | Professor/course Discord advice | Student advice | Local file: `data/discord_course_advice.txt` |
| 10 | Campus newspaper/opinion about classes | Student article | Local file: `data/campus_classes_article.txt` |

**Note:** The first seven documents are based on public source pages. The final three are local student-advice style documents used to test the system's ability to retrieve from forum-like and article-like text. If this system were expanded, I would replace or supplement those local files with more real student-created sources.

---

## System Architecture

The system follows this pipeline:

```text
data/*.txt
   ↓
Document ingestion and metadata extraction
   ↓
Chunking by natural units
   ↓
Embedding with all-MiniLM-L6-v2
   ↓
Persistent Chroma vector store
   ↓
User query
   ↓
Query embedding + semantic search
   ↓
Top-k retrieved chunks
   ↓
Grounded LLM response with citations
```

The implementation is organized around these files:

```text
app.py                 Command-line query interface
evaluate.py            Evaluation harness
src/config.py          Central settings
src/ingest.py          Document loading and chunking
src/embed_store.py     Embedding and Chroma vector storage
src/retrieve.py        Semantic retrieval
src/generate.py        Grounded response generation
src/pipeline.py        End-to-end retrieve → generate flow
```

---

## Document Ingestion

The ingestion pipeline loads every `.txt` file from the `data/` folder. Each document is read from disk, assigned a source type based on its filename, and split into chunks. Each chunk preserves metadata so that final answers can show source attribution.

Each chunk stores:

```text
source_file
source_path
title
source_type
chunk_id
text
```

This metadata is important because the system must be able to explain which source file supported each answer.

---

## Chunking Strategy and Reasoning

**Chunk size:** 1,000 characters maximum  
**Target floor:** 700 characters for split chunks  
**Overlap:** 125 characters when splitting long units  
**Strategy:** Natural-unit chunking first, fixed-size splitting only as a fallback

The documents are mostly review-style and advice-style sources, not long textbooks. Many useful facts are contained in short reviews, posts, messages, or paragraphs. Because of that, the chunker first tries to preserve natural boundaries such as:

- one professor review
- one forum post
- one Discord-style message
- one article paragraph
- one source section separated by `---`

This fits my corpus better than blindly splitting every 500 characters. If a review or message is split too aggressively, a chunk might include a claim like “the class is difficult” without the professor name or the reason. If a chunk is too large, it may mix multiple professors or unrelated course topics, which makes retrieval less precise.

The system only uses character-window splitting when one natural unit is longer than the configured maximum chunk size. The 125-character overlap helps preserve context when a long section must be split.

---

## Sample Chunks

### Sample Chunk 1 — `rmp_professor_a.txt`

```text
Professor: Carol Ligarski
School: Springfield College
Department: Computer Science
Overall Quality: 2.6 / 5
Number of Ratings: 12
Would Take Again: 67%
Level of Difficulty: 4.2 / 5
Common Course Codes Mentioned: CISC101, CISC105
```

This chunk is useful for direct factual questions about Professor Ligarski’s rating, difficulty, and would-take-again percentage.

### Sample Chunk 2 — `rmp_professor_b.txt`

```text
Professor: Carl Fetteroll
School: Springfield College
Department: Mathematics
Overall Quality: 5.0 / 5
Number of Ratings: 3
Would Take Again: 100%
Level of Difficulty: 1.3 / 5
Common Course Code Mentioned: MATH103
Top Tags Mentioned: Gives good feedback, hilarious, amazing lectures
```

This chunk is useful for questions about beginner-friendly math professors because it contains professor name, department, difficulty, and feedback signals.

### Sample Chunk 3 — `unigo_academics.txt`

```text
Class sizes rating: 4.5 stars from 53 students
Academics rating: 4.0 stars from 53 students

Extracted Student Signals:
Students rate class sizes highly, suggesting that small classes are a strength.
One student review says the small campus helps students get more one-on-one time with professors.
```

This chunk supports questions about class sizes and professor accessibility at Springfield College.

### Sample Chunk 4 — `campus_classes_article.txt`

```text
Several students recommended asking three questions before choosing a course.
First, how much weekly work does the class require?
Second, are exams based mostly on lectures, readings, homework, or projects?
Third, does the professor give feedback early enough for students to improve?
```

This chunk supports course-selection questions because it provides a concrete checklist for registration decisions.

### Sample Chunk 5 — `discord_course_advice.txt`

```text
Most CS exams are not about copying code from memory.
They usually ask you to trace code, explain output, identify bugs, or compare algorithms.
If you can explain your homework solutions out loud, you are usually prepared for the exam.
```

This chunk is useful for questions about how beginner CS students should prepare for programming exams.

---

## Embedding Model and Vector Store

**Embedding model:** `all-MiniLM-L6-v2`  
**Library:** `sentence-transformers`  
**Vector store:** ChromaDB  
**Top-k:** 4 retrieved chunks per query

I chose `all-MiniLM-L6-v2` because it is lightweight, fast, and appropriate for a small student project with a limited corpus. It is strong enough for semantic search over short review-style text, where students may ask questions using different words than the documents. For example, a query like “beginner-friendly math professor” can still match chunks that say “approachable,” “not overly difficult,” or “gives good feedback.”

For a production deployment, I would compare embedding models based on:

- retrieval accuracy on informal student language
- context length
- cost
- latency
- multilingual support
- whether the model runs locally or requires an API
- performance on short opinion-based text

A larger embedding model might improve accuracy, especially for vague questions, but it could also be slower and more expensive.

---

## Retrieval Test Results

### Retrieval Test 1

**Query:** Which professor is beginner-friendly for math?

**Top returned chunks:**

| Rank | Source | Notes |
|---|---|---|
| 1 | `rmp_professor_b.txt` | Carl Fetteroll math professor review |
| 2 | `rmp_professor_b.txt` | Additional Carl Fetteroll review/rating signals |
| 3 | `rmp_professor_c.txt` | Another professor with positive review signals, but not math |
| 4 | `discord_course_advice.txt` | General student advice about choosing professors |

**Why these chunks are relevant:**  
The first two chunks are directly relevant because they describe Carl Fetteroll, a mathematics professor, with a low difficulty rating, strong overall quality rating, and positive feedback signals. The third and fourth chunks are less directly relevant because they discuss professor helpfulness and beginner support generally, but they are not the main evidence for the math professor answer.

---

### Retrieval Test 2

**Query:** What do students say about Professor Carol Ligarski's workload and difficulty?

**Top returned chunks/files:**

| Rank | Source | Notes |
|---|---|---|
| 1 | `reddit_easy_classes.txt` | General discussion about class difficulty |
| 2 | `rmp_professor_a.txt` | Direct Carol Ligarski workload/difficulty evidence |
| 3 | `campus_classes_article.txt` | General course workload advice |

**Why these chunks are relevant:**  
The `rmp_professor_a.txt` chunk is the strongest evidence because it directly discusses Professor Carol Ligarski, her workload, homework, projects, attendance, and difficulty. The Reddit and campus article chunks are more general and help frame why class difficulty can vary, but they should not be treated as direct evidence about Ligarski.

---

### Retrieval Test 3

**Query:** What do students say about class sizes and professor accessibility at Springfield College?

**Top returned chunks/files:**

| Rank | Source | Notes |
|---|---|---|
| 1 | `unigo_academics.txt` | Class size rating and professor accessibility |
| 2 | `campus_classes_article.txt` | General course-selection advice |
| 3 | `niche_academics_reviews.txt` | Academic support and professor approachability |

**Why these chunks are relevant:**  
The `unigo_academics.txt` chunk is relevant because it contains a class-size rating and comments about students getting more one-on-one time with professors. The `niche_academics_reviews.txt` chunk is also relevant because it discusses professor support and academic resources.

---

## Grounded Generation

Grounded generation is enforced through both prompt design and pipeline structure.

The LLM receives only:

1. the user question
2. the top retrieved chunks
3. source metadata for each chunk

The system prompt tells the model to:

- answer only from the provided context
- avoid outside knowledge
- avoid inventing professors, courses, or facts
- use hedged wording because student reviews are subjective
- cite source files used in the answer
- say it does not have enough information when the context is insufficient

This prevents the model from giving generic college advice that sounds correct but is not supported by retrieved documents.

---

## Example Responses

### Example Response 1

**Query:** Which professor is beginner-friendly for math?

**Response:**

```text
According to the available sources, Carl Fetteroll seems most beginner-friendly for math (rmp_professor_b.txt). Students describe his class as approachable and not overly difficult, with a Level of Difficulty rating of 1.3/5. The document also mentions useful feedback and an engaging lecture style (rmp_professor_b.txt).
```

**Visible source attribution:** `rmp_professor_b.txt`

---

### Example Response 2

**Query:** Before choosing a class that seems easy, what should a student check first?

**Response:**

```text
According to the available sources, before choosing a class that seems easy, a student should check the workload, professor feedback style, exam format, and how the course fits with their other responsibilities (campus_classes_article.txt). Students specifically suggest asking how much weekly work the class requires, whether exams are based mostly on lectures, readings, homework, or projects, and whether the professor gives feedback early enough for students to improve (campus_classes_article.txt).
```

**Visible source attribution:** `campus_classes_article.txt`

---

### Out-of-Scope Example

**Query:** What is the best dining hall at Springfield College?

**Expected refusal response:**

```text
The available sources do not contain enough information to answer this. The retrieved documents focus on professors, courses, academic reviews, and student course advice, not dining halls.
```

This is the correct behavior because the system should not answer from general knowledge when the retrieved documents do not support the claim.

---

## Query Interface

The system uses a command-line interface.

### Input Options

| Command | Purpose |
|---|---|
| `python app.py --rebuild` | Rebuild the vector index from the `data/` folder |
| `python app.py "your question"` | Ask one question |
| `python app.py` | Start interactive mode |
| `python app.py --top-k 6 "your question"` | Retrieve a custom number of chunks |

### Output Fields

Each response prints:

- the user question
- the generated answer
- retrieved chunks with similarity scores
- source citations
- final source list

### Sample Interaction Transcript

```text
$ python app.py "Which professor is beginner-friendly for math?"

======================================================================
Q: Which professor is beginner-friendly for math?
----------------------------------------------------------------------
According to the available sources, Carl Fetteroll seems most beginner-friendly for math (rmp_professor_b.txt). Students describe his class as approachable and not overly difficult, with a Level of Difficulty rating of 1.3/5. Reviews also mention useful feedback and an engaging lecture style (rmp_professor_b.txt).
----------------------------------------------------------------------
Retrieved chunks (top-4):
  [1] score=0.572  Carl Fetteroll (Rate My Professors review, rmp_professor_b.txt)
  [2] score=0.562  Carl Fetteroll (Rate My Professors review, rmp_professor_b.txt)
  [3] score=0.534  Fabio Valenti Possamai (Rate My Professors review, rmp_professor_c.txt)
  [4] score=0.482  Discord Course Advice (Student course advice, discord_course_advice.txt)
Sources: rmp_professor_b.txt, rmp_professor_c.txt, discord_course_advice.txt
======================================================================
```

---

## Evaluation Report

The evaluation set includes five test questions. Each question has an expected answer and a judgment based on whether the retrieved chunks and generated response support that answer.

### Evaluation Summary

| # | Question | Expected Answer | System Response Summary | Retrieved Sources | Judgment |
|---|---|---|---|---|---|
| 1 | What do students say about Professor Carol Ligarski's workload and difficulty? | Students describe a heavy workload, high homework amount, difficult projects, important attendance, and challenging tests/quizzes. | The system said Ligarski’s class has heavy workload, homework, difficult projects, regular attendance expectations, and challenging tests/quizzes. | `reddit_easy_classes.txt`, `rmp_professor_a.txt`, `campus_classes_article.txt` | Accurate |
| 2 | Which professor in the documents seems most beginner-friendly for math? | Carl Fetteroll, based on MATH103, 1.3/5 difficulty, good feedback, and positive review signals. | The system identified Carl Fetteroll and cited his low difficulty rating and useful feedback. | `rmp_professor_b.txt`, `rmp_professor_c.txt` | Accurate |
| 3 | What do students say about class sizes and professor accessibility at Springfield College? | Unigo lists class sizes positively and students mention one-on-one access with professors; Niche supports professor approachability. | The system said class sizes are a strength and small classes help students get more one-on-one time with professors. | `unigo_academics.txt`, `campus_classes_article.txt`, `niche_academics_reviews.txt` | Accurate |
| 4 | Before choosing a class that seems easy, what should a student check first? | Students should check weekly workload, exam format, reading/writing/project expectations, feedback timing, and schedule fit. | The system listed workload, professor feedback style, exam format, and how the course fits with other responsibilities. | `campus_classes_article.txt`, `course_advice.txt`, `reddit_easy_classes.txt` | Accurate |
| 5 | How should a beginner CS student prepare for programming exams? | Students should practice tracing code, explaining output, identifying bugs, comparing algorithms, and explaining homework solutions. | The system mentioned explaining homework solutions, choosing professors with examples, starting assignments early, and understanding concepts, but it did not clearly list tracing code, explaining output, identifying bugs, or comparing algorithms. | `discord_course_advice.txt`, `course_advice.txt` | Partially accurate |

---

## Honest Failure Case

The clearest failure case was **Evaluation Question 5**:

```text
How should a beginner CS student prepare for programming exams?
```

The retrieval step found relevant documents: `discord_course_advice.txt` and `course_advice.txt`. However, the generated answer did not fully extract the most specific exam-preparation details from the Discord source. The expected answer included tracing code, explaining output, identifying bugs, and comparing algorithms. The system instead gave broader advice.

This is not a total failure but still but it was incomplete. The likely cause is generation focus: the LLM summarized general advice from multiple chunks instead of prioritizing the most specific exam-task sentence.

A smaller issue also appeared in some answers: the output sometimes listed all retrieved source files even when the final answer mainly used only one of them. This is not a grounding failure, but the citations could be cleaner if the system listed only the sources actually used in the final answer.

---

## How to Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Rebuild the index:

```bash
python app.py --rebuild
```

Ask one question:

```bash
python app.py "Which professor is beginner-friendly for math?"
```

Start interactive mode:

```bash
python app.py
```

Run evaluation:

```bash
python evaluate.py
```

---

## Spec Reflection

One way the spec helped me was by forcing me to think about chunking before building embeddings. The reminder that “most RAG failures trace back to bad chunks” helped me avoid a naive splitter and instead preserve reviews, posts, messages, and paragraphs as complete units.

One way implementation diverged from the original plan is that I chose **ChromaDB** as the vector store instead of leaving the plan open between FAISS and Chroma. I chose Chroma because it provides persistent local storage and stores metadata cleanly with each chunk, which made citation easier. Another small divergence is that the evaluation script automatically checks whether expected source files appear in the retrieved chunks, but final answer accuracy still requires manual judgment because retrieval success alone does not prove the generated answer is complete.

---

## AI Usage

I used AI tools as implementation support, but I revised the outputs to match the project requirements.

1. I asked AI to help design a beginner-friendly ingestion and chunking pipeline based on my `planning.md`. I gave it my domain, document list, and chunking strategy. I revised the output so the final implementation chunks by natural document units instead of blindly splitting every fixed number of characters.

2. I asked AI to help turn subjective evaluation questions into verifiable ones. For example, instead of only asking “Which professor is good?”, I revised questions to check specific ratings, file evidence, or exact advice from the documents.

3. I used AI to help organize the README into the required sections. I edited the final content to include my actual retrieval results, my honest failure case, and the specific implementation choices from my code.

4.  I used AI to help interpret terminal errors, especially when the app.py was crashing continously due lack of proper code structure.

---

## Current Status

The system supports:

- loading local `.txt` documents
- chunking by natural units
- embedding chunks with `all-MiniLM-L6-v2`
- storing vectors in ChromaDB
- retrieving top-k chunks by semantic similarity
- generating grounded answers with citations
- running a command-line query interface
- running an evaluation harness over five test questions

The next improvement would be to refine citation behavior so that final answers list only the sources actually used, not every retrieved source.
