import streamlit as st
import os
import logging
from main import analyze_rooftops, CITY_COORDINATES, VALID_IMAGE_EXTENSIONS
import plotly.graph_objects as go
from typing import List, Dict, Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/solar_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Streamlit page configuration
st.set_page_config(
    page_title="Solar Rooftop Analysis Tool",
    layout="wide",
    initial_sidebar_state="expanded"
)

def save_uploaded_files(uploaded_files: List[st.runtime.uploaded_file_manager.UploadedFile]) -> List[str]:
    """Save uploaded files to temporary directory and return their paths."""
    image_paths = []
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    
    for i, file in enumerate(uploaded_files):
        temp_path = temp_dir / f"{i}_{file.name}"
        with open(temp_path, "wb") as f:
            f.write(file.getbuffer())
        if temp_path.is_file() and any(temp_path.suffix.lower() == ext for ext in VALID_IMAGE_EXTENSIONS):
            image_paths.append(str(temp_path))
        else:
            st.warning(f"Invalid file: {file.name}. Use PNG, JPG, or JPEG.")
            logger.warning(f"Invalid file uploaded: {file.name}")
    
    return image_paths

def display_results(results: Dict[str, Any]) -> None:
    """Display analysis results and charts."""
    st.text_area(
        "Analysis Results",
        results["output"],
        height=400,
        placeholder="Results will appear here...",
        key="results_text"
    )
    st.plotly_chart(results["bar_fig"], use_container_width=True, key="bar_chart")
    st.plotly_chart(results["line_fig"], use_container_width=True, key="line_chart")

def display_download_buttons(export_files: Dict[str, str]) -> None:
    """Display download buttons for export files."""
    st.subheader("Download Reports")
    for file_type, file_path in export_files.items():
        if file_path and os.path.isfile(file_path):
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            st.download_button(
                label=f"Download {file_type.upper()} Report",
                data=file_bytes,
                file_name=os.path.basename(file_path),
                mime="application/octet-stream",
                key=f"download_{file_type}"
            )
        else:
            st.warning(f"{file_type.upper()} report not available.")
            logger.warning(f"No valid {file_type} file at: {file_path}")

def main():
    """Run the Streamlit interface for solar rooftop analysis."""
    st.title("AI Solar Rooftop Analysis Tool")
    st.markdown("""
    Upload satellite images (PNG/JPG/JPEG, >1080p, 1+ images). Select cities and panel types (equal number or one for all).
    View solar potential, ROI, recommendations, Plotly visualizations, and download reports (PDF, CSV, Excel, JSON).
    """)

    # Initialize session state
    if "results" not in st.session_state:
        st.session_state.results = {
            "output": "",
            "bar_fig": go.Figure(),
            "line_fig": go.Figure(),
            "export_files": {"pdf": "", "csv": "", "excel": "", "json": ""}
        }

    # Layout
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Inputs")
        uploaded_files = st.file_uploader(
            "Upload Satellite Images",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help="Upload high-resolution images (>1080p)",
            key="image_uploader"
        )

        cities = st.multiselect(
            "Select Cities",
            options=list(CITY_COORDINATES.keys()),
            default=["New Delhi"],
            help="Choose one city per image or a single city for all images",
            key="city_select"
        )
        panel_types = st.multiselect(
            "Select Panel Types",
            options=["monocrystalline", "bifacial", "perovskite"],
            default=["monocrystalline"],
            help="Choose one panel type per image or a single type for all images",
            key="panel_select"
        )

        if st.button("Analyze", type="primary", key="analyze_button"):
            if not uploaded_files:
                st.error("Please upload at least one image.")
                logger.error("No images uploaded")
                return

            image_paths = save_uploaded_files(uploaded_files)
            if not image_paths:
                st.error("No valid images provided.")
                logger.error("No valid image paths after upload")
                return

            with st.spinner("Analyzing rooftops..."):
                logger.info(f"Starting analysis for {len(image_paths)} images")
                try:
                    output, bar_fig, line_fig, pdf_file, csv_file, excel_file, json_file = analyze_rooftops(
                        image_paths, cities, panel_types
                    )
                    st.session_state.results = {
                        "output": output,
                        "bar_fig": bar_fig,
                        "line_fig": line_fig,
                        "export_files": {
                            "pdf": pdf_file,
                            "csv": csv_file,
                            "excel": excel_file,
                            "json": json_file
                        }
                    }
                    logger.info("Analysis completed and results stored")
                    if "Irradiance fetch failed" in output:
                        st.warning("OpenWeatherMap API key invalid or expired. Using default irradiance (600 W/m²).")
                except ImportError as e:
                    st.error("Image analysis failed due to missing PyTorch dependencies. Please install torch==2.5.0.")
                    logger.error(f"YOLO analysis failed: {e}")
                    return
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                    logger.error(f"Analysis failed: {e}")
                    return

    with col2:
        st.subheader("Analysis Results")
        if st.session_state.results["output"]:
            display_results(st.session_state.results)
            display_download_buttons(st.session_state.results["export_files"])

if __name__ == "__main__":
    main()