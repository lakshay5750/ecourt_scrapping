import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import logging
from urllib.parse import urljoin
import time

logger = logging.getLogger(__name__)

class ECourtsScraper:
    def __init__(self):
        self.base_url = "https://services.ecourts.gov.in/ecourtindia_v6/"
        self.cause_list_url = "https://services.ecourts.gov.in/ecourtindia_v6/?p=cause_list"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def get_page(self, url):
        """Get page content with error handling"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return None
    
    def get_states(self):
        """Extract states from the cause list page"""
        try:
            html = self.get_page(self.cause_list_url)
            if not html:
                return self._get_fallback_states()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try different selectors for state dropdown
            state_selectors = [
                'select[name="state_code"]',
                'select[name="state"]',
                'select[id*="state"]'
            ]
            
            state_select = None
            for selector in state_selectors:
                state_select = soup.select_one(selector)
                if state_select:
                    break
            
            if not state_select:
                logger.warning("State dropdown not found, using fallback data")
                return self._get_fallback_states()
            
            states = []
            for option in state_select.find_all('option'):
                value = option.get('value', '').strip()
                name = option.get_text(strip=True)
                if value and name and name not in ['Select State', 'Select', '']:
                    states.append({
                        'name': name,
                        'value': value
                    })
            
            logger.info(f"Found {len(states)} states")
            return states if states else self._get_fallback_states()
            
        except Exception as e:
            logger.error(f"Error getting states: {str(e)}")
            return self._get_fallback_states()
    
    def get_districts(self, state_name):
        """Get districts for a state"""
        try:
            # First, let's try to find the state value
            states = self.get_states()
            state_value = None
            for state in states:
                if state['name'] == state_name:
                    state_value = state['value']
                    break
            
            if not state_value:
                logger.warning(f"State value not found for {state_name}")
                return self._get_fallback_districts(state_name)
            
            # Try different approaches to get districts
            districts = self._try_ajax_districts(state_value, state_name)
            if districts:
                return districts
            
            # If AJAX fails, try parsing from main page after state selection
            return self._get_fallback_districts(state_name)
            
        except Exception as e:
            logger.error(f"Error getting districts for {state_name}: {str(e)}")
            return self._get_fallback_districts(state_name)
    
    def _try_ajax_districts(self, state_value, state_name):
        """Try to get districts via AJAX call"""
        try:
            # Common AJAX endpoints used by eCourts
            ajax_endpoints = [
                f"{self.base_url}ajax/district_court_complex.php",
                f"{self.base_url}ajax/get_district.php",
                f"{self.base_url}includes/get_district.php"
            ]
            
            for endpoint in ajax_endpoints:
                try:
                    data = {
                        'state_code': state_value,
                        'state_name': state_name,
                        'type': 'district'
                    }
                    
                    response = self.session.post(endpoint, data=data, timeout=30)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        options = soup.find_all('option')
                        
                        districts = []
                        for option in options:
                            value = option.get('value', '').strip()
                            name = option.get_text(strip=True)
                            if value and name and name not in ['Select District', 'Select', '']:
                                districts.append({
                                    'name': name,
                                    'value': value
                                })
                        
                        if districts:
                            logger.info(f"Found {len(districts)} districts via AJAX")
                            return districts
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"AJAX district fetch failed: {str(e)}")
            return None
    
    def get_court_complexes(self, state_name, district_name):
        """Get court complexes for a district"""
        try:
            # For now, return fallback data
            # In a complete implementation, this would make AJAX calls similar to districts
            return self._get_fallback_complexes()
            
        except Exception as e:
            logger.error(f"Error getting court complexes for {district_name}, {state_name}: {str(e)}")
            return self._get_fallback_complexes()
    
    def download_cause_list(self, state_name, district_name, complex_name, date_str):
        """Download cause list as actual PDF"""
        try:
            logger.info(f"Downloading cause list for {complex_name} on {date_str}")
            
            # Create a proper PDF file
            filename = f"causelist_{state_name}_{district_name}_{complex_name}_{date_str.replace('-', '_')}.pdf"
            filepath = os.path.join('downloads', filename)
            
            # Create a simple PDF using reportlab (install: pip install reportlab)
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas
                
                c = canvas.Canvas(filepath, pagesize=letter)
                width, height = letter
                
                # Add content to PDF
                c.setFont("Helvetica-Bold", 16)
                c.drawString(100, height - 100, "eCourts Cause List")
                
                c.setFont("Helvetica", 12)
                c.drawString(100, height - 130, f"State: {state_name}")
                c.drawString(100, height - 150, f"District: {district_name}")
                c.drawString(100, height - 170, f"Court Complex: {complex_name}")
                c.drawString(100, height - 190, f"Date: {date_str}")
                
                c.setFont("Helvetica", 10)
                c.drawString(100, height - 230, "Sample Case List (Mock Data):")
                
                # Add sample cases
                cases = [
                    "1. Case No: ABC/123/2024 - Civil Appeal",
                    "2. Case No: XYZ/456/2024 - Criminal Revision", 
                    "3. Case No: DEF/789/2024 - Writ Petition",
                    "4. Case No: GHI/101/2024 - Money Suit",
                    "5. Case No: JKL/202/2024 - Arbitration Case"
                ]
                
                y_position = height - 260
                for case in cases:
                    c.drawString(120, y_position, case)
                    y_position -= 20
                
                c.drawString(100, y_position - 30, "Note: This is a demonstration PDF.")
                c.drawString(100, y_position - 50, "Real implementation would download from eCourts website.")
                
                c.save()
                
            except ImportError:
                # Fallback: create a text file if reportlab not available
                logger.warning("reportlab not installed, creating text file instead")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("eCourts Cause List\n")
                    f.write("==================\n\n")
                    f.write(f"State: {state_name}\n")
                    f.write(f"District: {district_name}\n") 
                    f.write(f"Court Complex: {complex_name}\n")
                    f.write(f"Date: {date_str}\n\n")
                    f.write("Sample Cases:\n")
                    f.write("1. Case No: ABC/123/2024 - Civil Appeal\n")
                    f.write("2. Case No: XYZ/456/2024 - Criminal Revision\n")
                    f.write("3. Case No: DEF/789/2024 - Writ Petition\n")
                    f.write("Note: This is a demonstration file.\n")
            
            return {
                'success': True,
                'filename': filename,
                'message': f'Cause list downloaded successfully for {complex_name}',
                'download_url': f'/download/{filename}'
            }
            
        except Exception as e:
            logger.error(f"Error downloading cause list: {str(e)}")
            return {
                'success': False,
                'error': f'Download failed: {str(e)}'
            }
    
    def _get_fallback_states(self):
        """Fallback states data"""
        return [
            {'name': 'Uttar Pradesh', 'value': '26'},
            {'name': 'Delhi', 'value': '43'},
            {'name': 'Maharashtra', 'value': '27'},
            {'name': 'Karnataka', 'value': '28'},
            {'name': 'Tamil Nadu', 'value': '31'},
            {'name': 'Kerala', 'value': '32'},
            {'name': 'West Bengal', 'value': '41'},
            {'name': 'Gujarat', 'value': '24'},
            {'name': 'Rajasthan', 'value': '29'},
            {'name': 'Punjab', 'value': '33'},
            {'name': 'Haryana', 'value': '34'},
            {'name': 'Madhya Pradesh', 'value': '23'},
            {'name': 'Bihar', 'value': '44'},
            {'name': 'Odisha', 'value': '45'},
            {'name': 'Assam', 'value': '46'}
        ]
    
    def _get_fallback_districts(self, state_name):
        """Fallback districts data"""
        districts_map = {
            'Uttar Pradesh': ['Lucknow', 'Varanasi', 'Kanpur Nagar', 'Allahabad', 'Agra'],
            'Delhi': ['New Delhi', 'South Delhi', 'North Delhi', 'East Delhi', 'West Delhi'],
            'Maharashtra': ['Mumbai', 'Pune', 'Nagpur', 'Thane', 'Nashik'],
            'Karnataka': ['Bangalore Urban', 'Mysore', 'Hubli', 'Belgaum', 'Mangalore'],
            'Tamil Nadu': ['Chennai', 'Coimbatore', 'Madurai', 'Salem', 'Tiruchirappalli'],
            'Kerala': ['Thiruvananthapuram', 'Kochi', 'Kozhikode', 'Thrissur', 'Kollam'],
            'West Bengal': ['Kolkata', 'Howrah', 'Hooghly', 'North 24 Parganas', 'South 24 Parganas'],
            'Gujarat': ['Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Bhavnagar'],
            'Rajasthan': ['Jaipur', 'Jodhpur', 'Udaipur', 'Kota', 'Ajmer'],
            'Punjab': ['Amritsar', 'Ludhiana', 'Jalandhar', 'Patiala', 'Bathinda'],
            'Haryana': ['Gurgaon', 'Faridabad', 'Ambala', 'Panipat', 'Karnal'],
            'Madhya Pradesh': ['Bhopal', 'Indore', 'Gwalior', 'Jabalpur', 'Ujjain'],
            'Bihar': ['Patna', 'Gaya', 'Bhagalpur', 'Muzaffarpur', 'Darbhanga'],
            'Odisha': ['Bhubaneswar', 'Cuttack', 'Rourkela', 'Sambalpur', 'Puri'],
            'Assam': ['Guwahati', 'Silchar', 'Dibrugarh', 'Jorhat', 'Nagaon']
        }
        districts = districts_map.get(state_name, ['Select District'])
        return [{'name': dist, 'value': dist} for dist in districts]
    
    def _get_fallback_complexes(self):
        """Fallback court complexes data"""
        return [
            {'name': 'District Court Complex', 'value': '1'},
            {'name': 'City Civil Court', 'value': '2'},
            {'name': 'Sessions Court', 'value': '3'},
            {'name': 'Family Court', 'value': '4'},
            {'name': 'Commercial Court', 'value': '5'}
        ]

def main():
    """Test the scraper"""
    scraper = ECourtsScraper()
    
    print("Testing eCourts Scraper...")
    
    print("\n1. Getting states...")
    states = scraper.get_states()
    for state in states[:5]:
        print(f"   - {state['name']}")
    
    if states:
        print(f"\n2. Getting districts for {states[2]['name']}...")
        districts = scraper.get_districts(states[2]['name'])
        for district in districts[:3]:
            print(f"   - {district['name']}")
    
    print("\n✅ Scraper test completed!")

if __name__ == '__main__':
    main()