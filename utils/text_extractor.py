#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/utils/text_extractor.py

import os
import json
import docx
import PyPDF2
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextExtractor:
    """
    Utility class to extract text from various file formats (TXT, PDF, DOCX)
    and convert it to training data format for VulnLearnAI.
    """
    
    def __init__(self):
        self.supported_extensions = ['.txt', '.pdf', '.docx']
    
    def is_supported_file(self, file_path: str) -> bool:
        """Check if the file is supported based on its extension."""
        _, file_extension = os.path.splitext(file_path)
        return file_extension.lower() in self.supported_extensions
    
    def extract_text(self, file_path: str) -> Optional[str]:
        """Extract text from a file based on its format."""
        try:
            _, file_extension = os.path.splitext(file_path)
            file_extension = file_extension.lower()
            
            if file_extension == '.txt':
                return self._extract_from_txt(file_path)
            elif file_extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension == '.docx':
                return self._extract_from_docx(file_path)
            else:
                logger.warning(f"Unsupported file extension: {file_extension}")
                return None
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            return None
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from a TXT file."""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file."""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        return text
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from a DOCX file."""
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    
    def parse_vulnerability_from_text(self, text: str, file_name: str) -> Dict[str, Any]:
        """
        Parse vulnerability information from extracted text.
        Basic implementation - assumes specific format or uses heuristics to extract info.
        """
        # This is a simple implementation - you might need more sophisticated parsing
        # based on your document structure
        
        lines = text.split('\n')
        
        # Default values
        vuln_data = {
            "title": file_name,
            "description": text[:1000] if len(text) > 1000 else text,  # Limit description length
            "severity": self._extract_severity(text),
            "source": f"File: {file_name}",
            "timestamp": self._get_timestamp(),
        }
        
        # Try to extract a better title from the first non-empty line
        for line in lines:
            if line.strip():
                vuln_data["title"] = line.strip()[:100]  # Limit title length
                break
        
        return vuln_data
    
    def _extract_severity(self, text: str) -> str:
        """Extract severity information from text using keywords."""
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in ['critical', 'severe', 'highest']):
            return "Critical"
        elif any(kw in text_lower for kw in ['high', 'important', 'major']):
            return "High"
        elif any(kw in text_lower for kw in ['medium', 'moderate', 'average']):
            return "Medium"
        elif any(kw in text_lower for kw in ['low', 'minor', 'minimal']):
            return "Low"
        else:
            return "Unknown"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def process_file_to_jsonl(self, file_path: str, output_path: str) -> bool:
        """Process a single file and append the extracted data to a JSONL file."""
        if not self.is_supported_file(file_path):
            logger.warning(f"Unsupported file: {file_path}")
            return False
        
        text = self.extract_text(file_path)
        if not text:
            logger.warning(f"No text extracted from: {file_path}")
            return False
        
        file_name = os.path.basename(file_path)
        vuln_data = self.parse_vulnerability_from_text(text, file_name)
        
        # Convert to the format needed for fine-tuning
        training_entry = {
            "messages": [
                {"role": "system", "content": "You are a cybersecurity expert analyzing vulnerabilities."},
                {"role": "user", "content": f"Analyze this vulnerability:\nTitle: {vuln_data['title']}\nDescription: {vuln_data['description']}"},
                {"role": "assistant", "content": f"Based on my analysis, this appears to be a {vuln_data['severity']} severity vulnerability. The vulnerability involves {vuln_data['title'].lower()} which can lead to security issues. To remediate this, it's recommended to follow secure coding practices and implement proper validation."}
            ]
        }
        
        # Append to JSONL file
        with open(output_path, 'a', encoding='utf-8') as jsonl_file:
            jsonl_file.write(json.dumps(training_entry) + '\n')
        
        logger.info(f"Successfully processed {file_path} and added to {output_path}")
        return True
    
    def process_directory(self, input_dir: str, output_path: str) -> int:
        """
        Process all supported files in a directory and its subdirectories.
        Returns the number of successfully processed files.
        """
        count = 0
        for root, _, files in os.walk(input_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if self.process_file_to_jsonl(file_path, output_path):
                    count += 1
        
        logger.info(f"Processed {count} files from {input_dir} to {output_path}")
        return count


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract text from files for VulnLearnAI training.')
    parser.add_argument('--input', '-i', required=True, help='Input file or directory path')
    parser.add_argument('--output', '-o', required=True, help='Output JSONL file path')
    args = parser.parse_args()
    
    extractor = TextExtractor()
    
    if os.path.isdir(args.input):
        processed = extractor.process_directory(args.input, args.output)
        print(f"Processed {processed} files into {args.output}")
    elif os.path.isfile(args.input):
        if extractor.process_file_to_jsonl(args.input, args.output):
            print(f"Successfully processed {args.input} into {args.output}")
        else:
            print(f"Failed to process {args.input}")
    else:
        print(f"Input path {args.input} does not exist")
