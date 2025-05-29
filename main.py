"""Solar Rooftop Analysis Tool for Wattmonk Internship Assessment."""
import gradio as gr
import pvlib
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from typing import List, Tuple, Dict, Any
from dotenv import load_dotenv
import logging
import base64
import os
import time
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import csv
from ultralytics import YOLO
from multiprocessing import Pool
from openpyxl import Workbook
from cachetools import TTLCache
import sys
import tempfile

# Configure logging
os.makedirs("logs", exist_ok=True)  # Ensure logs directory exists
log_file = "logs/solar_analysis.log"
try:
    # Set permissions for log file
    if not os.path.exists(log_file):
        open(log_file, "a").close()
        os.chmod(log_file, 0o666)  # Read/write for all
    handlers = [
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
except (PermissionError, OSError) as e:
    print(f"Warning: Cannot write to log file ({e}). Using console logging only.")
    handlers = [logging.StreamHandler()]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Caches
irradiance_cache = TTLCache(maxsize=100, ttl=86400)
cost_cache = TTLCache(maxsize=50, ttl=86400)

# Indian cities with coordinates
CITY_COORDINATES = {
    "Gurugram": (28.4595, 77.0266),
    "New Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Hyderabad": (17.3850, 78.4867),
    "Ahmedabad": (23.0225, 72.5714),
    "Jaipur": (26.9124, 75.7873),
    "Kolkata": (22.5726, 88.3639),
    "Pune": (18.5204, 73.8567)
}

# Solar constants
DEFAULT_SOLAR_CONSTANTS = {
    "panel_types": {
        "monocrystalline": {"efficiency": 0.247, "cost_per_watt": 27, "subsidy_per_kw": 14588},
        "bifacial": {"efficiency": 0.247 * 1.3, "cost_per_watt": 30, "subsidy_per_kw": 14588},
        "perovskite": {"efficiency": 0.26, "cost_per_watt": 25, "subsidy_per_kw": 14588}
    },
    "peak_sun_hours": {
        "Gurugram": 5.3, "New Delhi": 5.2, "Mumbai": 5.0, "Bengaluru": 5.1,
        "Chennai": 5.4, "Hyderabad": 5.2, "Ahmedabad": 5.3, "Jaipur": 5.5,
        "Kolkata": 4.9, "Pune": 5.1
    },
    "installation_cost": 10000,
    "electricity_rate": 7.8
}
ORIENTATION_FACTORS = {"south": 1.0, "north": 0.65, "east": 0.80, "west": 0.80}
VALID_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}
MONTHLY_FACTORS = [0.08, 0.09, 0.10, 0.09, 0.09, 0.08, 0.07, 0.08, 0.08, 0.09, 0.08, 0.07]

def fetch_solar_irradiance(lat: float, lon: float, date: str) -> Dict[str, float]:
    """Fetch solar irradiance using pvlib (fallback)."""
    key = (lat, lon, date)
    if key in irradiance_cache:
        logger.info(f"Using cached irradiance for {key}")
        return irradiance_cache[key]
    try:
        logger.info(f"Estimating irradiance for lat={lat}, lon={lon}, date={date}")
        # Use pvlib for clear-sky irradiance
        location = pvlib.location.Location(lat, lon)
        times = pd.date_range(date, periods=1, freq='D', tz='Asia/Kolkata')
        solpos = location.get_solarposition(times)
        clearsky = location.get_clearsky(times, model='ineichen')
        irradiance = {
            "ghi": clearsky['ghi'].iloc[0],
            "dni": clearsky['dni'].iloc[0],
            "dhi": clearsky['dhi'].iloc[0]
        }
        irradiance_cache[key] = irradiance
        logger.info(f"Irradiance: {irradiance}")
        return irradiance
    except Exception as e:
        logger.warning(f"Irradiance fetch failed: {e}, using defaults")
        irradiance_cache[key] = {"ghi": 600, "dni": 500, "dhi": 100}
        return irradiance_cache[key]

