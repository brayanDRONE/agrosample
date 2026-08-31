#!/usr/bin/env python3
"""
Test script to validate PDF planilla parser.
"""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from inspections.planilla_parser import parse_planilla_pdf, map_planilla_to_multipuerto
from inspections.dispatch_flatfile import build_dispatch_flat_file

def test_pdf_parser(pdf_path: str):
    """Test parsing a planilla PDF and generating flat file."""
    print(f'Testing parser with: {pdf_path}')
    
    try:
        # Parse PDF
        print('\n1. Parsing PDF...')
        planilla_data = parse_planilla_pdf(pdf_path)
        print(f'   ✓ Extracted {len(planilla_data)} fields')
        
        # Display extracted data
        print('\n2. Extracted data:')
        for key, value in planilla_data.items():
            if isinstance(value, list):
                print(f'   {key}: {value}')
            else:
                val_str = str(value)[:60]
                print(f'   {key}: {val_str}')
        
        # Map to Multipuerto
        print('\n3. Mapping to Multipuerto format...')
        multipuerto_payload = map_planilla_to_multipuerto(planilla_data)
        print(f'   ✓ Mapped {len(multipuerto_payload)} fields')
        
        # Generate flat file
        print('\n4. Generating flat file...')
        filename, content = build_dispatch_flat_file(multipuerto_payload)
        print(f'   ✓ Generated: {filename}')
        
        # Display flat file
        fields = content.split(';')
        print(f'\n5. Flat file output ({len(fields)} fields):')
        print(f'   {content[:200]}...')
        
        return True
        
    except Exception as e:
        print(f'\n✗ Error: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Look for PDF in data folder
    data_dir = Path(__file__).parent.parent.parent / 'data'
    pdf_files = list(data_dir.glob('*.pdf'))
    
    if not pdf_files:
        print(f'No PDF files found in {data_dir}')
        sys.exit(1)
    
    pdf_path = str(pdf_files[0])
    success = test_pdf_parser(pdf_path)
    sys.exit(0 if success else 1)
