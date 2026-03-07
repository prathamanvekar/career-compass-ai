import os
import json
from groq import Groq
from PyPDF2 import PdfReader
from docx import Document
import pdfplumber
from config import Config

# Initialize Groq client
client = Groq(api_key=Config.GROQ_API_KEY)


class ResumeParser:
    """Parse resumes using Groq AI (Llama model)"""

    def __init__(self):
        self.model = Config.GROQ_MODEL

    def extract_text_from_pdf(self, file_path):
        """Extract text from PDF file"""
        text = ""
        try:
            # Try pdfplumber first (better for complex PDFs)
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"pdfplumber failed: {e}, trying PyPDF2...")
            try:
                reader = PdfReader(file_path)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            except Exception as e2:
                print(f"PyPDF2 also failed: {e2}")
                return None
        return text.strip()

    def extract_text_from_docx(self, file_path):
        """Extract text from DOCX file"""
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            print(f"Error extracting DOCX: {e}")
            return None

    def extract_text(self, file_path):
        """Extract text from resume file"""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif ext == '.docx':
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _call_groq(self, prompt):
        """Make a call to Groq API"""
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional resume parser and career advisor. Always respond with valid JSON only, no additional text or markdown."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=4096,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Groq API error: {e}")
            raise e

    def parse_resume(self, resume_text):
        """Use Groq to parse resume and extract structured data"""

        # Truncate if too long (Llama has context limits)
        if len(resume_text) > 6000:
            resume_text = resume_text[:6000]

        prompt = f"""Analyze this resume and extract information in JSON format.

Resume Text:
{resume_text}

Extract and return a JSON object with these exact keys:
{{
    "full_name": "candidate's full name",
    "email": "email if found, else null",
    "phone": "phone if found, else null",
    "location": "location/city if found, else null",
    "detected_domain": "primary career domain (e.g., Software Engineering, Data Science, Marketing, Finance, Healthcare, etc.)",
    "experience_years": numeric value of total years of experience (estimate if not explicit),
    "experience_level": "entry/mid/senior/executive based on experience",
    "skills": ["list", "of", "technical", "and", "soft", "skills"],
    "education": [
        {{
            "degree": "degree name",
            "field": "field of study",
            "institution": "university/college name",
            "year": "graduation year if available"
        }}
    ],
    "work_history": [
        {{
            "title": "job title",
            "company": "company name",
            "duration": "duration or dates",
            "description": "brief description of role"
        }}
    ],
    "certifications": ["list of certifications if any"],
    "summary": "brief professional summary (2-3 sentences)"
}}

Return ONLY valid JSON, no additional text or markdown code blocks."""

        try:
            response_text = self._call_groq(prompt)
            response_text = response_text.strip()

            # Clean up response - remove markdown code blocks if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                # Find the JSON content between ``` markers
                start_idx = 1 if lines[0].startswith('```') else 0
                end_idx = len(lines) - 1 if lines[-1].strip() == '```' else len(lines)
                response_text = '\n'.join(lines[start_idx:end_idx])

            # Remove any remaining ``` markers
            response_text = response_text.replace('```json', '').replace('```', '').strip()

            # Parse JSON
            parsed_data = json.loads(response_text)
            return parsed_data

        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response was: {response_text[:500]}...")
            return self._get_default_parsed_data()
        except Exception as e:
            print(f"Error parsing resume with Groq: {e}")
            return self._get_default_parsed_data()

    def _get_default_parsed_data(self):
        """Return default parsed data when parsing fails"""
        return {
            "full_name": None,
            "email": None,
            "phone": None,
            "location": None,
            "detected_domain": "General",
            "experience_years": 0,
            "experience_level": "entry",
            "skills": [],
            "education": [],
            "work_history": [],
            "certifications": [],
            "summary": "Resume parsed with limited information."
        }

    def analyze_resume_quality(self, resume_text, parsed_data):
        """Analyze resume quality and provide score + suggestions"""

        skills_count = len(parsed_data.get('skills', []))
        work_history = parsed_data.get('work_history', [])
        education = parsed_data.get('education', [])

        # Truncate resume text
        if len(resume_text) > 3000:
            resume_text = resume_text[:3000]

        prompt = f"""Analyze this resume for quality and provide improvement suggestions.

Resume Text:
{resume_text}

Parsed Data:
- Skills found: {skills_count}
- Work experiences: {len(work_history)}
- Education entries: {len(education)}
- Has summary: {bool(parsed_data.get('summary'))}

Evaluate the resume on these criteria and return JSON:
{{
    "overall_score": <0-100 score>,
    "section_scores": {{
        "formatting": <0-20>,
        "content_quality": <0-20>,
        "skills_presentation": <0-20>,
        "experience_detail": <0-20>,
        "overall_impression": <0-20>
    }},
    "strengths": ["list of strengths"],
    "weaknesses": ["list of weaknesses"],
    "enhancement_suggestions": [
        {{
            "category": "Skills/Experience/Format/Content",
            "suggestion": "specific actionable suggestion",
            "priority": "high/medium/low"
        }}
    ],
    "missing_sections": ["list any commonly expected sections that are missing"],
    "keyword_optimization": ["suggested keywords to add for ATS optimization"]
}}

Return ONLY valid JSON, no markdown or additional text."""

        try:
            response_text = self._call_groq(prompt)
            response_text = response_text.strip()

            # Clean up response
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                start_idx = 1 if lines[0].startswith('```') else 0
                end_idx = len(lines) - 1 if lines[-1].strip() == '```' else len(lines)
                response_text = '\n'.join(lines[start_idx:end_idx])

            response_text = response_text.replace('```json', '').replace('```', '').strip()

            analysis = json.loads(response_text)
            return analysis

        except Exception as e:
            print(f"Error analyzing resume quality: {e}")
            # Return default analysis if API fails
            return {
                "overall_score": 50,
                "section_scores": {
                    "formatting": 10,
                    "content_quality": 10,
                    "skills_presentation": 10,
                    "experience_detail": 10,
                    "overall_impression": 10
                },
                "strengths": ["Resume submitted successfully"],
                "weaknesses": ["Unable to perform detailed analysis"],
                "enhancement_suggestions": [
                    {
                        "category": "General",
                        "suggestion": "Consider adding more specific achievements with metrics",
                        "priority": "medium"
                    }
                ],
                "missing_sections": [],
                "keyword_optimization": []
            }


# Utility function for quick parsing
def parse_resume_file(file_path):
    """Quick function to parse a resume file"""
    parser = ResumeParser()
    text = parser.extract_text(file_path)
    if text:
        parsed = parser.parse_resume(text)
        if parsed:
            quality = parser.analyze_resume_quality(text, parsed)
            return {
                'text': text,
                'parsed': parsed,
                'quality': quality
            }
    return None
