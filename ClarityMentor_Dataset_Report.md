# ClarityMentor Fine‑Tuning Dataset Report

**Project name:** ClarityMentor  
**Owner:** Lebi Raja (Lebi)  
**Machine:** RTX 4050 Laptop GPU (~6GB VRAM)  
**Fine‑tuning method:** QLoRA (4‑bit) + LoRA adapters  

---

## 1) Executive Summary

This project fine‑tunes a small instruction LLM into a **mature philosophical mentor** that provides **clarity, perspective, and grounded advice**. The model is designed to:

- Ask **clarifying questions** (Socratic coaching) when the user is vague
- Offer **philosophical reframes** (Stoicism / existentialism / humanism / absurdism)
- Be explicitly **atheist‑friendly** (no religious preaching; rational + compassionate)
- Provide **relationship & conflict guidance** with emotional intelligence
- Give **motivational clarity** without being cringe or overly “therapy-like”

The dataset stack is intentionally diverse:

- **Empathy + emotional conversations** → tone and emotional alignment
- **Counseling-style guidance** → structured advice, coping strategies, clarity building
- **Philosophy QA + encyclopedic content** → conceptual depth + life meaning
- **Quotes datasets** → punchy “reel‑style” wisdom + memorable lines
- **Reddit-style relationship conflicts** → realistic messy situations + perspective taking

End output: a fine‑tuned LoRA adapter (**ClarityMentor‑LoRA**) that turns a base model (recommended: `Qwen2.5-1.5B-Instruct`) into a consistent mentor persona.

---

## 2) Dataset Inventory (Downloaded Sources)

Your dataset directory structure:

```
~/projects/mentor/
  Empathetic Dialogues (Facebook AI) 25k.zip
  empatheticdialogues/
  empathetic_dialogues_llm/
  Mental Health Conversational Data.zip
  Mental Health Counseling Conversations.zip
  reddit_dataset_170/
  hf_datasets/
    AiresPucrs/
    datastax/
    Felladrin/
    Langame/
    LuangMV97/
    sayhan/
  kaggle_datasets/
    goodreads-quotes/
    inspirational-quotes/
    quotes-500k/
```

Below is what each dataset contributes, why it is used, and how it will be converted for fine‑tuning.

---

## 3) Detailed Dataset Use‑Cases

### A) Empathy + Emotional Intelligence

#### 1) **Empathetic Dialogues (Facebook AI) – 25k**
**Files:**
- `Empathetic Dialogues (Facebook AI) 25k.zip`
- `empatheticdialogues/`

**What it contains:**
- Human conversations grounded in emotional situations (sadness, regret, anger, joy, anxiety etc.)

**Why we use it:**
- Trains the assistant to **understand emotions**, respond gently, and build trust.
- Provides “human warmth” and natural flow in conversations.

**How it helps ClarityMentor:**
- Enables the mentor to **validate feelings** without being dramatic.
- Makes responses sound mature rather than robotic.

**How we will process it:**
- Convert each conversation turn into chat format.
- Add ClarityMentor system prompt on top.
- Optionally rewrite assistant messages into the target template:
  1) empathy + summary
  2) clarifying questions
  3) reframe
  4) steps
  5) reflection prompt

---

#### 2) **Empathetic Dialogues LLM Format**
**Folder:** `empathetic_dialogues_llm/`

**What it contains:**
- Same dataset, already formatted for instruction/LLM training.

**Why we use it:**
- Faster conversion pipeline (less preprocessing).

**How it helps ClarityMentor:**
- Standardizes early training data.

---

### B) Counseling + Clarity Coaching

#### 3) **Mental Health Counseling Conversations**
**File:** `Mental Health Counseling Conversations.zip`

**What it contains:**
- Q/A or multi-turn dialogues where the assistant responds with supportive guidance.

**Why we use it:**
- It teaches:
  - asking the right questions
  - structuring advice
  - coping strategies
  - calm tone during tough situations

**How it helps ClarityMentor:**
- Converts the model from “chatty” to **actionable clarity coaching**.

**Processing plan:**
- Filter for safe/ethical responses.
- Ensure the assistant avoids medical claims.
- Normalize tone to atheism‑friendly, non‑religious guidance.

---

#### 4) **Mental Health Conversational Data**
**File:** `Mental Health Conversational Data.zip`

**What it contains:**
- Broader mental health conversational samples (often shorter, more varied).

**Why we use it:**
- Increases coverage of real life cases:
  - overthinking
  - loneliness
  - breakup pain
  - confidence
  - fear
  - motivation collapse

