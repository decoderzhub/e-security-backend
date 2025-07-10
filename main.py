import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import json
import asyncio
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Salesforce Opportunity AI Analysis API", version="1.0.0")

# Get CORS origins from environment variable
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Azure OpenAI Configuration
AZURE_OPENAI_CONFIG = {
    "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
    "subscription_key": os.getenv("AZURE_OPENAI_SUBSCRIPTION_KEY"),
    "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
    "deployment_id": os.getenv("AZURE_OPENAI_DEPLOYMENT_ID")
}

OPPORTUNITY_TYPES = [
    'Security Assessment',
    'Cloud Security',
    'Endpoint Security',
    'SIEM/SOC',
    'Identity Management',
    'Network Security',
    'Data Protection',
    'Vulnerability Management',
    'Compliance & Audit',
    'Incident Response',
    'Security Training',
    'Mainframe Security'
]

# Pydantic models
class OpportunityForAnalysis(BaseModel):
    id: str
    opportunityName: str
    description: str
    onHoldReason: Optional[str] = None

class OpportunityAnalysis(BaseModel):
    type: str
    confidence: int
    reasoning: str

class AnalysisRequest(BaseModel):
    opportunities: List[OpportunityForAnalysis]

class AnalysisResponse(BaseModel):
    results: dict[str, OpportunityAnalysis]
    processed_count: int
    timestamp: str

