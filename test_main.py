import pytest
import logging
from main import analyze_rooftops
import os
from main import (
    fetch_solar_irradiance, fetch_dynamic_costs, analyze_image_yolo,
    calculate_solar_potential, estimate_roi, parse_location, create_visualizations
)
import plotly.graph_objects as go

# Configure logger
logger = logging.getLogger(__name__)

# Mock environment variables
os.environ["OPENROUTER_API_KEY"] = "test_key"
os.environ["OPENWEATHER_API_KEY"] = "test_key"

def test_parse_location():
    lat, lon = parse_location("New Delhi")
    assert lat == 28.6139
    assert lon == 77.2090
    with pytest.raises(ValueError):
        parse_location("Invalid City")

def test_fetch_dynamic_costs():
    costs = fetch_dynamic_costs("monocrystalline")
    assert costs["efficiency"] == 0.247
    assert costs["cost_per_watt"] == 27
    costs = fetch_dynamic_costs("invalid_type")
    assert costs["efficiency"] == 0.247  # Default

def test_calculate_solar_potential():
    annual, monthly = calculate_solar_potential(100.0, "south", 28.6139, 77.2090, "New Delhi", "monocrystalline")
    assert 9000 <= annual <= 10000
    assert len(monthly) == 12
    assert all(0 < e <= 1000 for e in monthly)  # Relaxed upper bound

def test_estimate_roi():
    roi = estimate_roi(9360, "New Delhi", "monocrystalline")
    assert 4.0 <= roi["payback_period_years"] <= 5.0
    assert 0 < roi["system_size_kw"] <= 5.0
    assert roi["total_cost"] > 0
    assert roi["annual_savings"] > 0
    assert len(roi["monthly_savings_inr"]) == 12
    assert all(400 <= s <= 8000 for s in roi["monthly_savings_inr"])  # Adjusted range

def test_create_visualizations():
    figs = create_visualizations(9360, 70000, [750] * 12, [1000] * 12)
    assert isinstance(figs["bar"], go.Figure)
    assert isinstance(figs["line"], go.Figure)
    assert len(figs["line"].data) == 2  # Energy and savings
    assert figs["bar"].layout.title.text == "Solar Potential and Savings"
    assert figs["line"].layout.title.text == "Monthly Energy and Savings"

import tempfile
import shutil
try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None
from PIL import Image

@pytest.mark.skipif(AppTest is None, reason="Streamlit testing not available")
def test_streamlit_interface():
    """Test Streamlit interface functionality indirectly."""
    try:
        import torch
    except ImportError:
        pytest.skip("PyTorch not available, skipping Streamlit interface test")
    
    # Create temporary directory for test image
    temp_dir = tempfile.mkdtemp()
    test_image_path = os.path.join(temp_dir, "test_image.jpg")
    
    # Create a test image (100x100 pixels to pass resolution check)
    img = Image.new("RGB", (100, 100), color="white")
    img.save(test_image_path)
    
    try:
        # Simulate Streamlit inputs
        cities = ["New Delhi"]
        panel_types = ["monocrystalline"]
        
        # Run analysis
        output, bar_fig, line_fig, pdf_file, csv_file, excel_file, json_file = analyze_rooftops(
            [test_image_path], cities, panel_types
        )
        
        # Verify outputs
        assert output, "No analysis results generated"
        assert "Error" not in output, f"Analysis failed with error: {output}"
        assert isinstance(bar_fig, go.Figure), "Bar chart not generated"
        assert isinstance(line_fig, go.Figure), "Line chart not generated"
        assert os.path.isfile(pdf_file), "PDF report not generated"
        assert os.path.isfile(csv_file), "CSV report not generated"
        
        logger.info("Streamlit interface test passed")
    except Exception as e:
        logger.error(f"Streamlit test failed: {e}")
        raise
    finally:
        shutil.rmtree(temp_dir)

# Run: pytest test_main.py -v