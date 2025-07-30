# Resume Shortlisting Tool 🚀
An AI-powered resume shortlisting application that uses CrewAI and OpenAI to automatically analyze resumes against job descriptions, extract candidate information, and generate personalized interview questions.

## ✨ Features
- **AI-Powered Analysis**: Uses OpenAI GPT models through CrewAI for intelligent resume evaluation
- **Automatic Information Extraction**: Extracts candidate names, phone numbers, and emails from PDFs
- **Smart Scoring**: Scores candidates from 1-10 based on job requirement alignment
- **Interview Question Generation**: Creates personalized interview questions for each candidate
- **Multiple Export Formats**: Export results as CSV or professionally formatted PDF reports
- **Interactive Web Interface**: Built with Streamlit for easy use
- **REST API**: FastAPI backend for programmatic access
- **Configurable Thresholds**: Adjustable scoring thresholds and processing limits
- **Real-time Processing**: Live progress tracking during resume analysis
- **Cloud Ready**: Docker containerized with GCP deployment support

## 🛠️ Technology Stack
- **Frontend**: Streamlit
- **Backend API**: FastAPI
- **AI Framework**: CrewAI with OpenAI GPT-4o-mini
- **PDF Processing**: PyPDF2
- **Report Generation**: ReportLab
- **Data Processing**: Pandas
- **Configuration**: YAML
- **Containerization**: Docker
- **Cloud Platform**: Google Cloud Platform (Cloud Run)

