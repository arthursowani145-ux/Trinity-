#!/usr/bin/env python3
"""
Trinity Web App v2.1 - CLEAN
Only drag & drop local file upload. No URL fetch.
User downloads EDF from source, then uploads to Trinity.
"""

import os
import uuid
import json
import subprocess
import re
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading

app = Flask(__name__)
CORS(app)

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
UPLOAD_FOLDER = BASE_DIR / 'uploads'
RESULTS_FOLDER = BASE_DIR / 'results'

for folder in [UPLOAD_FOLDER, RESULTS_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)

app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# Tool paths
TRINITY_QUICK = BASE_DIR / 'tools' / 'trinity_research_v1.2_fixed.py'
TRINITY_DEEP = BASE_DIR / 'tools' / 'batch_failed_seizure_detector_v3.1.py'

# Job storage
jobs = {}

def run_trinity_quick(filepath, patient_id):
    """Run quick prediction (v1.2)"""
    try:
        cmd = [
            'python', str(TRINITY_QUICK),
            '--path', str(filepath.parent),
            '--patient', patient_id
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        output = result.stdout
        
        # Parse results
        lead_times = re.findall(r'Lead:\s*(\d+)s', output)
        peak_ratios = re.findall(r'Peak:\s*([\d,]+\.?\d*)x', output)
        
        return {
            'success': True,
            'mode': 'quick',
            'seizures_found': len(lead_times),
            'lead_times': lead_times,
            'peak_ratios': [p.replace(',', '') for p in peak_ratios],
            'raw_output': output[-5000:] if len(output) > 5000 else output
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Analysis timeout (5 minutes)'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def run_trinity_deep(filepath, patient_id):
    """Run deep dive (v3.1)"""
    try:
        cmd = [
            'python', str(TRINITY_DEEP),
            '--path', str(filepath.parent),
            '--patient', patient_id
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        output = result.stdout
        
        # Parse failed seizure count
        failed_matches = re.findall(r'💚 FAILED SEIZURES?:?\s*(\d+)', output)
        if not failed_matches:
            failed_matches = re.findall(r'FAILED SEIZURES?:?\s*(\d+)', output)
        
        failed_count = int(failed_matches[0]) if failed_matches else 0
        
        clinical_matches = re.findall(r'CLINICAL SEIZURES?:?\s*(\d+)', output)
        clinical_count = int(clinical_matches[0]) if clinical_matches else 0
        
        return {
            'success': True,
            'mode': 'deep',
            'failed_seizures_count': failed_count,
            'clinical_seizures_count': clinical_count,
            'raw_output': output[-5000:] if len(output) > 5000 else output
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Analysis timeout (10 minutes)'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload and analyze local EDF file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.edf'):
        return jsonify({'error': 'Only .edf files are supported'}), 400
    
    mode = request.form.get('mode', 'quick')
    patient_id = request.form.get('patient_id', 'upload')
    job_id = str(uuid.uuid4())[:12]
    
    filename = secure_filename(file.filename)
    filepath = UPLOAD_FOLDER / f"{job_id}_{filename}"
    file.save(filepath)
    
    jobs[job_id] = {
        'id': job_id,
        'status': 'analyzing',
        'progress': 30,
        'mode': mode,
        'filename': filename,
        'patient_id': patient_id,
        'created_at': datetime.now().isoformat()
    }
    
    def analyze():
        try:
            jobs[job_id]['progress'] = 50
            if mode == 'quick':
                result = run_trinity_quick(filepath, patient_id)
            else:
                result = run_trinity_deep(filepath, patient_id)
            
            if result['success']:
                jobs[job_id]['result'] = result
                jobs[job_id]['status'] = 'completed'
                jobs[job_id]['progress'] = 100
            else:
                jobs[job_id]['status'] = 'failed'
                jobs[job_id]['error'] = result.get('error', 'Analysis failed')
        except Exception as e:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = str(e)
        finally:
            try:
                filepath.unlink()
            except:
                pass
    
    thread = threading.Thread(target=analyze)
    thread.start()
    
    return jsonify({'job_id': job_id})

@app.route('/status/<job_id>')
def status(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    response = {
        'status': job['status'],
        'progress': job.get('progress', 0),
        'mode': job.get('mode', 'quick')
    }
    
    if job['status'] == 'completed':
        response['result'] = job.get('result')
    elif job['status'] == 'failed':
        response['error'] = job.get('error')
    
    return jsonify(response)

@app.route('/download/<job_id>')
def download(job_id):
    if job_id not in jobs:
        return "Job not found", 404
    
    job = jobs[job_id]
    result_file = RESULTS_FOLDER / f"{job_id}_results.json"
    
    with open(result_file, 'w') as f:
        json.dump(job.get('result', {}), f, indent=2)
    
    return send_file(result_file, as_attachment=True, download_name=f"trinity_{job_id}.json")

if __name__ == '__main__':
    print("=" * 60)
    print("🧠 Trinity Web App v2.1 - CLEAN")
    print("=" * 60)
    print("Features:")
    print("  - Drag & drop .edf file upload")
    print("  - Quick mode (v1.2) - Seizure prediction")
    print("  - Deep Dive (v3.1) - Failed seizure discovery")
    print("=" * 60)
    print(f"URL: http://localhost:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
