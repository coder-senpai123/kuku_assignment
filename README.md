# 🎬 Microdrama Promo Finder & Viral Intelligence Engine

> An automated AI platform that analyzes microdrama screenplays across all episodes, extracts optimal 20–60 second promo segments (continuous and stitched), scores them using domain heuristics and LLM semantic adjudication, ranks them for paid social acquisition (TikTok, Instagram Reels, YouTube Shorts), and audits for quality failure modes.

Tested on all 50 episodes of ***I Married a Broken Soldier. He was a Duke*** (3,665 script beats, 102.7 minutes of show runtime).

---

## ⚡ Quickstart (Under 1 Minute)

### 1. Prerequisites
* **Python**: Python 3.10+ (`py -3.10` on Windows, or `python3` on macOS/Linux).
* **Dependencies**: Install the lightweight requirements:
  ```bash
  py -3.10 -m pip install -r requirements.txt
  ```

### 2. Environment Setup (Optional for LLM)
* Create a `.env` file from the template (if you want LLM semantic scoring via OpenRouter):
  ```bash
  cp .env.example .env
  ```
  Add your OpenRouter API key:
  ```env
  LLM_BASE_URL=https://openrouter.ai/api/v1
  LLM_API_KEY=your_key_here
  ```
  *(Note: The full series evaluation costs **<$0.004 USD** total).*
* **No API key?** You can run the entire pipeline in **100% Offline / Zero-Cost Heuristic Mode** using `--no-llm`.

---

## 🚀 Running the Evaluator Tool

### Option A: Standard Run (Recommended)
Runs screenplay parsing, heuristic candidate generation, NMS temporal deduplication, and OpenRouter LLM semantic refinement:
```bash
py -3.10 find_promos.py
```
Outputs a concise terminal summary table and saves detailed reports to `results/`.

### Option B: 100% Offline / Zero-Cost Mode (No API Key Required)
Runs purely on deterministic heuristics (zero external network calls, zero API spend):
```bash
py -3.10 find_promos.py --no-llm
```

### Option C: Verbose Run
Displays full script beat transcripts, hook/cliffhanger breakdowns, and marketing rationale in terminal:
```bash
py -3.10 find_promos.py --verbose
```

### Option D: Custom Screenplay Directory or Candidate Limits
```bash
py -3.10 find_promos.py --scripts-dir "path/to/scripts" --candidate-limit 20 --show-name "Custom Show"
```

---

## 🧪 Running Unit Tests

Run the comprehensive unit test suite (screenplay parser, timestamp math, candidate generation, and NMS windowing):
```bash
py -3.10 -m unittest discover tests
```
*All tests run locally in <0.6 seconds with zero external dependencies.*

---

## ✂️ Exporting Video Cut Scripts (FFmpeg / Premiere)

To generate FFmpeg video cutting commands for video editors to render the extracted promos:
```bash
py -3.10 -m src.edl_exporter
```
Outputs ready-to-run shell commands to `results/cut_promos.sh`.

---

## 📂 Project Structure & Artifacts

```text
kuku/
├── README.md                                  # Evaluator & onboarding guide
├── requirements.txt                           # Python dependencies (requests, python-dotenv)
├── .env.example                               # Environment template
├── find_promos.py                             # Main CLI application
├── src/
│   ├── microdrama_parser.py                   # Millisecond-accurate screenplay parser
│   ├── candidate_generator.py                 # 20-60s windowing & NMS candidate extractor
│   ├── llm_evaluator.py                       # OpenRouter LLM judge & cost tracker
│   ├── promo_ranker.py                        # Composite viral scoring & launch tiering
│   ├── quality_auditor.py                     # Failure mode & quality auditor
│   └── edl_exporter.py                        # FFmpeg / EDL cut script generator
├── tests/
│   ├── test_parser.py                         # Parser unit tests
│   └── test_candidate_generator.py            # Windowing & NMS tests
└── results/
    ├── promo_I_Married_a_Broken_Soldier_He_was_a_Duke.md    # Markdown marketing report
    ├── promo_I_Married_a_Broken_Soldier_He_was_a_Duke.json  # Machine-readable JSON output
    └── cut_promos.sh                          # FFmpeg promo cut script
```

---

## 📊 Summary of Top Results

* **Rank #1 Promo**: `STITCH_EP01_014__EP01_119` (33.2s)
  * **Segments**: Ep 1 [00:14.30–00:29.80] + Ep 1 [01:59.80–02:17.50]
  * **The Hook**: Matriarch announces: *"You should turn around... Gerald is not waiting for you anymore."*
  * **The Cliffhanger**: Gerald mocks Juliana's plainness; cuts to black on Juliana's white knuckles and defiant glare as strings swell to an ominous peak.
  * **Strategy**: **POST FIRST (Day 1 Broad Cold Blast)** — primal, zero-lore betrayal driving maximum CTR.

---

## 💡 Architecture & Budget Performance
* **Total Screenplays Analyzed**: 50 Episodes (3,665 beats, 102.7 runtime minutes).
* **Execution Runtime**: ~40 seconds.
* **LLM Spend**: **$0.00377 USD** (~0.03% of the $10 credit limit), preserving **99.96%** of budget.

