# VaultIQ - Complete Project Structure & File Mapping

This document shows the complete directory structure and which artifact contains each file.

## 📂 Complete Directory Structure

```
VaultIQ-Project/
│
├── vaultiq-backend/                    # Backend (AWS CDK + Python Lambda)
│   ├── aws-cdk-infra/                  # Infrastructure as Code
│   │   ├── bin/
│   │   │   └── vaultiq-infra.ts        → Artifact: "VaultIQ CDK App"
│   │   ├── lib/
│   │   │   └── vaultiq-stack.ts        → Artifact: "VaultIQ CDK Stack"
│   │   ├── package.json                → Artifact: "CDK package.json"
│   │   ├── cdk.json                    → Artifact: "CDK cdk.json"
│   │   └── tsconfig.json               → Artifact: "CDK tsconfig.json"
│   │
│   └── src-lambda-code/                # Python Lambda Functions
│       ├── connectors/
│       │   ├── conflu_connector.py     → Artifact: "Confluence Connector"
│       │   ├── slack_connector.py      → Artifact: "Slack Connector"
│       │   ├── jira_connector.py       → Artifact: "Jira Connector"
│       │   ├── github_connector.py     → Artifact: "GitHub Connector"
│       │   └── requirements.txt        → Artifact: "Connectors requirements.txt"
│       │
│       ├── processing/
│       │   ├── handler.py              → Artifact: "Processing Lambda"
│       │   └── requirements.txt        → Artifact: "Processing requirements.txt"
│       │
│       └── api/
│           ├── main.py                 → Artifact: "API Lambda"
│           └── requirements.txt        → Artifact: "API requirements.txt"
│
└── vaultiq-frontend/                   # Frontend (React + TypeScript)
    ├── src/
    │   ├── components/
    │   │   ├── SearchBar.tsx           → Artifact: "SearchBar Component"
    │   │   ├── AnswerDisplay.tsx       → Artifact: "AnswerDisplay Component"
    │   │   └── SourcesDisplay.tsx      → Artifact: "SourcesDisplay Component"
    │   ├── hooks/
    │   │   └── useApiStream.ts         → Artifact: "useApiStream Hook"
    │   ├── types/
    │   │   └── api.ts                  → Artifact: "API Types"
    │   ├── App.tsx                     → Artifact: "App Component"
    │   ├── main.tsx                    → Artifact: "Main Entry"
    │   └── index.css                   → Artifact: "Index CSS"
    ├── index.html                      → Artifact: "Index HTML"
    ├── package.json                    → Artifact: "Frontend package.json"
    ├── vite.config.ts                  → Artifact: "Vite Config"
    ├── tsconfig.json                   → Artifact: "TypeScript Config"
    ├── tsconfig.node.json              → Artifact: "TypeScript Node Config"
    ├── tailwind.config.js              → Artifact: "Tailwind Config"
    ├── postcss.config.js               → Artifact: "PostCSS Config"
    ├── .env.example                    → Artifact: ".env.example"
    └── README.md                       → Artifact: "Frontend README"
```

## 🚀 Quick Setup Guide

### Option 1: Create Both Projects (PowerShell)

```powershell
# Create both backend and frontend structures
mkdir -p VaultIQ-Project/vaultiq-backend/aws-cdk-infra/bin, VaultIQ-Project/vaultiq-backend/aws-cdk-infra/lib, VaultIQ-Project/vaultiq-backend/src-lambda-code/connectors, VaultIQ-Project/vaultiq-backend/src-lambda-code/processing, VaultIQ-Project/vaultiq-backend/src-lambda-code/api, VaultIQ-Project/vaultiq-frontend/src/components, VaultIQ-Project/vaultiq-frontend/src/hooks, VaultIQ-Project/vaultiq-frontend/src/types

cd VaultIQ-Project
```

### Option 2: Create Backend Only (Command Prompt)

```cmd
mkdir vaultiq-backend
cd vaultiq-backend
mkdir aws-cdk-infra\bin
mkdir aws-cdk-infra\lib
mkdir src-lambda-code\connectors
mkdir src-lambda-code\processing
mkdir src-lambda-code\api
```

### Option 3: Create Frontend Only (Command Prompt)

```cmd
mkdir vaultiq-frontend
cd vaultiq-frontend
mkdir src\components
mkdir src\hooks
mkdir src\types
```

## 📝 File Creation Checklist

### Backend Files (15 files)

**AWS CDK Infrastructure:**
- [ ] `aws-cdk-infra/bin/vaultiq-infra.ts`
- [ ] `aws-cdk-infra/lib/vaultiq-stack.ts`
- [ ] `aws-cdk-infra/package.json`
- [ ] `aws-cdk-infra/cdk.json`
- [ ] `aws-cdk-infra/tsconfig.json`