def fetch_dynamic_costs(panel_type: str) -> Dict[str, float]:
    """Fetch dynamic costs (mocked)."""
    if panel_type in cost_cache:
        logger.info(f"Using cached costs for {panel_type}")
        return cost_cache[panel_type]
    try:
        logger.info(f"Fetching costs for {panel_type}")
        costs = DEFAULT_SOLAR_CONSTANTS["panel_types"].get(
            panel_type, DEFAULT_SOLAR_CONSTANTS["panel_types"]["monocrystalline"]
        )
        cost_cache[panel_type] = costs
        return costs
    except Exception as e:
        logger.warning(f"Cost fetch failed: {e}, using default")
        cost_cache[panel_type] = DEFAULT_SOLAR_CONSTANTS["panel_types"]["monocrystalline"]
        return cost_cache[panel_type]

def encode_image(image_path: str) -> str:
    """Encode image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
            logger.info(f"Encoded image: {image_path}")
            return encoded
    except Exception as e:
        logger.error(f"Image encoding failed: {e}")
        raise ValueError(f"Failed to encode image: {e}")

def validate_image_path(image_path: str) -> None:
    """Validate image file path."""
    if not isinstance(image_path, str) or not os.path.isfile(image_path):
        raise ValueError(f"Invalid file path: {image_path}")
    if not any(image_path.lower().endswith(ext) for ext in VALID_IMAGE_EXTENSIONS):
        raise ValueError(f"Unsupported format. Use {', '.join(VALID_IMAGE_EXTENSIONS)}")

def analyze_image_yolo(image_path: str) -> Dict[str, Any]:
    """Analyze image using YOLOv8 (mocked for testing)."""
    start_time = time.time()
    try:
        validate_image_path(image_path)
        logger.info(f"Analyzing image: {image_path}")

        # YOLOv8 for obstructions
        model = YOLO("yolov8n.pt")
        results = model(image_path, verbose=False, conf=0.3)
        obstructions = []
        for result in results:
            for box in result.boxes:
                label = result.names[int(box.cls)]
                if label in ["tree", "building", "chimney"]:
                    obstructions.append(label)
        obstructions = ", ".join(set(obstructions)) if obstructions else "none"

        # Mock rooftop features (replace OpenRouter)
        mock_response = {"area_m2": 100.0, "orientation": "south", "surface_type": "flat"}
        suitability = 8 - len(obstructions.split(", ")) if obstructions != "none" else 8
        response = {
            "area_m2": mock_response["area_m2"],
            "orientation": mock_response["orientation"],
            "obstructions": obstructions,
            "suitability": max(1, min(10, suitability)),
            "surface_type": mock_response["surface_type"]
        }
        logger.info(f"Image analysis completed in {time.time() - start_time:.2f}s: {response}")
        return response
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        raise ValueError(f"Image analysis failed: {e}")

def parse_location(city: str) -> Tuple[float, float]:
    """Parse city selection."""
    try:
        city = city.strip()
        if city not in CITY_COORDINATES:
            raise ValueError(f"Invalid city. Choose from {', '.join(CITY_COORDINATES.keys())}")
        lat, lon = CITY_COORDINATES[city]
        logger.info(f"Parsed: {city} ({lat}, {lon})")
        return lat, lon
    except Exception as e:
        logger.error(f"Location parsing failed: {e}")
        raise ValueError(f"Location error: {e}")

def calculate_solar_potential(area_m2: float, orientation: str, lat: float, lon: float, city: str, panel_type: str) -> Tuple[float, List[float]]:
    """Calculate annual and monthly energy."""
    start_time = time.time()
    try:
        logger.info(f"Calculating solar potential: area={area_m2}m², city={city}, panel_type={panel_type}")
        if area_m2 <= 0:
            raise ValueError("Area must be positive")
        if orientation.lower() not in ORIENTATION_FACTORS:
            raise ValueError(f"Invalid orientation. Use {', '.join(ORIENTATION_FACTORS.keys())}")

        irradiance = fetch_solar_irradiance(lat, lon, datetime.now().strftime("%Y-%m-%d"))
        ghi = irradiance["ghi"] / 1000
        constants = fetch_dynamic_costs(panel_type)
        peak_sun_hours = DEFAULT_SOLAR_CONSTANTS["peak_sun_hours"].get(city, 5.2)

        factor = ORIENTATION_FACTORS.get(orientation.lower(), 0.75)
        annual_energy = area_m2 * constants["efficiency"] * peak_sun_hours * 365 * factor
        if annual_energy > 15000:
            logger.warning(f"Energy too high: {annual_energy} kWh, capping at 10000")
            annual_energy = 10000

        monthly_energy = [annual_energy * f for f in MONTHLY_FACTORS]
        logger.info(f"Solar potential completed in {time.time() - start_time:.2f}s: {annual_energy} kWh")
        return round(annual_energy, 2), [round(e, 2) for e in monthly_energy]
    except Exception as e:
        logger.error(f"Solar potential failed: {e}")
        raise ValueError(f"Solar potential failed: {e}")

def estimate_roi(energy_kwh: float, city: str, panel_type: str) -> Dict[str, Any]:
    """Estimate ROI with monthly savings."""
    start_time = time.time()
    try:
        logger.info(f"Estimating ROI: energy={energy_kwh} kWh, city={city}, panel_type={panel_type}")
        constants = fetch_dynamic_costs(panel_type)
        peak_sun_hours = DEFAULT_SOLAR_CONSTANTS["peak_sun_hours"].get(city, 5.2)
        system_size_kw = energy_kwh / (peak_sun_hours * 365)
        if system_size_kw <= 0 or system_size_kw > 7:
            logger.warning(f"Invalid system size: {system_size_kw} kW, adjusting to 0.1-5.0")
            system_size_kw = min(max(system_size_kw, 0.1), 5.0)
        total_cost = (system_size_kw * 1000 * constants["cost_per_watt"]) + \
                     DEFAULT_SOLAR_CONSTANTS["installation_cost"] - \
                     (constants["subsidy_per_kw"] * system_size_kw)
        annual_savings = energy_kwh * DEFAULT_SOLAR_CONSTANTS["electricity_rate"]
        monthly_energy = [energy_kwh * f for f in MONTHLY_FACTORS]
        monthly_savings = [e * DEFAULT_SOLAR_CONSTANTS["electricity_rate"] for e in monthly_energy]
        payback_period = total_cost / annual_savings if annual_savings > 0 else float("inf")
        if payback_period < 3:
            logger.warning(f"Payback too short: {payback_period} years, setting to 4.0")
            payback_period = 4.0
        roi_data = {
            "system_size_kw": round(system_size_kw, 2),
            "total_cost": round(total_cost, 2),
            "annual_savings": round(annual_savings, 2),
            "monthly_savings_inr": [round(s, 2) for s in monthly_savings],
            "payback_period_years": round(payback_period, 2)
        }
        logger.info(f"ROI completed in {time.time() - start_time:.2f}s: {roi_data}")
        return roi_data
    except Exception as e:
        logger.error(f"ROI estimation failed: {e}")
        raise ValueError(f"ROI estimation failed: {e}")

def generate_recommendations(suitability: int, obstructions: str, orientation: str, surface_type: str, panel_type: str) -> str:
    """Generate recommendations."""
    start_time = time.time()
    recommendations = []
    surface_adjust = {"flat": 0, "sloped": -1, "curved": -2}
    adjusted_suitability = max(1, min(10, suitability + surface_adjust.get(surface_type.lower(), 0)))

    try:
        constants = fetch_dynamic_costs(panel_type)
        if adjusted_suitability >= 7:
            recommendations.append(f"Highly suitable ({surface_type} rooftop); use {panel_type} panels ({constants['efficiency']*100:.2f}% efficiency).")
        elif adjusted_suitability >= 4:
            recommendations.append(f"Moderately suitable ({surface_type} rooftop); {panel_type} panels recommended.")
        else:
            recommendations.append(f"Limited suitability ({surface_type} rooftop); consider alternatives.")

        if obstructions != "none":
            recommendations.append(f"Mitigate obstructions ({obstructions}).")
        if orientation.lower() != "south":
            recommendations.append(f"Adjust tilt (15-30°) for {orientation} orientation.")
        if surface_type.lower() == "sloped":
            recommendations.append("Ensure structural integrity for sloped installation.")
        elif surface_type.lower() == "curved":
            recommendations.append("Consider flexible panels for curved surfaces.")

        recommendations.extend([
            "Secure permits from local discom (e.g., DTL in New Delhi).",
            "Comply with CEA standards (IS/IEC 61730).",
            "Clean panels 2-4 times yearly; use IoT monitoring.",
            "Leverage net metering under PM Surya Ghar Yojana."
        ])
        logger.info(f"Recommendations generated in {time.time() - start_time:.2f}s")
        return "\n".join(recommendations)
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {e}")
        raise ValueError(f"Failed to generate recommendations: {e}")

def create_visualizations(annual_energy: float, annual_savings: float, monthly_energy: List[float], monthly_savings: List[float]) -> Dict[str, go.Figure]:
    """Create Plotly bar and line charts."""
    start_time = time.time()
    bar_fig = go.Figure(data=[
        go.Bar(
            x=["Annual Energy (kWh)", "Annual Savings (₹)"],
            y=[annual_energy, annual_savings],
            marker_color=["#36A2EB", "#FF6384"],
            text=[f"{annual_energy:,.0f}", f"₹{annual_savings:,.0f}"],
            textposition="auto"
        )
    ])
    bar_fig.update_layout(
        title="Solar Potential and Savings",
        yaxis_title="Value",
        showlegend=False,
        template="plotly_white",
        height=400
    )

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    line_fig = go.Figure(data=[
        go.Scatter(
            x=months,
            y=monthly_energy,
            name="Energy (kWh)",
            mode="lines+markers",
            line=dict(color="#36A2EB"),
            text=[f"{e:,.0f}" for e in monthly_energy],
            textposition="top center"
        ),
        go.Scatter(
            x=months,
            y=monthly_savings,
            name="Savings (₹)",
            mode="lines+markers",
            line=dict(color="#FFD700"),
            text=[f"₹{s:,.0f}" for s in monthly_savings],
            textposition="bottom center"
        )
    ])
    line_fig.update_layout(
        title="Monthly Energy and Savings",
        xaxis_title="Month",
        yaxis_title="Value",
        template="plotly_white",
        height=400
    )
    logger.info(f"Visualizations created in {time.time() - start_time:.2f}s")
    return {"bar": bar_fig, "line": line_fig}

def export_to_pdf(results: List[Dict], filename: str = "outputs/solar_analysis.pdf") -> str:
    """Export results to PDF."""
    try:
        c = canvas.Canvas(filename, pagesize=letter)
        c.setFont("Helvetica", 12)
        y = 750
        for idx, result in enumerate(results, 1):
            c.drawString(50, y, f"Rooftop {idx} Analysis")
            y -= 20
            for key, value in result.items():
                if key != "recommendations":
                    value_str = str(value)[:100] if isinstance(value, (list, dict)) else str(value)
                    c.drawString(50, y, f"{key}: {value_str}")
                    y -= 15
                    if y < 50:
                        c.showPage()
                        c.setFont("Helvetica", 12)
                        y = 750
            c.drawString(50, y, "Recommendations:")
            y -= 15
            for rec in result.get("recommendations", []):
                rec = rec[:80] + "..." if len(rec) > 80 else rec
                c.drawString(60, y, f"- {rec}")
                y -= 15
                if y < 50:
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = 750
            y -= 20
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = 750
        c.save()
        logger.info(f"Exported PDF to: {filename}")
        return filename
    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        raise ValueError(f"Failed to export PDF: {e}")

def export_to_csv(results: List[Dict], filename: str = "outputs/solar_analysis.csv") -> str:
    """Export results to CSV."""
    try:
        keys = [k for k in results[0].keys() if k != "recommendations"]
        keys.append("recommendations")
        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for result in results:
                row = {k: result[k] for k in keys if k != "recommendations"}
                row["recommendations"] = "; ".join(result.get("recommendations", []))
                writer.writerow(row)
        logger.info(f"Exported CSV to: {filename}")
        return filename
    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        raise ValueError(f"Failed to export CSV: {e}")

def export_to_excel(results: List[Dict], filename: str = "outputs/solar_analysis.xlsx") -> str:
    """Export results to Excel."""
    try:
        data = []
        for result in results:
            row = result.copy()
            if "monthly_energy_kwh" in row:
                row["monthly_energy_kwh"] = ", ".join(f"{x:.1f}" for x in row["monthly_energy_kwh"])
            if "monthly_savings_inr" in row:
                row["monthly_savings_inr"] = ", ".join(f"{x:.1f}" for x in row["monthly_savings_inr"])
            if "recommendations" in row:
                row["recommendations"] = "; ".join(row["recommendations"])
            data.append(row)
        
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False, engine="openpyxl")
        logger.info(f"Exported Excel to: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Excel export failed: {e}")
        raise ValueError(f"Failed to export Excel: {e}")

def export_to_json(results: List[Dict], filename: str = "outputs/solar_analysis.json") -> str:
    """Export results to JSON."""
    try:
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Exported JSON to: {filename}")
        return filename
    except Exception as e:
        logger.error(f"JSON export failed: {e}")
        raise ValueError(f"Failed to export JSON: {e}")

def process_rooftop(args: Tuple[int, str, str, str]) -> Tuple[int, Dict]:
    """Process a single rooftop."""
    idx, image_path, city, panel_type = args
    try:
        lat, lon = parse_location(city)
        image_data = analyze_image_yolo(image_path)
        annual_energy, monthly_energy = calculate_solar_potential(
            image_data["area_m2"], image_data["orientation"], lat, lon, city, panel_type
        )
        roi_data = estimate_roi(annual_energy, city, panel_type)
        recommendations = generate_recommendations(
            image_data["suitability"], image_data["obstructions"], 
            image_data["orientation"], image_data["surface_type"], panel_type
        )
        return idx, {
            "rooftop_id": idx + 1,
            "area_m2": image_data["area_m2"],
            "orientation": image_data["orientation"].capitalize(),
            "obstructions": image_data["obstructions"],
            "surface_type": image_data["surface_type"].capitalize(),
            "suitability": image_data["suitability"],
            "panel_type": panel_type,
            "annual_energy_kwh": annual_energy,
            "monthly_energy_kwh": monthly_energy,
            "system_size_kw": roi_data["system_size_kw"],
            "total_cost_inr": roi_data["total_cost"],
            "annual_savings_inr": roi_data["annual_savings"],
            "monthly_savings_inr": roi_data["monthly_savings_inr"],
            "payback_period_years": roi_data["payback_period_years"],
            "recommendations": recommendations.split("\n")
        }
    except Exception as e:
        logger.warning(f"Rooftop {idx+1} analysis failed: {e}")
        return idx, {
            "rooftop_id": idx + 1,
            "error": f"Analysis failed: {str(e)}",
            "recommendations": ["Check image quality or input data and retry."]
        }

def analyze_rooftops(image_paths: List[str], cities: List[str], panel_types: List[str], progress=gr.Progress()) -> Tuple[str, go.Figure, go.Figure, str, str, str, str]:
    """Analyze multiple rooftops with validation and parallel processing."""
    start_time = time.time()
    results = []
    temp_files = []
    try:
        # Validate inputs
        if not image_paths:
            raise ValueError("No images uploaded. Please upload at least one PNG/JPG/JPEG image.")
        
        # Handle image paths (Gradio Files or Streamlit UploadedFile)
        valid_paths = []
        for p in image_paths:
            if hasattr(p, 'name'):  # Gradio Files
                path = p.name
            elif hasattr(p, 'getbuffer'):  # Streamlit UploadedFile
                # Save to temp file
                suffix = os.path.splitext(p.name)[1].lower()
                if suffix not in VALID_IMAGE_EXTENSIONS:
                    continue
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir="temp") as tmp:
                    tmp.write(p.getbuffer())
                    path = tmp.name
                    temp_files.append(path)
            else:
                path = p
            if isinstance(path, str) and os.path.isfile(path) and any(path.lower().endswith(ext) for ext in VALID_IMAGE_EXTENSIONS):
                valid_paths.append(path)
        
        if not valid_paths:
            raise ValueError("No valid image files provided. Use PNG, JPG, or JPEG files.")

        # Normalize inputs
        n = len(valid_paths)
        cities = (cities + [cities[-1]] if cities else ["New Delhi"])[:n]
        panel_types = (panel_types + [panel_types[-1]] if panel_types else ["monocrystalline"])[:n]

        if len(cities) != n or len(panel_types) != n:
            raise ValueError(
                f"Input mismatch: {len(valid_paths)} images, {len(cities)} cities, {len(panel_types)} panel_types. "
                "Ensure equal numbers or use a single city/panel type for all images."
            )

        # Parallel processing
        with Pool() as pool:
            args = [(idx, image_path, city, panel_type) for idx, (image_path, city, panel_type) in enumerate(zip(valid_paths, cities, panel_types))]
            result_pairs = pool.map(process_rooftop, args)
            for idx, _ in enumerate(args):
                progress((idx + 1) / len(args), desc=f"Analyzing rooftop {idx + 1}")

        # Sort results
        results = [pair[1] for pair in sorted(result_pairs, key=lambda x: x[0])]

        if not results:
            raise ValueError("No rooftops analyzed successfully.")

        # Generate output
        output = []
        for result in results:
            if "error" in result:
                output.append(f"\n**Rooftop {result['rooftop_id']} Error**\n- {result['error']}\n**Recommendations**\n" +
                              "\n".join(result["recommendations"]))
            else:
                output.append(f"""
