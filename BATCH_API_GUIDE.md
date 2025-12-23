# OpenAI Batch API Guide

## Why Use Batch API?

✅ **50% Cost Reduction** - Half the price of regular API  
✅ **Simple Workflow** - Submit once, retrieve when ready  
✅ **Bulk Processing** - Process thousands of articles efficiently  
✅ **No Rate Limits** - No need to manage API rate limits  

---

## Complete Workflow

### Step 1: Prepare Batch Requests

```bash
python summarize_batch_prepare.py
```

**What it does:**
- Queries database for articles with text
- Creates `batch_requests.jsonl` file
- Each article becomes one request
- Shows cost estimate

**Output:**
```
Found 2592 articles to summarize
Created batch_requests.jsonl with 2592 requests

Cost Estimate:
  Est. cost: $3.12 (with 50% batch discount)
  Regular API cost: $6.24
  Savings: $3.12
```

---

### Step 2: Submit Batch

```bash
python summarize_batch_submit.py
```

**What it does:**
- Uploads `batch_requests.jsonl` to OpenAI
- Creates batch job
- Saves batch ID to database
- Creates `batch_info.txt` for tracking

**Output:**
```
✓ Uploaded file: file-abc123
✓ Batch created: batch-xyz789
  Status: validating
  Total requests: 2592
```

---

### Step 3: Check Status (Repeat)

```bash
python summarize_batch_check.py
```

**What it does:**
- Retrieves current batch status
- Shows progress and completion estimate
- Run this periodically to check progress

**Example outputs:**

**While processing:**
```
Batch ID: batch-xyz789
Status: in_progress
Request counts:
  Total: 2592
  Completed: 1458
  Failed: 0
  Progress: 56.3%

⏳ Batch is still processing...
Check again later
```

**When complete:**
```
Batch ID: batch-xyz789
Status: completed
Completed at: 2025-12-19 20:45:32
Duration: 215 minutes

Request counts:
  Total: 2592
  Completed: 2589
  Failed: 3
  Progress: 100.0%

✓ Output file ready: file-output123
Run: python summarize_batch_process.py
```

---

### Step 4: Process Results

```bash
python summarize_batch_process.py
```

**What it does:**
- Downloads results from OpenAI
- Saves to `batch_results.jsonl` (backup)
- Updates database with summaries
- Shows final statistics

**Output:**
```
[STEP 1] Downloading results...
✓ Saved results to batch_results.jsonl

[STEP 2] Processing results and updating database...
  ✓ Processed 100 articles...
  ✓ Processed 200 articles...
  ...
  ✓ Processed 2589 articles...

PROCESSING COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Articles with text: 2592
Articles with summaries: 2589 (99.9%)

This batch:
  ✓ Successfully summarized: 2589
  ✗ Errors: 3
  📊 Total tokens used: 3,847,291
  💰 Estimated cost: $3.08 (with 50% batch discount)

✓ Database updated
```

---

## Timeline

| Stage | Duration | Action |
|-------|----------|--------|
| Prepare | < 1 minute | Run once |
| Submit | < 1 minute | Run once |
| **Processing** | **2-6 hours** | **Wait (automatic)** |
| Check | < 10 seconds | Run every hour |
| Process | 1-2 minutes | Run once when complete |

**Total active time:** ~5 minutes  
**Total wait time:** 2-6 hours (hands-off)

---

## Batch Statuses

| Status | Meaning | Action |
|--------|---------|--------|
| `validating` | OpenAI is validating requests | Wait |
| `in_progress` | Processing articles | Wait, check periodically |
| `finalizing` | Almost done | Wait |
| `completed` | ✅ Ready to download | Run process script |
| `failed` | ❌ Error occurred | Check error logs |
| `expired` | Took > 24 hours | Resubmit |
| `cancelled` | Manually cancelled | Resubmit if needed |

---

## Cost Breakdown

### Batch API Pricing (50% off)
- Input: $0.075 per 1M tokens
- Output: $0.300 per 1M tokens

### Example Calculation (2,592 articles)
```
Average input:  1,500 tokens/article = 3,888,000 tokens
Average output:   500 tokens/article = 1,296,000 tokens

Input cost:  3,888,000 / 1M * $0.075 = $0.29
Output cost: 1,296,000 / 1M * $0.300 = $0.39
Total: $0.68 per 1,000 articles

For 2,592 articles: ~$1.76
With variations in length: $2.50-5.00 typical
```

### Regular API (for comparison)
Same calculation * 2 = $5.00-10.00

**Savings: 50%** 💰

---

## Troubleshooting

### "No batch found in database"
- You haven't submitted a batch yet
- Run: `python summarize_batch_submit.py`

### "Batch not completed yet"
- Still processing
- Run: `python summarize_batch_check.py` to check progress
- Typical wait: 2-6 hours

### "Some requests failed"
- Check `batch_results.jsonl` for error details
- Failed articles can be reprocessed individually
- Common causes: invalid text format, extremely long articles

### Batch expired (>24 hours)
- Rerun from step 1
- Adjust `max_tokens` if articles are very long

---

## Files Generated

| File | Purpose | Keep? |
|------|---------|-------|
| `batch_requests.jsonl` | Input requests | Optional (can delete after) |
| `batch_results.jsonl` | Output results | Yes (backup) |
| `batch_info.txt` | Tracking info | Yes (reference) |

---

## Best Practices

1. ✅ Run during off-peak hours (submit and forget)
2. ✅ Keep `batch_results.jsonl` as backup
3. ✅ Check status every 1-2 hours
4. ✅ Process results as soon as complete
5. ✅ Export to CSV after processing

---

## Quick Reference

```bash
# Complete workflow
python summarize_batch_prepare.py   # 1 min
python summarize_batch_submit.py     # 1 min
# Wait 2-6 hours
python summarize_batch_check.py      # Check status
python summarize_batch_process.py    # 2 min when ready

# Export results
python export_to_csv.py
```

**Total cost:** $2.50-5 (50% off)  
**Total time:** ~5 minutes active + 2-6 hours wait

