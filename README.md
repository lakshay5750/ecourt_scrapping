# eCourts Cause List Scraper

A Python-based web application for scraping and downloading cause lists from the Indian eCourts website in real-time.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green)
![Selenium](https://img.shields.io/badge/Selenium-4.15.0-orange)

## 🚀 Features

- **Real-time Data Fetching**: Direct scraping from [eCourts India](https://services.ecourts.gov.in/ecourtindia_v6/)
- **Dynamic Dropdowns**: States → Districts → Court Complexes → Courts
- **PDF Download**: Automated cause list PDF downloads
- **Web Interface**: User-friendly Flask web application
- **CLI Support**: Command-line interface for automation
- **CAPTCHA Handling**: Manual CAPTCHA solving support
- **Error Handling**: Robust error management with fallbacks

## 📋 Requirements

- Python 3.8+
- Chrome Browser
- ChromeDriver

## 🛠 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/lakshay5750/ecourt_scrapping.git
   cd ecourt_scrapping
