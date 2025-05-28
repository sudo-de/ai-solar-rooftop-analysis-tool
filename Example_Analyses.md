# 📊 Example Analyses: AI Solar Rooftop Analysis Tool

## 🔹 Example 1: New Delhi, Bifacial Panel

### 🖼️ Input
- **Image**: `samples/sample_rooftop_1.png` (1920x1080, PNG)
- **City**: New Delhi (28.6139, 77.209)
- **Panel Type**: Bifacial

### 🛠️ Steps
1. Launched Streamlit: `python main.py --streamlit`
2. Uploaded `sample_rooftop_1.png` at `http://localhost:8501`
3. Selected “New Delhi” and “bifacial”
4. Clicked “Analyze”

### 🧪 Output (from `logs/solar_analysis.log`)

#### 📷 Image Analysis
- **Area**: 100.0 m²
- **Orientation**: South
- **Obstructions**: None
- **Suitability**: 8/10
- **Time**: 1.04s

#### ☀️ Solar Potential
- **Energy**: 10,000 kWh (capped from 60,944.78 kWh)
- **Irradiance**: 600 W/m² (OpenWeatherMap 401 error)
- **Time**: 0.31s

#### 💰 ROI
- **System Size**: 5.27 kW
- **Total Cost**: ₹91,201.26
- **Annual Savings**: ₹78,000
- **Monthly Savings**:
  `[₹6,240, ₹7,020, ₹7,800, ₹7,020, ₹7,020, ₹6,240, ₹5,460, ₹6,240, ₹6,240, ₹7,020, ₹6,240, ₹5,460]`
- **Payback Period**: 4.0 years (from 1.17 years)
- **Time**: 0.00s

#### 📊 Visualizations
- **Bar Chart**: Monthly savings
- **Line Chart**: Cumulative savings
- **Time**: 0.19s

#### 📁 Exports
- **PDF**: `outputs/solar_analysis.pdf`
- **CSV**: `outputs/solar_analysis.csv`
- **Excel**: `outputs/solar_analysis.xlsx`
- **JSON**: `outputs/solar_analysis.json`

**Total Time**: 6.2s

#### 📂 Sample Output
- Sample CSV
- Sample Chart

---

## 🔹 Example 2: Mumbai, Monocrystalline Panel

### 🖼️ Input
- **Image**: `samples/sample_rooftop_2.jpg` (2560x1440, JPEG)
- **City**: Mumbai (19.0760, 72.8777)
- **Panel Type**: Monocrystalline

### 🛠️ Steps
1. Launched Streamlit
2. Uploaded `sample_rooftop_2.jpg`
3. Selected “Mumbai” and “monocrystalline”
4. Clicked “Analyze”

### 🧪 Output (simulated)

#### 📷 Image Analysis
- **Area**: 120.0 m²
- **Orientation**: Southwest
- **Obstructions**: Minor (chimney)
- **Suitability**: 7/10
- **Time**: 1.12s

#### ☀️ Solar Potential
- **Energy**: 10,000 kWh (capped from 55,000 kWh)
- **Irradiance**: 600 W/m²
- **Time**: 0.28s

#### 💰 ROI
- **System Size**: 6.32 kW
- **Total Cost**: ₹90,474.18
- **Annual Savings**: ₹93,600
- **Monthly Savings**:
  `[₹7,488, ₹8,424, ₹9,360, ₹8,424, ₹8,424, ₹7,488, ₹6,552, ₹7,488, ₹7,488, ₹8,424, ₹7,488, ₹6,552]`
- **Payback Period**: 4.0 years
- **Time**: 0.00s

#### 📊 Visualizations & Exports
- Similar to Example 1

**Total Time**: 6.5s

#### 📂 Sample Output
- Sample JSON

---

## 📝 Notes
- Images must be **>1080p**
- Use `samples/` or high-resolution satellite images
- OpenWeatherMap API failures trigger **default irradiance**: 600 W/m²
- Outputs: stored in `outputs/`
- Logs: written to `logs/solar_analysis.log`
