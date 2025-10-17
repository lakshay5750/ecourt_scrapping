from flask import Flask, render_template, request, jsonify, send_file
from scraper import ECourtsScraper
import os
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ecourts-scraper-2024'

@app.route('/')
def index():
    return render_template('index.html', today=datetime.now().strftime('%d-%m-%Y'))

@app.route('/api/states')
def get_states():
    """Get available states"""
    try:
        scraper = ECourtsScraper()
        states = scraper.get_states()
        return jsonify({'success': True, 'data': states})
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/districts/<state>')
def get_districts(state):
    """Get districts for a state"""
    try:
        scraper = ECourtsScraper()
        districts = scraper.get_districts(state)
        return jsonify({'success': True, 'data': districts})
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/court-complexes/<state>/<district>')
def get_court_complexes(state, district):
    """Get court complexes for a district"""
    try:
        scraper = ECourtsScraper()
        complexes = scraper.get_court_complexes(state, district)
        return jsonify({'success': True, 'data': complexes})
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/download-causelist', methods=['POST'])
def download_causelist():
    """Download cause list PDF"""
    try:
        data = request.json
        state = data.get('state')
        district = data.get('district')
        court_complex = data.get('court_complex')
        date_str = data.get('date')
        
        if not all([state, district, court_complex, date_str]):
            return jsonify({'success': False, 'error': 'All fields are required'})
        
        # Validate date
        try:
            datetime.strptime(date_str, '%d-%m-%Y')
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format. Use DD-MM-YYYY'})
        
        scraper = ECourtsScraper()
        result = scraper.download_cause_list(state, district, court_complex, date_str)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    """Serve downloaded files"""
    try:
        file_path = os.path.join('downloads', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('downloads', exist_ok=True)
    print("🚀 eCourts Scraper running at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)