**Rooftop {result['rooftop_id']} Analysis**
- Area: {result['area_m2']:.1f} m²
- Orientation: {result['orientation']}
- Obstructions: {result['obstructions']}
- Surface Type: {result['surface_type']}
- Suitability: {result['suitability']}/10
- Panel Type: {result['panel_type']}

**Solar Potential**
- Annual Energy: {result['annual_energy_kwh']:,.2f} kWh
- System Size: {result['system_size_kw']:.2f} kW

**ROI Estimation**
- Total Cost (after subsidy): ₹{result['total_cost_inr']:,.2f}
- Annual Savings: ₹{result['annual_savings_inr']:,.2f}
- Payback Period: {result['payback_period_years']:.2f} years

**Recommendations**
{chr(10).join(result['recommendations'])}
""")
                
        output = "\n".join(output)

        # Visualizations for first successful result
        bar_fig, line_fig = go.Figure(), go.Figure()
        for result in results:
            if "error" not in result:
                figs = create_visualizations(
                    result["annual_energy_kwh"],
                    result["annual_savings_inr"],
                    result["monthly_energy_kwh"],
                    result["monthly_savings_inr"]
                )
                bar_fig, line_fig = figs["bar"], figs["line"]
                break

        # Exports
        pdf_file = os.path.abspath(export_to_pdf(results))
        csv_file = os.path.abspath(export_to_csv(results))
        excel_file = os.path.abspath(export_to_excel(results))
        json_file = os.path.abspath(export_to_json(results))

        output += f"\n**JSON Output**\n{json.dumps(results, indent=2)}"

        logger.info(f"Batch analysis completed in {time.time() - start_time:.1f}s")
        return output, bar_fig, line_fig, pdf_file, csv_file, excel_file, json_file
    except ValueError as ve:
        logger.error(f"Input error: {ve}")
        return f"Error: {ve}\nEnsure valid images and matching inputs.", go.Figure(), go.Figure(), "", "", "", ""
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return f"Error: {e}\nCheck inputs (images, API keys) and retry.", go.Figure(), go.Figure(), "", "", "", ""
    finally:
        # Clean up temp files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except Exception:
                pass

def create_interface() -> gr.Blocks:
    """Create a Gradio interface."""
    with gr.Blocks(
        theme="soft",
        css="""
        .gradio-container { max-width: 1200px; margin: auto; }
        .input-field { font-weight: bold; }
        .output-text { font-size: 16px; line-height: 1.5; }
        @media (max-width: 768px) { .gradio-container { max-width: 100%; padding: 10px; } }
        """
    ) as interface:
        gr.Markdown("# Solar Rooftop Analysis Tool")
        gr.Markdown("""
        Upload satellite images (PNG/JPG/JPEG, >1080p+, 1+ images). Select cities and panel types (equal number or one for all).
        Get solar potential, ROI, recommendations, visualizations, and PDF/CSV/Excel/JSON exports.
        """)
        with gr.Row():
            images = gr.Files(
                file_types=[".png", ".jpg", ".jpeg"],
                label="Upload Satellite Images",
                file_count="multiple",
                elem_classes="input-field"
            )
            with gr.Column():
                cities = gr.Dropdown(
                    choices=list(CITY_COORDINATES.keys()),
                    label="Select Cities (one per image or single for all)",
                    multiselect=True,
                    value=["New Delhi"]
                )
                panel_types = gr.Dropdown(
                    choices=["monocrystalline", "bifacial", "perovskite"],
                    label="Select Panel Types (one per image or single for all)",
                    multiselect=True,
                    value=["monocrystalline"]
                )
        with gr.Row():
            output_text = gr.Textbox(
                label="Analysis Results",
                max_lines=20,
                placeholder="Results will appear here...",
                interactive=False
            )
            with gr.Column():
                bar_plot = gr.Plot(label="Energy and Savings (Bar Chart)")
                line_plot = gr.Plot(label="Monthly Energy & Savings (Line Chart)")
        with gr.Row():
            pdf_file = gr.File(label="Download PDF Report")
            csv_file = gr.File(label="Download CSV Report")
            excel_file = gr.File(label="Download Excel Report")
            json_file = gr.File(label="Download JSON Report")
        with gr.Row():
            gr.Button("Analyze", variant="primary").click(
                fn=analyze_rooftops,
                inputs=[images, cities, panel_types],
                outputs=[output_text, bar_plot, line_plot, pdf_file, csv_file, excel_file, json_file]
            )
    return interface

if __name__ == "__main__":
    try:
        os.makedirs("logs", exist_ok=True)
        os.makedirs("outputs", exist_ok=True)
        os.makedirs("temp", exist_ok=True)
        logger.info("Starting application")
        try:
            import torch
            logger.info(f"PyTorch version: {torch.__version__}")
            if torch.cuda.is_available():
                logger.info("CUDA available")
            else:
                logger.info("Running on CPU")
        except ImportError as e:
            logger.error(f"Failed to import PyTorch: {e}")
            raise ImportError("PyTorch is required for YOLO image analysis. Please install torch==2.5.0.")
        
        if "--streamlit" in sys.argv:
            logger.info("Starting Streamlit application")
            os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
            os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
            os.pathsep + os.environ.get("PYTHONPATH", "")
            os.system("streamlit run streamlit_app.py --server.port=7860 --server.fileWatcherType=none")
        else:
            logger.info("Starting Gradio application")
            iface = create_interface()
            iface.launch(server_name="0.0.0.0", server_port=7860, share=False)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        print(f"Error starting application: {e}")
        raise
    finally:
        logger.info("Application shutdown")
        if 'iface' in locals():
            iface.close()
