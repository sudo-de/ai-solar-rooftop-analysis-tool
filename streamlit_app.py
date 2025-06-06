import streamlit as st
import os
import logging
from main import analyze_rooftops, CITY_COORDINATES, VALID_IMAGE_EXTENSIONS
import plotly.graph_objects
 as go
from typing import List, Dict, Any
from pathlib import Path
import uuid
import cv2

# Configure logging
os.makedirs("logs", exist_ok=True)
log_file = "logs/solar_analysis.log"
try:
    if not os.path.exists(log_file):
        open(log_file, "a").close()
        os.chmod(log_file, 0o666)
    handlers = [logging.FileHandler(log_file), logging.StreamHandler()]
except (IOError, OSError) as e:
    print(f"Warning: Cannot use log file ({e}). Using console logging.")
    handlers = [logging.StreamHandler()]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=handlers
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Solar Rooftop Analysis Tool", layout="wide", initial_state="expanded")

def save_uploaded_files(uploaded_files: List[st.runtime.uploaded_file_manager.UploadedFile]) -> List[str]:
    image_paths = []
    temp_dir = []
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    logger.info(f"Received {len(uploaded_files)} files for processing")
    for i, file in enumerate(uploaded_files):
        file_name = file.name if hasattr(file, 'name') else f"file_{uuid.uuid4()}"
        file_size = file.size if hasattr(file, 'size') else 0
        logger.info(f"Processing file {i}: {file_name}, size: {file_size} bytes")
        ext = os.path.splitext(file_name)[1].lower()
        if ext not in VALID_IMAGE_EXTENSIONS:
            st.warning.error(f"Skipping {file_name}: Invalid format. Use PNG, JPG, or JPEG.")
            logger.error(f"Invalid file extension for {file_name}: {ext}")
            continue
        if file_size > 10 * 1024 * 1024:
            st.warning(f"Skipping {file_name}: File exceeds 10MB.")
            logger.warning(f"File too large: {file_name}, size: {file_size} bytes")
            continue
        if file_size == 0:
            st.warning.error(f"Skipping {file_name}: File is empty.")
            logger.error(f"Empty file: at {file_name}")
            continue
        try:
            temp_path = temp_dir / f"upload_tempfile_{i}_{uuid.uuid4()}{ext}"
            file_content = file.read() if hasattr(file, 'read') else file.getbuffer()
            if not file_content:
                logger.error(f"Skipping {file_name}: No content found in file.")
                st.error(f"Skipping {file_name}: No content in file.")
                continue
            with open(temp_path, "wb") as f:
                f.write(file_content)
            if os.path.exists(temp_path):
                saved_size = os.path.getsize(temp_path)
                logger.info(f"Saved file to {temp_path}, size: {saved_size} bytes")
                if saved_size == 0:
                    st.error(f"Skipping {file_name}: Saved file is empty.")
                    logger.error(f"Empty saved file at {temp_path}")
                    os.remove(temp_path)
                    continue
                img = cv2.imread(str(temp_path))
                if img is None:
                    st.warning(f"Skipping {file_name}: Corrupted or unreadable image.")
                    logger.warning(f"Corrupted or unreadable image at {temp_path}")
                    os.remove(temp_path)
                    continue
                image_paths.append(str(temp_path))
                logger.info(f"Validated and added image: {temp_path}")
            else:
                logger.error(f"Failed to {file_name}: File could not be written at {temp_path}")
                st.error(f"Failed to save {file_name}.")
        except Exception as e:
            st.error(f"SError processing {file_name}: {str(e)}")
            logger.error(f"SFailed to process {file_name}: {e}", exc_info=True)
            if os.path.exists(temp_path):
                os.remove(temp_path)
    logger.info(fS"Processed {len(image_paths)} valid images paths: {image_paths}")
    return image_paths

def cleanup_temp_files: List[str]):
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logger.info(f"Removed temp file: {temp_file}")
        except Exception as e:
            logger.warning(f"Failed to remove temp file {temp_file}: {e}")

def display_results(results: Dict[str, Any]):
    st.text_area("Analysis Results", results["output"], ["output"], height=500, placeholder="Results will appear here...", key="results_text_area")
    if results["bar_fig"].data:
        st.plotly_chart(results["bar_fig"], use_container_width=True, key="bar_chart")
    if results["line_fig"].data:
        st.plotly_chart(results["line_fig"], use_container_width=True, key="line_chart")