**How it helps:**
- Helps model generalize beyond a narrow counseling style.

**Processing plan:**
- Deduplicate repeated patterns.
- Remove low quality or generic one‑liners.
- Rewrite into ClarityMentor structured answer template.

---

#### 5) **HF Dataset: Felladrin – pretrain mental health counseling conversations**
**Folder:** `hf_datasets/Felladrin/`

**What it contains:**
- Counseling-oriented conversational dataset hosted on HuggingFace.

**Why we use it:**
- Adds more high‑quality “mentor response” patterns.
- Improves consistency in supportive tone.

**Processing plan:**
- Convert to chat JSONL.
- Add safety filters.

---

#### 6) **HF Dataset: LuangMV97 – Empathetic Counseling Dataset**
**Folder:** `hf_datasets/LuangMV97/`

**Why we use it:**
- Strong guidance and clarity patterns.
- Often cleaner than raw Reddit.

---

### C) Philosophy + Meaning of Life + Atheism-Compatible Depth

#### 7) **HF Dataset: sayhan – Strix Philosophy QA**
**Folder:** `hf_datasets/sayhan/`

**What it contains:**
- Philosophy questions and answers (ethics, meaning, mind, identity, suffering).

**Why we use it:**
- This is the dataset that gives your model:
  - philosophical reasoning
  - depth and worldview
  - existential clarity

**How it helps ClarityMentor:**
- Without this, the model becomes “therapy chat” only.
- With this, the model feels like a **wise philosopher‑mentor**.

**Processing plan:**
- Convert QA into mentor conversational format.
- Add real-life framing prompts, e.g.:
  - User: “I feel like life has no meaning.”
  - Assistant: philosophical reframe + steps + reflection.

---

#### 8) **HF Dataset: AiresPucrs – Stanford Encyclopedia of Philosophy**
**Folder:** `hf_datasets/AiresPucrs/`

**What it contains:**
- Long-form philosophical encyclopedia text.

**Why we use it:**
- Best used for **RAG** OR for generating curated Q/A pairs.
- Helps increase concept accuracy and reduce shallow advice.

**Important note:**
- We should NOT dump long encyclopedia articles directly into fine‑tuning.
- Instead, we:
  1) generate Q/A or short “mentor explanations” from it
  2) optionally use it later as retrieval knowledge (RAG)

---

### D) Motivational Wisdom + “Reels Style” Punch

#### 9) **HF Dataset: datastax – Philosopher Quotes**
**Folder:** `hf_datasets/datastax/`

**What it contains:**
- Quotes from philosophers.

**Why we use it:**
- Teaches short, memorable wisdom.
- Improves writing style.

**How we use it properly:**
- Quotes alone create shallow output.
- We will transform each quote into:
  - situation prompt
  - quote as anchor
  - explanation
  - action steps

---

#### 10) Kaggle Quotes Datasets
**Folders:**
- `kaggle_datasets/quotes-500k/`
- `kaggle_datasets/goodreads-quotes/`
- `kaggle_datasets/inspirational-quotes/`

**Why we use them:**
- Inject “Instagram motivational” language.
- Give variety of phrasing.
- Strengthen punchy clarity.

**How we avoid making it cringe:**
- We do NOT train the model to only output quotes.
- We use quotes as **supporting lines** inside structured advice.

**Transformation example:**
- User problem → choose relevant quote → explain it → give steps → reflection question.

---

### E) Relationship & Social Conflict Realism

#### 11) **reddit_dataset_170**
**Folder:** `reddit_dataset_170/`

**What it contains:**
- Online posts/comments. Likely includes relationship problems, social conflicts, raw human conversations.

**Why we use it:**
- Adds messy real‑world cases:
  - betrayal
  - jealousy
  - communication issues
  - family conflict
  - boundaries

**Main risk:**
- Contains toxic, biased, hateful, or harmful advice.

**How we safely use it:**
- **Strict filtering**:
  - remove NSFW
  - remove hate speech, harassment
  - remove self-harm encouragement
  - remove extremist content
- Rewrite assistant responses into:
  - mature, empathetic, non‑toxic guidance
  - “understand both sides” framing

---

#### 12) HF Dataset: Langame – conversation-starters
**Folder:** `hf_datasets/Langame/`

**What it contains:**
- Conversation prompts.

**Why we use it:**
- Helps train the model to ask:
  - better questions
  - explore context
  - open up the user

This dataset is valuable for training **Socratic style prompting**.

