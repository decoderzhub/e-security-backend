# Salesforce Opportunity AI Analysis Backend

This FastAPI backend provides AI-powered analysis of Salesforce opportunities using Azure OpenAI.

## Setup

1. Install Python 3.8+ if not already installed
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your actual values
   ```

5. Run the server:
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

- `GET /` - Root endpoint with API info
- `GET /health` - Health check endpoint
- `POST /analyze-opportunities` - Analyze multiple opportunities
- `GET /opportunity-types` - Get available opportunity types

## Usage

The API accepts a POST request to `/analyze-opportunities` with the following structure:

```json
{
  "opportunities": [
    {
      "id": "unique-id",
      "opportunityName": "Opportunity Name",
      "description": "Detailed description",
      "onHoldReason": "Optional hold reason"
    }
  ]
}
```

Returns:

```json
{
  "results": {
    "unique-id": {
      "type": "Security Assessment",
      "confidence": 85,
      "reasoning": "Analysis reasoning"
    }
  },
  "processed_count": 1,
  "timestamp": "2024-01-01T12:00:00"
}
```

## Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and update the values:

- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint
- `AZURE_OPENAI_SUBSCRIPTION_KEY`: Your Azure OpenAI subscription key
- `AZURE_OPENAI_API_VERSION`: API version to use
- `AZURE_OPENAI_DEPLOYMENT_ID`: Your GPT model deployment ID
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)

## Development

The server runs on `http://localhost:8000` by default. The FastAPI automatic documentation is available at `http://localhost:8000/docs`.