**Python Connectors:**
- [ ] `src-lambda-code/connectors/conflu_connector.py`
- [ ] `src-lambda-code/connectors/slack_connector.py`
- [ ] `src-lambda-code/connectors/jira_connector.py`
- [ ] `src-lambda-code/connectors/github_connector.py`
- [ ] `src-lambda-code/connectors/requirements.txt`

**Python Processing:**
- [ ] `src-lambda-code/processing/handler.py`
- [ ] `src-lambda-code/processing/requirements.txt`

**Python API:**
- [ ] `src-lambda-code/api/main.py`
- [ ] `src-lambda-code/api/requirements.txt`

**Documentation:**
- [ ] `README.md` (Backend README)

### Frontend Files (16 files)

**React Components:**
- [ ] `src/components/SearchBar.tsx`
- [ ] `src/components/AnswerDisplay.tsx`
- [ ] `src/components/SourcesDisplay.tsx`

**Hooks:**
- [ ] `src/hooks/useApiStream.ts`

**Types:**
- [ ] `src/types/api.ts`

**App Files:**
- [ ] `src/App.tsx`
- [ ] `src/main.tsx`
- [ ] `src/index.css`

**Configuration:**
- [ ] `index.html`
- [ ] `package.json`
- [ ] `vite.config.ts`
- [ ] `tsconfig.json`
- [ ] `tsconfig.node.json`
- [ ] `tailwind.config.js`
- [ ] `postcss.config.js`
- [ ] `.env.example`
- [ ] `README.md` (Frontend README)

## 🎯 Step-by-Step Setup Process

### Step 1: Create Directories

Use the Windows batch scripts or PowerShell commands above.

### Step 2: Copy Files from Artifacts

Go through each artifact in Claude's response and copy the content into the corresponding file based on the mapping above.

### Step 3: Install Backend Dependencies

```bash
# Install CDK dependencies
cd vaultiq-backend/aws-cdk-infra
npm install

# Install Python dependencies (do this for each Lambda folder)
cd ../src-lambda-code/connectors
pip install -r requirements.txt -t .

cd ../processing
pip install -r requirements.txt -t .

cd ../api
pip install -r requirements.txt -t .
```

### Step 4: Install Frontend Dependencies

```bash
cd vaultiq-frontend
npm install
```

### Step 5: Configure Environment

**Backend:**
- Configure AWS credentials
- Bootstrap CDK: `cdk bootstrap`
- Deploy: `cdk deploy`
- Configure secrets in AWS Secrets Manager

**Frontend:**
- Copy `.env.example` to `.env`
- Update `VITE_API_URL` with your API Gateway URL

### Step 6: Run Applications

**Backend:**
```bash
# Deploy infrastructure
cd vaultiq-backend/aws-cdk-infra
cdk deploy
```

**Frontend:**
```bash
# Start development server
cd vaultiq-frontend
npm run dev
```

## 🔗 Integration Points

1. **Frontend → Backend**: 
   - Frontend calls `POST /api/query`
   - Configure `VITE_API_URL` in `.env`

2. **Backend → AWS Services**:
   - Lambda → S3 (data lake)
   - Lambda → DynamoDB (metadata)
   - Lambda → OpenSearch (vectors)
   - Lambda → Bedrock (AI/embeddings)

3. **Connectors → External APIs**:
   - Confluence API
   - Slack API
   - Jira API
   - GitHub API

## 📊 Deployment Flow

```
1. Deploy Backend (CDK)
   ↓
2. Configure Secrets
   ↓
3. Test Connectors
   ↓
4. Verify Data in S3/OpenSearch
   ↓
5. Test API Endpoint
   ↓
6. Configure Frontend .env
   ↓
7. Build & Deploy Frontend
   ↓
8. Production Ready! 🎉
```

## 🆘 Quick Troubleshooting

**Backend Issues:**
- CDK deploy fails → Check AWS credentials
- Lambda timeout → Increase memory/timeout in stack
- No search results → Check OpenSearch index

**Frontend Issues:**
- API connection fails → Verify `.env` URL
- Build errors → Run `npm install` again
- Styles not loading → Check Tailwind config

## 📚 Documentation References

- Backend: See `vaultiq-backend/README.md`
- Frontend: See `vaultiq-frontend/README.md`
- AWS CDK: https://docs.aws.amazon.com/cdk/
- React 18: https://react.dev/

---

**Total Files: 31 files across 2 main directories**
**Total Artifacts: 26+ artifacts provided by Claude**