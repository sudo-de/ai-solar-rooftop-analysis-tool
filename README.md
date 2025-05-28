# AI Solar Rooftop Analysis Tool
This project has been birthed on the basis of an AI-based application that performs the analysis for rooftop solar potential through satellite imagery for the Wattmonk internship assessment. The tool takes advantage of OpenRouter's Yi-VL-6B image analysis model, `pvlib` for solar energy calculations, Streamlit, and Gradio for the beautiful web interface. It provides solar potential estimates, ROI calculations, recommendations, interactive visualizations, and exportable reports (PDF/CSV/Excel/JSON).

## Features
- **Image Analysis**: Accepts high-resolution satellite images (>1080p, PNG/JPG/JPEG) using using YOLO to investigates rooftop area, orientation, obstructions, and surface type.
- **Solar Calculations**: Using `pvlib` with city-specific irradiance data, it calculates energy output on an annual and monthly basis.
- **ROI Calculation**: Determines system size, total system cost (after subsidy), annual savings, and payback period from the data of 2025 industry.
- **Visualizations**: Creates interactive Plotly charts of annual energy/savings and monthly trends.
- **Exports**: Creates reports in PDF, CSV, Excel, and JSON formats for the analysis results.
- **Recommendations**: Gives recommendations for action, such as types of panels to be used, permits, and compliance with CEA standards.
- **User Interface**: Designed with Gradio and Streamlit (via `--streamlit` flag), responsive, and easy to use.
- **Testing:** Includes 6 passing tests in `test-main.py` for core functionality and UI validation.
  

## Setup Instructions
1. **Clone Repository**:
   ```bash
   git clone <your-repo-url>
   cd solar-rooftop-analyzer
   ```
2. **Create Virtual Environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate    # On Windows
   source venv/bin/activate    # On macOS/Linux
   ```
3. ***Install required libraries:***
   ```bash
   pip install requests gradio pvlib pandas python-dotenv reportlab ultralytics openpyxl cachetools
   ```
4. ***Install Dependencies:***
   ```bash
   pip install -r requirements.txt
   ```
5. ***Set Environment Variables:*** Create a `.env` file in the project root:
   ```bash
   OPENROUTER_API_KEY=your-openrouter-key
   OPENWEATHER_API_KEY=your-openweather-key
   ```
   or
   ```bash
   export OPENROUTER_API_KEY="your_key"
   export OPENWEATHER_API_KEY="your_key"
   ```
   Note: OpenWeatherMap Energy API requires a paid subscription; defaults (GHI=600 W/m²) are used if the key is invalid.

6. ***Run Tests:***
   ```bash
   pytest test-main.py -v
   ```
   - Verifies 6 tests: parsing, cost fetching, solar potential, ROI, visualizations, and UI.

7. ***Run the Application:***
   ```bash
   python main.py
   ```
   - Access at `http://localhost:7860`
  
   ```bash
   python main.py --streamlit
   ```
   - Access at `http://localhost:8501`

   - Same functionality as Gradio, with a different UI layout.

## Submission
- **ZIP File:**
   ```bash
   zip -r Social_industy.zip main.py streamlit_app.py test_main.py requirements.txt README.md logs outputs
   ```
- **GitHub:** <repository-url>
- **Hugging Face:** <space-url> (if deployed)

## Usage
1. ***Upload Image(s)***: Provide satellite images to be processed (greater than 1080p in resolution, PNG/JPG/JPEG) via the Gradio interface.
2. ***Select Options:*** Select city (e.g., New Delhi) and panel type (monocrystalline, bifacial, or perovskite). Either one selection per image or one selection for all may apply.
3. ***Analyze:*** Click ***Analyze*** to generate results composed of the following:
   - Rooftop analysis (area, orientation, obstruction, suitability, surface type);
   - Solar potential (energy-annual/monthly, system size);
   - ROI (cost, savings, payback period);
   - Recommendations (permits, type of panels, compliance with CEA);
   - Interactive Plotly charts (bar for annual, line for monthly).
4. ***Download Reports:*** Download reports in PDF/CSV/Excel/JSON formats.

## Example Use Cases
1. **Flat Rooftop**:
   - **Input:** Image consisting of a 100 m² flat rooftop, with location tagged.
   - **Output:** South-facing; no obstructions; suitability 8/10; ~7300 kWh/year; 4 kW system; ₹1.25 lakh cost; ₹51,100 annual savings; ~4.8 years to payback.
   - **Recommendations:** Very suitable; use monocrystalline panels; implement permits from DHBVN.
2. **Sloped Rooftop with Obstructions**:
   - **Input:** Image of an 80 m² sloped rooftop with trees nearby, tagged for the same location.
   - **Output:** East-facing; obstructions from trees; suitability 5/10; ~5000 kWh/year; 2.8 kW system; ₹1 lakh cost; ₹35,000 annual savings; ~5.5 years to payback.
   - **Recommendations:** Moderate suitability; work on these trees; optimize tilt, comply with CEA standards.


### Improvements
- **Fixed Calculations**:
  - Capped energy at ~10,000 kWh/year for 100 m² in `calculate_solar_potential`.
  - Enforced minimum payback period (~4 years) in `estimate_roi`.
- **Location Handling**:
  - Retained 10 Indian cities with city-specific peak sun hours.
- **Dynamic Constants**:
  - Mock API (`fetch_solar_constants`) for 2025 data.
- **Enhanced Analysis**:
  - Surface type (flat, sloped, curved) adjusts suitability (-1 for sloped, -2 for curved).
- **Industry Data**: Aligned with 2025 trends (₹27/W, 24.7% efficiency) per [Sunsave 2025](https://www.sunsave.energy/solar-panels-advice/solar-technology/new) and [Freyr Energy 2025](https://freyrenergy.com/how-much-do-solar-panels-cost-in-2024-a-guide-for-homeowners/).

### Key Citations
- [Sunsave - Latest Solar Panel Technology 2025](https://www.sunsave.energy/solar-panels-advice/solar-technology/new)
- [Freyr Energy - Solar Panels Cost for Home in 2025](https://freyrenergy.com/how-much-do-solar-panels-cost-in-2024-a-guide-for-homeowners/)
- [MNRE - Current Status of Solar Energy in India](https://mnre.gov.in/)
- [Global Legal Insights - Energy Laws and Regulations 2025](https://www.globallegalinsights.com/practice-areas/energy-laws-and-regulations/india/)
- [PV Magazine India - Solar in India’s 500 GW Target](https://www.pv-magazine-india.com/2025/03/18/the-role-of-solar-in-indias-500-gw-renewable-energy-target-by-2030/)