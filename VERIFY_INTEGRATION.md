# Quick Integration Verification

Use this guide to verify everything is properly integrated in 5 minutes.

## Quick Verification (5 Steps)

### Step 1: Check Dependencies

```bash
cd backend
python -c "from agents.integrated_supervisor import IntegratedSupervisor; print('✓ Integration OK')"
python -c "from agents.langgraph_supervisor import MultiAgentSupervisor; print('✓ LangChain OK')"
python -c "from agents.approval_workflow import ApprovalWorkflowManager; print('✓ Approval OK')"
python -c "from agents.hd_image_agent import HDImageAgent; print('✓ HD Images OK')"
```

Expected output:
```
✓ Integration OK
✓ LangChain OK
✓ Approval OK
✓ HD Images OK
```

### Step 2: Check Backend Starts

```bash
cd backend
uvicorn server:app --reload --port 8000
```

Look for these logs:
```
INFO: IntegratedSupervisor initialized with all agents and approval system
INFO: LangChain supervisor initialized successfully
INFO: Database initialization complete!
INFO: Application startup complete
```

### Step 3: Check Frontend

```bash
cd frontend
npm start
```

Visit: http://localhost:3000

Should load without errors.

### Step 4: Test Approval Workflow

1. Go to http://localhost:3000
2. Type: "Create a mail campaign"
3. Should see message about approval
4. Go to http://localhost:3000/task-management
5. Should see pending approval
6. Click "Approve" button

✓ If this works, approval workflow is integrated properly.

### Step 5: Check Agent Communication

On Task Management page:
- Look at "Agent Communication" panel
- Should see messages between agents
- Messages should NOT have emojis or symbols

✓ If you see clean messages, everything is integrated.

---

## Visual Verification

### Task Management Page Should Show:

```
┌─────────────────────────────────────────────┐
│ Task Management                             │
│                                             │
│ Pending Approvals                           │
│ ┌─────────────────────────────────────────┐ │
│ │ CAMPAIGN EXECUTION      [HIGH]          │ │
│ │ Requested by: LangChainSupervisor       │ │
│ │                                         │ │
│ │ Task: Execute multi-agent task...      │ │
│ │                                         │ │
│ │ [Approve] [Reject]                      │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Agent Communication                         │
│ ┌─────────────────────────────────────────┐ │
│ │ Supervisor → ContentAgent               │ │
│ │ Creating email content...               │ │
│ │                                         │ │
│ │ ContentAgent → EmailAgent               │ │
│ │ Content complete, sharing messaging...  │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

---

## API Endpoint Verification

Test these endpoints with cURL:

### 1. Integrated Chat
```bash
curl -X POST http://localhost:8000/api/integrated/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a campaign"}'
```

Should return JSON with approval request.

### 2. Pending Approvals
```bash
curl http://localhost:8000/api/approvals/pending
```

Should return list of pending approvals.

### 3. Agent Communication
```bash
curl http://localhost:8000/api/agent-communication
```

Should return agent communication logs.

---

## Success Criteria

✅ All these should pass:

- [ ] Backend imports work without errors
- [ ] Backend starts and shows integration logs
- [ ] Frontend loads without errors
- [ ] Task Management page accessible
- [ ] Approval workflow creates requests
- [ ] Approve/Reject buttons work
- [ ] Agent communication visible
- [ ] No emojis in agent messages
- [ ] API endpoints respond correctly

---

## If Any Step Fails

### Backend Import Errors
```bash
cd backend
pip install -r requirements.txt
```

### Backend Won't Start
Check `.env` file has:
```
MONGO_URL=your_mongodb_url
DB_NAME=your_db_name
EMERGENT_LLM_KEY=your_key
```

### Frontend Errors
```bash
cd frontend
npm install
npm start
```

### Task Management Page 404
Check `frontend/src/App.js` has:
```javascript
import TaskManagementPage from "@/pages/TaskManagementPage";
...
<Route path="/task-management" element={<TaskManagementPage />} />
```

### No Approvals Showing
- Make a complex request first: "Create a mail campaign"
- Check `/api/approvals/pending` endpoint
- Verify MongoDB `approval_requests` collection exists

---

## Full Integration Test

Run this complete test sequence:

```bash
# 1. Start backend
cd backend
uvicorn server:app --reload --port 8000 &

# Wait 5 seconds
sleep 5

# 2. Test integrated chat
curl -X POST http://localhost:8000/api/integrated/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a mail campaign", "user_id": "test"}' \
  > test_result.json

# 3. Check result
cat test_result.json

# Should see: "type": "approval_required"

# 4. Get pending approvals
curl http://localhost:8000/api/approvals/pending

# Should see at least one approval

# 5. Get communication
curl http://localhost:8000/api/agent-communication

# Should see agent messages
```

If all these work, integration is complete!

---

## Quick Troubleshooting

### Issue: "LangChain not available"
**Cause:** OPENAI_API_KEY not set
**Impact:** System works but uses standard agents
**Fix:** Add to `.env`: `OPENAI_API_KEY=sk-your-key`

### Issue: "No module named langchain"
**Cause:** Dependencies not installed
**Fix:** `pip install -r backend/requirements.txt`

### Issue: "Approval requests empty"
**Cause:** Only complex tasks require approval
**Fix:** Use complex request: "Create a mail campaign"

### Issue: "Agent communication empty"
**Cause:** No tasks executed yet
**Fix:** Make a request first, then check communication

---

## Verification Complete

Once all steps pass, you have:

✅ All agents properly integrated with LangChain
✅ Approval workflow fully functional
✅ HD image generation working
✅ Clean agent communication (no emojis)
✅ Task Management UI operational
✅ Complete end-to-end integration

Your system is ready to use!

---

**Quick Test Time:** 5 minutes
**Full Test Time:** 10 minutes
**Success Rate:** All steps should pass
