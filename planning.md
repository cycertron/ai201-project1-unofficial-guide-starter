# Project 1 Planning: The Unofficial Guide
## Domain 

I chose Unofficial Professor and Course Guidance at Springfield College as my domain. This guide focuses on student-generated knowledge about professors, course difficulty, workload, exam style, teaching quality, feedback, and registration decisions.

This knowledge is valuable because official course catalogs explain what a class is about, but they do not explain what students actually experience in the class. A student may want to know whether a professor gives useful feedback, whether exams match homework, whether a class is beginner-friendly, or whether the workload is manageable. That kind of information is usually scattered across review sites, forums, Reddit threads, and student conversations, so a RAG system can make it easier to search and cite.
---


<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->


| # | Source | Description | URL or location | File Path |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Rate My Professors - Carol Ligarski | Professor review source for Computer Science courses, workload, difficulty, and teaching style | data/rmp_professor_a.txt | |
| 2 | Rate My Professors - Carl Fetteroll | Professor review source for Mathematics, feedback quality, class difficulty, and beginner-friendliness | data/rmp_professor_b.txt | |
| 3 | Rate My Professors - Fabio Valenti Possamai | Professor review source for Philosophy/humanities teaching style, feedback, and course difficulty | data/rmp_professor_c.txt | |
| 4 | Reddit thread about CS professors | General student discussion about CS teaching quality, professor explanation style, and beginner support | data/reddit_cs_professors.txt | |
| 5 | Reddit thread about easiest classes | Student discussion about what makes college classes easy or hard, including workload, exams, reading, and grading style | data/reddit_easy_classes.txt | |
| 6 | Niche Springfield College academics reviews | College review page covering academics, professors, registration, support, and student academic experience | data/niche_academics_reviews.txt | |
| 7 | Unigo Springfield College academics reviews | College review page covering class size, professor accessibility, academics, and student experience | data/unigo_academics.txt | |
| 8 | Student course advice page/forum | Course advice source about programming, data structures, linear algebra, writing courses, and schedule balance | data/course_advice.txt | |
| 9 | Professor/course Discord advice | Informal student advice about professor choice, office hours, CS exams, registration, and balanced schedules | data/discord_course_advice.txt | |
| 10 | Campus newspaper/opinion about classes | Student-style article about registration, workload, professor feedback, exam format, and course selection | | |


## Chunking Strategy
**Chunk size:**
About 700–1,000 characters per chunk, roughly 150–250 tokens.

**Overlap:**
About 100–150 characters of overlap when a longer section needs to be split.


**Reasoning:**
Most of my documents are short reviews, student comments, forum posts, or advice messages. Because of that, I should not split every file blindly by a fixed size. A single review or message often contains the professor name, course name, workload description, and student recommendation together. If I split too aggressively, the system might retrieve a sentence like “the class is hard” without the reason why it is hard.

My first strategy will be to chunk by natural units: one review, one forum post, one Discord-style message, or one article paragraph. If a section is too long, then I will split it into 700–1,000 character chunks with 100–150 characters of overlap. The overlap helps when an important idea is spread across two nearby paragraphs or when a professor name appears in one sentence and the actual student advice appears in the next sentence.

If chunks are too small, retrieval may return incomplete evidence and the answer may become vague or unsupported. If chunks are too large, retrieval may return too much unrelated information, such as multiple professors or several course topics in one chunk. A good chunk should be specific enough to answer a question but complete enough to include the context behind the answer.

---

## Retrieval Approach
**Embedding model:**
all-MiniLM-L6-v2 using sentence-transformers

**Top-k:**
Retrieve the top 4 chunks for each user query.

**Production tradeoff reflection:**
I chose all-MiniLM-L6-v2 because it is lightweight, fast, and good enough for a first RAG project with a small text corpus. Since my documents are short and opinion-based, retrieving the top 4 chunks should give the LLM enough evidence without overwhelming it with too much context.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->


| # | Question | Expected answer |
| :--- | :--- | :--- |
| 1 | What do students say about Professor Carol Ligarski’s workload and difficulty? | The system should answer that students describe her classes as challenging, with heavy homework, difficult projects, and important attendance expectations. It should also mention that some students still felt they learned useful programming skills. Expected source: data/rmp_professor_a.txt. |
| 2 | Which professor in the documents seems most beginner-friendly for math? | The system should identify Carl Fetteroll as a strong option based on positive student signals such as helpful feedback, approachable difficulty, engaging lectures, and support for understanding the material. Expected source: data/rmp_professor_b.txt. |
| 3 | What do students say about class sizes and professor accessibility at Springfield College? | The system should explain that students describe class sizes positively and suggest that smaller classes help students get more one-on-one access to professors. Expected source: data/unigo_academics.txt. |
| 4 | Before choosing a class that seems easy, what should a student check first? | The system should say that students should check weekly workload, exam format, reading or writing expectations, project deadlines, and whether the professor gives feedback early enough to improve. Expected sources: data/reddit_easy_classes.txt and data/campus_classes_article.txt. |
| 5 | How should a beginner CS student prepare for programming exams? | The system should explain that students should practice tracing code, explaining outputs, identifying bugs, reviewing homework solutions, and understanding algorithms rather than only memorizing code. Expected sources: data/discord_course_advice.txt, data/course_advice.txt, or data/reddit_cs_professors.txt. |

---

## Anticipated Challenges
1. Student-generated sources can be subjective and inconsistent. One student may describe a professor as difficult while another student may describe the same professor as helpful. The system should avoid absolute claims and use careful wording like “students in the collected sources suggest” or “the available reviews indicate.”
2. Source attribution could break if metadata is not preserved during chunking. Since the project requires grounded and cited answers, each chunk needs to keep its file path, document title, source type, and chunk ID. Without this metadata, the answer might be correct but not properly cited.

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

## Milestone 3 — Ingestion and chunking:
I will use ChatGPT and Claude to help implement the document loading and chunking functions. I will give the AI my Documents section and Chunking Strategy section as input. I will ask it to create a load_documents() function that reads .txt files from the data/ folder and a chunk_text() function that splits documents by natural units such as reviews, posts, messages, and paragraphs before using fixed-size character splitting.

## Milestone 4 — Embedding and retrieval:
I will use ChatGPT, and Claude to help implement the embedding and retrieval pipeline. I will give the AI my Retrieval Approach section and ask it to write code using sentence-transformers with all-MiniLM-L6-v2. I expect it to help create embeddings for chunks, store them in FAISS or Chroma, and retrieve the top 4 chunks for a user query.

## Milestone 5 — Generation and interface:
I will use AI tools to help build the final answer-generation prompt and a simple user interface. I will provide the AI with my evaluation questions, retrieval approach, and citation requirements. I expect it to help write a prompt that tells the LLM to answer only from retrieved chunks, cite the source files, and admit when the documents do not contain enough information.