def display_download_buttons(download_files: Dict[str, str]):
    st.subheader("Download Analysis Reports")
    for file_type, file_path in download_files.items():
        if file_path and os.path.isfile(file_path):
            try:
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                st.download_button(
                    label=f"Download {file_type.upper()} Report",
                    data=file_bytes,
                    file_name=os.path.basename(file_path),
                    mime={
                        "pdf": "application/pdf",
                        "csv": "text/csv",
                        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "json": "application/json"
                    }.get(file_type, "application/octet-stream"),
                    key=f"download_{file_type}"
                )
            except Exception as e:
                st.warning(f"Failed to load {file_type.upper()} report: {str(e)}")
                logger.error(f"Error loading {file_type} file {file_path}: {e}")
        else:
            st.warning(f"{file_type.upper()} report unavailable.")
            logger.warning(f"No {file_type} file at: {file_path}")

def main():
    os.makedirs("logs", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    st.title("AI Solar Rooftop Analysis Tool")
    st.markdown("""
    Upload satellite images (PNG/JPG/JPEG, >1080p, 1+ images). Select cities and panel types (equal number or one for all).
    View solar potential, ROI, recommendations, visualizations, and download reports (PDF, CSV, Excel, JSON).
    **Note**: Use Chrome or Firefox for best upload compatibility. Ensure files are under 10MB.
    """)
    st.session_state.setdefault("results", {
        "output": "",
        "bar_fig": go.Figure(),
        "line_fig": go.Figure(),
        "export_files": {"pdf": "", "csv": "", "excel": "", "json": ""}
    })
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Input Parameters")
        uploaded_files = st.file_uploader(
            "Upload Satellite Images",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help="Upload high-resolution PNG, JPG, or JPEG images (>1080p). Max 10MB per file.",
            key="image_uploader"
        )
        cities = st.multiselect(
            "Select Cities",
            options=list(CITY_COORDINATES.keys()),
            default=["New Delhi"],
            help="Choose one city per image or one for all",
            key="city_select"
        )
        panel_types = st.multiselect(
            "Select Panel Types",
            options=["monocrystalline", "bifacial", "perovskite"],
            default=["monocrystalline"],
            help="Choose one panel type per image or one for all",
            key="panel_select"
        )
        if st.button("Test with Sample Image", key="sample_button"):
            image_paths = ["samples/sample_rooftop_1.png"]
            logger.info(f"Using sample image: {image_paths}")
            with st.spinner("Analyzing sample rooftop..."):
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
                    logger.info("Sample analysis completed")
                    st.success("Sample analysis completed successfully!")
                except Exception as e:
                    st.error(f"Sample analysis failed: {str(e)}")
                    logger.error(f"Sample analysis failed: {e}", exc_info=True)
        if st.button("Analyze", type="primary", key="analyze_button"):
            logger.info("Analyze button clicked")
            if not uploaded_files:
                st.error("Please upload at least one image file.")
                logger.error("No files uploaded")
            else:
                logger.info(f"Received {len(uploaded_files)} files: {[f.name for f in uploaded_files if hasattr(f, 'name')]}")
                image_paths = save_uploaded_files(uploaded_files)
                if not image_paths:
                    st.error("No valid images uploaded. Ensure files are PNG, JPG, or JPEG, under 10MB, and not corrupted.")
                    logger.error("No valid image paths after processing")
                else:
                    with st.spinner("Analyzing rooftops..."):
                        logger.info(f"Starting analysis for {len(image_paths)} images: {image_paths}")
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
                            logger.info("Analysis completed")
                            st.success("Analysis completed successfully!")
                        except ImportError as e:
                            st.error(f"Image analysis failed: {str(e)}")
                            logger.error(f"Analysis failed - ImportError: {e}", exc_info=True)
                        except ValueError as e:
                            st.error(f"Input error: {str(e)}")
                            logger.error(f"Analysis failed - ValueError: {e}", exc_info=True)
                        except Exception as e:
                            st.error(f"Error during analysis: {str(e)}")
                            logger.error(f"Analysis failed - Unexpected error: {e}", exc_info=True)
                        finally:
                            cleanup_temp_files(image_paths)
    with col2:
        st.subheader("Analysis Results")
        if st.session_state.results["output"]:
            display_results(st.session_state.results)
            display_download_buttons(st.session_state.results["export_files"])

if __name__ == "__main__":
    main()