## 📋 Prerequisites
- Python ≥ 3.10, <3.14
- OpenAI API Key ([Get one here](https://platform.openai.com/account/api-keys))
- Docker (for containerized deployment)
- Google Cloud SDK (for GCP deployment)

## 🚀 Installation

### Method 1: Using pip (Recommended)

```bash
git clone https://github.com/Kartavya-AI/Resume-Shortlisting.git
cd Resume-Shortlisting

pip install -e .

pip install -e ".[dev]"
```

### Method 2: Using Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -

git clone https://github.com/Kartavya-AI/Resume-Shortlisting.git
cd Resume-Shortlisting
poetry install
```

### Method 3: Manual Installation

```bash
git clone https://github.com/Kartavya-AI/Resume-Shortlisting.git
cd Resume-Shortlisting

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install streamlit crewai crewai-tools pandas PyPDF2 reportlab PyYAML pydantic openai fastapi uvicorn gunicorn
```

## 🏃‍♂️ Quick Start

### Streamlit Web Application

1. **Run the Application**:
   ```bash
   streamlit run app.py
   ```

2. **Open in Browser**: The app will automatically open at `http://localhost:8501`

3. **Enter API Key**: Input your OpenAI API key in the configuration section

4. **Upload Resumes**: Upload PDF resumes (up to 20 files)

5. **Add Job Description**: Paste the complete job description

6. **Analyze**: Click "Analyze and Shortlist Resumes" to start processing

### FastAPI Backend

1. **Run the API Server**:
   ```bash
   uvicorn api:app --host 0.0.0.0 --port 8000
   ```

2. **Access API Documentation**: Visit `http://localhost:8000/docs` for interactive API documentation

3. **API Endpoints**:
   - `GET /`: Health check endpoint
   - `POST /shortlist-resumes/`: Main endpoint for resume analysis

## 🐳 Docker Deployment

### Building the Docker Image

The project includes a production-ready Dockerfile optimized for deployment:

```bash
# Build the Docker image
docker build -t resume-shortlisting .

# Run the container
docker run -p 8080:8080 -e OPENAI_API_KEY=your_api_key_here resume-shortlisting
```

### Docker Configuration Details

The Dockerfile includes:
- **Base Image**: `python:3.11-slim-bullseye` for optimal size and security
- **Environment Variables**: 
  - `PYTHONDONTWRITEBYTECODE=1` (prevents .pyc files)
  - `PYTHONUNBUFFERED=1` (ensures real-time logging)
- **Production Server**: Gunicorn with Uvicorn workers
- **Port**: Exposes port 8080 (required for Cloud Run)
- **Optimization**: Multi-stage build with dependency caching

### Environment Variables

Set the following environment variables when running the container:

```bash
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=your_openai_api_key \
  -e PORT=8080 \
  resume-shortlisting
```

## ☁️ Google Cloud Platform Deployment

### Prerequisites for GCP Deployment

1. **Install Google Cloud SDK**:
   ```bash
   # Follow instructions at: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate and Setup**:
   ```bash
   gcloud auth login
   gcloud projects list
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Enable Required APIs**:
   ```bash
   gcloud services enable cloudbuild.googleapis.com artifactregistry.googleapis.com run.googleapis.com
   ```

### Step-by-Step GCP Deployment

1. **Set Deployment Variables**:
   ```powershell
   $REPO_NAME = "resume-shortlisting-repo"
   $REGION = "us-central1"  # or your preferred region
   $SERVICE_NAME = "resume-shortlisting-service"
   ```

2. **Create Artifact Registry Repository**:
   ```powershell
   gcloud artifacts repositories create $REPO_NAME `
       --repository-format=docker `
       --location=$REGION `
       --description="Resume Shortlisting Tool Docker Repository"
   ```

3. **Build and Push Image**:
   ```powershell
   $PROJECT_ID = $(gcloud config get-value project)
   $IMAGE_TAG = "$($REGION)-docker.pkg.dev/$($PROJECT_ID)/$($REPO_NAME)/resume-shortlisting:latest"

   # Build and push to Artifact Registry
   gcloud builds submit --tag $IMAGE_TAG
   ```

4. **Deploy to Cloud Run**:
   ```powershell
   gcloud run deploy $SERVICE_NAME `
       --image=$IMAGE_TAG `
       --platform=managed `
       --region=$REGION `
       --allow-unauthenticated `
       --port=8080 `
       --memory=2Gi `
       --cpu=1 `
       --set-env-vars="OPENAI_API_KEY=your_openai_api_key_here"
   ```

### Advanced GCP Configuration

For production deployments, consider these additional configurations:

```powershell
# Deploy with custom settings
gcloud run deploy $SERVICE_NAME `
    --image=$IMAGE_TAG `
    --platform=managed `
    --region=$REGION `
    --allow-unauthenticated `
    --port=8080 `
    --memory=4Gi `
    --cpu=2 `
    --min-instances=0 `
    --max-instances=10 `
    --concurrency=80 `
    --timeout=300 `
    --set-env-vars="OPENAI_API_KEY=your_openai_api_key_here,ENVIRONMENT=production"
```

### GCP Environment Variables

Set these environment variables in Cloud Run:

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes |
| `PORT` | Server port (automatically set by Cloud Run) | No |
| `ENVIRONMENT` | Deployment environment (prod/dev) | No |

### GCP Deployment Commands Reference

For quick reference, all GCP deployment commands are available in `GCP Deployment Commands.txt`:

```powershell
# Complete deployment script
gcloud auth login
gcloud projects list
gcloud config set project YOUR_PROJECT_ID
gcloud services enable cloudbuild.googleapis.com artifactregistry.googleapis.com run.googleapis.com

$REPO_NAME = "resume-shortlisting-repo"
$REGION = "us-central1"

gcloud artifacts repositories create $REPO_NAME `
    --repository-format=docker `
    --location=$REGION `
    --description="Resume Shortlisting Tool Docker Repository"

$PROJECT_ID = $(gcloud config get-value project)
$IMAGE_TAG = "$($REGION)-docker.pkg.dev/$($PROJECT_ID)/$($REPO_NAME)/resume-shortlisting:latest"

gcloud builds submit --tag $IMAGE_TAG

$SERVICE_NAME = "resume-shortlisting-service"

gcloud run deploy $SERVICE_NAME `
    --image=$IMAGE_TAG `
    --platform=managed `
    --region=$REGION `
    --allow-unauthenticated
```

## 📊 Usage Guide

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| Maximum Resumes | Number of resumes to process | 10 |
| Score Threshold | Minimum score for qualification | 7.0 |
| API Model | OpenAI model to use | gpt-4o-mini |

### Input Requirements

**Job Description**: Include the following for best results:
- Required skills and technologies
- Experience level requirements
- Educational qualifications
- Job responsibilities
- Company culture fit criteria

**Resume Files**:
- Format: PDF only
- Size: No specific limit (reasonable file sizes recommended)
- Content: Should include contact information, skills, and experience

### Output Format

The tool generates a structured table with:
- **Name**: Extracted from resume
- **Mobile**: Phone number extracted from resume
- **Score**: 1-10 rating based on job fit
- **Questions for Interview**: 2-3 personalized questions
- **Reasoning**: Explanation for the score

### API Usage

**POST /shortlist-resumes/**

```bash
curl -X POST "https://your-cloud-run-url/shortlist-resumes/" \
  -H "Content-Type: multipart/form-data" \
  -F "job_description=Software Engineer position requiring Python and AI experience..." \
  -F "resumes=@resume1.pdf" \
  -F "resumes=@resume2.pdf"
```

**Response Format**:
```json
{
  "final_report": "| Name | Mobile | Score | Questions for Interview | Reasoning |\n|------|--------|-------|------------------------|-----------|..."
}
```

## 🔧 Configuration Files

### agents.yaml
Defines the AI agents' roles and capabilities:
- `jd_interpreter`: Analyzes job descriptions
- `resume_analyst`: Evaluates resumes and generates questions

### tasks.yaml
Defines the workflow tasks:
- `analyze_jd`: Extracts key requirements from job descriptions
- `shortlist_resumes`: Analyzes and scores candidates

## 📁 Project Structure

```
resume-shortlisting-tool/
├── app.py                              # Main Streamlit application
├── api.py                              # FastAPI backend
├── Dockerfile                          # Docker configuration
├── requirements.txt                    # Production dependencies
├── src/
│   └── resume_shortlisting/
│       ├── __init__.py
│       ├── main.py                     # CLI entry point
│       ├── crew.py                     # CrewAI configuration
│       ├── config/
│       │   ├── agents.yaml             # AI agents configuration
│       │   └── tasks.yaml              # Task definitions
│       └── tools/
│           ├── __init__.py
│           └── custom_tool.py          # PDF text extraction tool
├── knowledge/
│   └── user_preference.txt             # User context information
├── pyproject.toml                      # Project configuration
└── README.md                           # This file
```

## 🔒 Security Considerations

- **API Keys**: Never commit API keys to version control
- **Environment Variables**: Use Cloud Run's secure environment variable storage
- **Authentication**: Consider adding authentication for production use
- **Rate Limiting**: Implement rate limiting to prevent abuse
- **Input Validation**: Validate file uploads and input data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Contribution Guidelines
- Follow the existing code style
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting
- Test Docker builds locally before submitting

## 🔧 Troubleshooting

### Common Issues

**Docker Build Fails**:
- Ensure all dependencies are in requirements.txt
- Check Python version compatibility
- Verify Docker is running

**GCP Deployment Issues**:
- Verify all required APIs are enabled
- Check IAM permissions
- Ensure environment variables are set correctly

**API Connection Issues**:
- Verify OpenAI API key is valid
- Check network connectivity
- Review Cloud Run logs for errors

### Getting Help

- Check the [Issues](https://github.com/Kartavya-AI/Resume-Shortlisting/issues) page
- Review Cloud Run logs: `gcloud run logs read SERVICE_NAME --region=REGION`
- Test locally before deploying to production

## 🙏 Acknowledgments

- [CrewAI](https://crewai.com/) for the multi-agent AI framework
- [Streamlit](https://streamlit.io/) for the web application framework
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [OpenAI](https://openai.com/) for the language model API
- [ReportLab](https://www.reportlab.com/) for PDF generation
- [Google Cloud Platform](https://cloud.google.com/) for cloud hosting
