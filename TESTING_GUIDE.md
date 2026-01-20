# Business Assistant - Testing Guide

## Quick Start Testing

### 1. Initialize System (First Time Only)

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# or
source venv/bin/activate  # Linux/Mac

# Initialize database
python -m scripts.init_database

# Initialize vector store with sample policies
python -m scripts.init_vector_store
```

### 2. Run the Application

```bash
python -m business_assistant.run_gradio
```

The app will start at: `http://127.0.0.1:7860`

## Testing Scenarios

### Test 1: Process Excel/CSV File

**Steps:**
1. Open the Gradio UI at `http://127.0.0.1:7860`
2. Click "Upload files" and select a CSV or Excel file
3. Click "Process data" button
4. **Expected Output:**
   - Insights JSON appears in the "Computed insights" text area
   - Visualizations appear in the "Generated Visuals" gallery
   - Status shows "Processing Status: Success"

**Sample Test File:**
Create a CSV file `test_data.csv`:
```csv
date,employee,leave_days,sales
2024-01-01,Alice,5,1000
2024-01-02,Bob,8,1200
2024-01-03,Carol,12,800
2024-01-04,Alice,3,1500
2024-01-05,Bob,10,1100
```

### Test 2: Generate Report with Insights

**Steps:**
1. Paste or upload insights JSON:
```json
{
  "trends": "Leave days increased 15% month-over-month",
  "averages": {"leave_days_avg": 8.5},
  "anomalies": ["Bob has 10 leave days (above average)"],
  "comparisons": {"region": "North has higher leave than South"}
}
```

2. Paste policy documents (separated by `---`):
```
Leave Policy: Employees may take up to 10 days of leave per year.
---
HR Guidelines: Managers must review leave requests exceeding 8 days.
```

3. Enter a question: "Which employees exceeded leave limits?"

4. Click "Generate Report"

5. **Expected Output:**
   - **Summary of Findings**: Shows the insights you provided
   - **Policy Alignment**: Shows how insights align with policies
   - **Recommended Actions**: Provides actionable recommendations
   - **Limitations / Confidence**: Shows confidence level and missing information

### Test 3: Test RAG (Vector Store Retrieval)

**Prerequisites:** Vector store must be initialized

**Steps:**
1. Enter insights that mention keywords from your policies
2. Leave policy input empty (or minimal)
3. Click "Generate Report"

4. **Expected Output:**
   - System should retrieve relevant policies from vector store
   - Console shows: "RAG retrieved X relevant policy chunks"
   - Policy Alignment section references retrieved policies

### Test 4: Test Error Handling

**Test Invalid File:**
1. Try uploading a file that's too large (>50MB)
2. **Expected:** Error message in "Processing Status"

**Test Invalid JSON:**
1. Paste invalid JSON in insights field
2. **Expected:** System falls back to treating as raw text

**Test Empty Inputs:**
1. Leave all fields empty and click "Generate"
2. **Expected:** System provides conservative output with low confidence

### Test 5: Test Rate Limiting

**Steps:**
1. Make 100+ rapid requests
2. **Expected:** After limit, you'll see "Rate limit exceeded" message

### Test 6: Test Prompt Preview

**Steps:**
1. Fill in question, insights, and policies
2. Click "Preview Prompt"
3. **Expected:** See the full prompt that will be sent to LLM

## Command-Line Testing

### Test Processor Directly

```bash
python print_sample.py
```

**Expected Output:**
- Prints structured 4-section output
- Shows audit record
- Demonstrates rule-based fallback

### Run Unit Tests

```bash
pytest tests/
```

**Expected:** All tests pass

## Database Testing

### Check Database Contents

```python
from business_assistant.db import SessionLocal, Decision
db = SessionLocal()
decisions = db.query(Decision).all()
print(f"Total decisions: {len(decisions)}")
db.close()
```

### Check Vector Store

```python
from business_assistant.rag.vector_store import PolicyVectorStore
store = PolicyVectorStore()
count = store.get_document_count()
print(f"Policies in vector store: {count}")
```

## Expected Outputs

### Successful Report Structure

A successful report should have:

1. **Summary of Findings**
   - Key insights from data
   - Trends, averages, anomalies
   - Clear, concise summary

2. **Policy Alignment**
   - Which policies are relevant
   - How insights align with policies
   - Token overlaps or semantic matches

3. **Recommended Actions**
   - Specific, actionable steps
   - Tied to insights and policies
   - Conservative recommendations

4. **Limitations / Confidence**
   - Confidence level (low/moderate/high)
   - Missing information
   - What needs validation

### Sample Output Quality Checks

✅ **Good Output:**
- All 4 sections present
- Recommendations are specific
- Confidence level stated
- Policies referenced

❌ **Poor Output:**
- Missing sections
- Generic recommendations
- No confidence assessment
- Policies not referenced

## Troubleshooting

### Issue: "Vector store is empty"
**Solution:** Run `python -m scripts.init_vector_store`

### Issue: "LLM unavailable"
**Solution:** 
- Check `.env` file has `GROQ_API_KEY`
- System will use rule-based fallback (still works)

### Issue: "Database error"
**Solution:** Run `python -m scripts.init_database`

### Issue: "No visualizations generated"
**Solution:** 
- Check file has numeric columns
- Check file format is CSV/Excel
- Check file size < 50MB

## Performance Testing

### Test Processing Speed

1. Upload a 1000-row CSV file
2. Measure time from upload to insights
3. **Expected:** < 10 seconds for processing

### Test LLM Response Time

1. Generate report with LLM enabled
2. Measure time from click to output
3. **Expected:** 5-15 seconds depending on API

## Integration Testing

### End-to-End Test Flow

1. ✅ Initialize database
2. ✅ Initialize vector store
3. ✅ Upload sample data file
4. ✅ Process data → Get insights
5. ✅ Add policies
6. ✅ Generate report → Get 4-section output
7. ✅ Check database has decision record
8. ✅ Verify exports work

## Validation Checklist

Before considering testing complete:

- [ ] Database initializes successfully
- [ ] Vector store loads policies
- [ ] File upload works (CSV, Excel)
- [ ] Data processing generates insights
- [ ] Report generation works
- [ ] All 4 sections appear in output
- [ ] RAG retrieval works (if vector store populated)
- [ ] Error handling works (invalid inputs)
- [ ] Rate limiting works
- [ ] Database saves decisions
- [ ] Logs are created
- [ ] Exports work (JSON, Markdown, TXT)

## Sample Test Data

### Sample Insights JSON
```json
{
  "trends": "Revenue increased 10% QoQ, Employee satisfaction dropped 5%",
  "averages": {
    "revenue": 50000,
    "satisfaction_score": 7.5
  },
  "anomalies": [
    "Q4 revenue spike: 75000 (50% above average)",
    "Department X satisfaction: 4.2 (below threshold)"
  ],
  "comparisons": {
    "department": "Sales leads in revenue, HR leads in satisfaction",
    "quarter": "Q4 shows highest revenue but lowest satisfaction"
  }
}
```

### Sample Policies
```
Revenue Recognition Policy: All revenue must be recognized when services are delivered, not when payment is received.

Employee Satisfaction Policy: Departments with satisfaction scores below 6.0 must undergo review and improvement plans within 30 days.
```

## Next Steps After Testing

1. Review generated reports for quality
2. Check database for saved decisions
3. Verify logs are being created
4. Test with your own company data
5. Customize policies for your organization
6. Set up production environment variables