---

## 4) Why These Datasets Together Work

ClarityMentor needs **both heart and brain**.

- Empathy datasets → makes the model feel human and safe
- Counseling datasets → teaches practical coaching and structured advice
- Philosophy datasets → gives depth and meaning-of-life frameworks
- Quotes datasets → provides powerful language and motivational impact
- Reddit dataset → exposes messy real situations for stronger generalization

This stack is designed to create a model that doesn’t just “comfort the user”, but:

✅ **clarifies the situation**  
✅ **expands perspective**  
✅ **suggests mature actions**  
✅ **asks the right questions**  

---

## 5) End Goal (What We Are Building)

### Final Model Capabilities
ClarityMentor should:

1) **Detect ambiguity** and ask questions before advice
2) Provide a **philosophical reframe** grounded in realism
3) Be **atheist-friendly** and rational
4) Offer **relationship advice** that is mature and empathetic
5) Encourage **personal responsibility + boundaries**
6) Avoid harmful guidance; suggest professional help in high‑risk scenarios

### Model Deliverables
- `claritymentor_train.jsonl` / `claritymentor_eval.jsonl`
- Fine‑tuned QLoRA adapter: `claritymentor-lora/`
- Inference script / chat demo
- GitHub repo: dataset pipeline + training pipeline + evaluation prompts

---

## 6) Training Strategy Overview (RTX 4050 6GB)

### Recommended Base Model
- `Qwen/Qwen2.5-1.5B-Instruct`

### Fine‑tuning Method
- QLoRA:
  - 4‑bit base model loading
  - LoRA adapters trained on top

### Key Hyperparameters (safe for 6GB)
- `max_seq_length`: 1024
- `per_device_train_batch_size`: 1
- `gradient_accumulation_steps`: 16
- `epochs`: 1–2
- `learning_rate`: ~2e-4
- `lora_r`: 16
- `target_modules`: `q_proj`, `v_proj`

---

## 7) Data Processing Plan (High Level)

### Step 1: Standardize Format
Convert everything into **chat JSONL**:

```json
{"messages": [
  {"role":"system","content":"<ClarityMentor system prompt>"},
  {"role":"user","content":"..."},
  {"role":"assistant","content":"..."}
]}
```

### Step 2: Cleaning + Filtering
- remove empty / too short samples
- deduplicate
- remove toxic content
- ensure no self-harm encouragement

### Step 3: Style Alignment
Rewrite assistant responses to the ClarityMentor template:
1) empathy
2) clarifying questions
3) reframe
4) steps
5) reflection question

### Step 4: Mix Datasets
Suggested starting ratio:
- 30% counseling datasets
- 25% empathetic dialogues
- 20% philosophy QA
- 15% reddit relationship conflicts (filtered)
- 10% quotes → advice converted

### Step 5: Train + Evaluate
- small eval set with categories:
  - meaning of life
  - atheism questions
  - relationship conflict
  - anxiety/overthinking
  - decision paralysis

---

## 8) Risks & Mitigations

### Risk 1: Toxic Reddit influence
**Mitigation:** strict filters + rewriting into mature tone.

### Risk 2: Model becomes “therapy bot”
**Mitigation:** increase philosophy QA weight and add reframing prompts.

### Risk 3: Cringe motivation
**Mitigation:** use quotes only as anchor lines; enforce grounded action steps.

### Risk 4: Harmful advice in sensitive situations
**Mitigation:** add safety training examples:
- encourage professional support
- crisis hotlines suggestions (generic, non‑region specific)
- avoid diagnosis

---

## 9) Success Criteria

ClarityMentor is successful if:

- It consistently asks clarifying questions when needed
- It offers deep, rational philosophical insight
- It remains empathetic and respectful
- It handles relationship topics maturely
- It provides a practical action plan
- It avoids toxic/harmful outputs

---

## 10) Next Immediate Actions

1) Write `system_prompt.txt` for the model persona
2) Build dataset converter scripts:
   - `convert_empathetic_dialogues.py`
   - `convert_counseling.py`
   - `convert_philosophy_qa.py`
   - `convert_quotes_to_advice.py`
   - `reddit_filter_and_rewrite.py`
3) Merge + mix into:
   - `claritymentor_train.jsonl`
   - `claritymentor_eval.jsonl`
4) Train QLoRA adapter on RTX 4050
5) Run evaluation prompts

---

**Report generated for:** Lebi Raja  
**Project:** ClarityMentor mentor LLM fine‑tuning