async def analyze_single_opportunity(
    client: httpx.AsyncClient,
    opportunity: OpportunityForAnalysis
) -> tuple[str, OpportunityAnalysis]:
    """Analyze a single opportunity using Azure OpenAI"""
    
    prompt = f"""
You are a cybersecurity expert analyzing business opportunities. Based on the information provided, determine the most appropriate security opportunity type.

Available Types: {', '.join(OPPORTUNITY_TYPES)}

Opportunity Information:
- Name: "{opportunity.opportunityName}"
- Description: "{opportunity.description}"
- On Hold Reason: "{opportunity.onHoldReason or 'N/A'}"

Please analyze this opportunity and respond with a JSON object containing:
{{
  "type": "one of the available types that best matches",
  "confidence": "number between 0-100 indicating confidence level",
  "reasoning": "brief explanation of why this type was chosen"
}}

Focus on identifying key security domains, technologies, and services mentioned. Consider:
- Security assessments and audits
- Cloud security implementations
- Endpoint protection and management
- SIEM, SOC, and monitoring services
- Identity and access management
- Network security and firewalls
- Data protection and encryption
- Vulnerability scanning and management
- Compliance requirements
- Incident response capabilities
- Security training and awareness
- Mainframe and legacy system security

Respond only with the JSON object, no additional text.
"""

    try:
        response = await client.post(
            f"{AZURE_OPENAI_CONFIG['endpoint']}/openai/deployments/{AZURE_OPENAI_CONFIG['deployment_id']}/chat/completions",
            params={"api-version": AZURE_OPENAI_CONFIG['api_version']},
            headers={
                'Content-Type': 'application/json',
                'Ocp-Apim-Subscription-Key': AZURE_OPENAI_CONFIG['subscription_key'],
            },
            json={
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a cybersecurity expert that analyzes business opportunities and categorizes them accurately. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 300,
                "temperature": 0.1,
                "top_p": 0.9
            },
            timeout=30.0
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Azure OpenAI API error: {response.text}")

        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        if not content:
            raise ValueError('No response content from Azure OpenAI')

        # Parse the JSON response
        analysis_data = json.loads(content.strip())
        
        # Validate the response
        if analysis_data.get('type') not in OPPORTUNITY_TYPES:
            print(f"AI suggested invalid type: {analysis_data.get('type')}, using fallback")
            analysis_data = fallback_categorization(opportunity)

        analysis = OpportunityAnalysis(**analysis_data)
        return opportunity.id, analysis

    except Exception as error:
        print(f"Error analyzing opportunity {opportunity.id}: {error}")
        # Use fallback categorization
        analysis = fallback_categorization(opportunity)
        return opportunity.id, analysis

def fallback_categorization(opportunity: OpportunityForAnalysis) -> OpportunityAnalysis:
    """Fallback rule-based categorization if AI fails"""
    search_text = f"{opportunity.opportunityName} {opportunity.description} {opportunity.onHoldReason or ''}".lower()
    
    if 'assessment' in search_text or 'audit' in search_text or 'evaluation' in search_text:
        return OpportunityAnalysis(
            type='Security Assessment',
            confidence=70,
            reasoning='Contains assessment/audit keywords'
        )
    elif 'cloud' in search_text or 'aws' in search_text or 'azure' in search_text or 'gcp' in search_text:
        return OpportunityAnalysis(
            type='Cloud Security',
            confidence=75,
            reasoning='Contains cloud platform keywords'
        )
    elif 'endpoint' in search_text or 'antivirus' in search_text or 'malware' in search_text:
        return OpportunityAnalysis(
            type='Endpoint Security',
            confidence=75,
            reasoning='Contains endpoint security keywords'
        )
    elif 'siem' in search_text or 'soc' in search_text or 'monitoring' in search_text:
        return OpportunityAnalysis(
            type='SIEM/SOC',
            confidence=80,
            reasoning='Contains SIEM/SOC keywords'
        )
    elif 'identity' in search_text or 'access' in search_text or 'mfa' in search_text or 'authentication' in search_text:
        return OpportunityAnalysis(
            type='Identity Management',
            confidence=75,
            reasoning='Contains identity management keywords'
        )
    elif 'firewall' in search_text or 'network' in search_text or 'perimeter' in search_text:
        return OpportunityAnalysis(
            type='Network Security',
            confidence=75,
            reasoning='Contains network security keywords'
        )
    elif 'data' in search_text or 'encryption' in search_text or 'backup' in search_text or 'protection' in search_text:
        return OpportunityAnalysis(
            type='Data Protection',
            confidence=75,
            reasoning='Contains data protection keywords'
        )
    elif 'vulnerability' in search_text or 'scanning' in search_text or 'penetration' in search_text:
        return OpportunityAnalysis(
            type='Vulnerability Management',
            confidence=75,
            reasoning='Contains vulnerability management keywords'
        )
    elif 'compliance' in search_text or 'regulatory' in search_text or 'gdpr' in search_text or 'hipaa' in search_text:
        return OpportunityAnalysis(
            type='Compliance & Audit',
            confidence=75,
            reasoning='Contains compliance keywords'
        )
    elif 'incident' in search_text or 'response' in search_text or 'forensics' in search_text:
        return OpportunityAnalysis(
            type='Incident Response',
            confidence=75,
            reasoning='Contains incident response keywords'
        )
    elif 'training' in search_text or 'awareness' in search_text or 'phishing' in search_text:
        return OpportunityAnalysis(
            type='Security Training',
            confidence=75,
            reasoning='Contains security training keywords'
        )
    elif 'mainframe' in search_text or 'legacy' in search_text or 'z/os' in search_text:
        return OpportunityAnalysis(
            type='Mainframe Security',
            confidence=80,
            reasoning='Contains mainframe keywords'
        )
    
    return OpportunityAnalysis(
        type='Security Assessment',
        confidence=40,
        reasoning='Default fallback categorization'
    )

@app.get("/")
async def root():
    return {"message": "Salesforce Opportunity AI Analysis API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/analyze-opportunities", response_model=AnalysisResponse)
async def analyze_opportunities(request: AnalysisRequest):
    """Analyze multiple opportunities and return their categorizations"""
    
    if not request.opportunities:
        raise HTTPException(status_code=400, detail="No opportunities provided for analysis")
    
    results = {}
    
    # Process opportunities in batches to avoid rate limiting
    batch_size = 5
    
    async with httpx.AsyncClient() as client:
        for i in range(0, len(request.opportunities), batch_size):
            batch = request.opportunities[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [analyze_single_opportunity(client, opp) for opp in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"Error in batch processing: {result}")
                    continue
                
                opp_id, analysis = result
                results[opp_id] = analysis
            
            # Add delay between batches to respect rate limits
            if i + batch_size < len(request.opportunities):
                await asyncio.sleep(1)
    
    return AnalysisResponse(
        results=results,
        processed_count=len(results),
        timestamp=datetime.now().isoformat()
    )

@app.get("/opportunity-types")
async def get_opportunity_types():
    """Get the list of available opportunity types"""
    return {"types": OPPORTUNITY_TYPES}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host=host, port=port)