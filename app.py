import streamlit as st
import tempfile
import subprocess
import os

# Configure Streamlit with increased file upload limit
st.set_page_config(
    page_title="Video Shrinker", 
    layout="centered"
)

# Set max upload size to 1GB (1024 MB)
st.config.set_option('server.maxUploadSize', 1024)

st.title("📹 Video Shrinker (using FFmpeg)")
st.markdown("Upload a video (up to 1GB), choose compression settings, and download a smaller version.")

uploaded = st.file_uploader(
    "Upload a video file (Max: 1GB)",
    type=["mp4", "mov", "avi", "mkv", "webm", "flv", "wmv", "m4v"],
    accept_multiple_files=False,
    help="Supported formats: MP4, MOV, AVI, MKV, WebM, FLV, WMV, M4V"
)

if uploaded is not None:
    file_size_mb = uploaded.size / 1024 / 1024
    st.write(f"**Uploaded file:** {uploaded.name}")
    st.write(f"**Format:** {uploaded.type}")
    st.write(f"**Size:** {file_size_mb:.2f} MB")
    
    # Show warning for very large files
    if file_size_mb > 500:
        st.warning("⚠️ Large file detected. Compression may take several minutes.")
    
    st.sidebar.header("🎛️ Compression Settings")
    
    # Quality preset
    quality_preset = st.sidebar.selectbox(
        "Quality Preset",
        options=["Custom", "High Quality", "Balanced", "Small Size"],
        index=2,
        help="Quick presets for common use cases"
    )
    
    # Set default values based on preset
    if quality_preset == "High Quality":
        default_crf, default_audio = 20, "192k"
    elif quality_preset == "Balanced":
        default_crf, default_audio = 23, "128k"
    elif quality_preset == "Small Size":
        default_crf, default_audio = 28, "96k"
    else:  # Custom
        default_crf, default_audio = 23, "128k"
    
    crf_value = st.sidebar.slider(
        "CRF (Constant Rate Factor)",
        min_value=15, max_value=35, value=default_crf, step=1,
        help="Lower CRF = higher quality but larger file. Higher CRF = smaller file but lower quality."
    )
    
    # Resolution options
    resolution_option = st.sidebar.selectbox(
        "Resolution",
        options=["Keep Original", "1920x1080 (1080p)", "1280x720 (720p)", "854x480 (480p)", "Custom"],
        index=0
    )
    
    scale_width = 0
    if resolution_option == "1920x1080 (1080p)":
        scale_width = 1920
    elif resolution_option == "1280x720 (720p)":
        scale_width = 1280
    elif resolution_option == "854x480 (480p)":
        scale_width = 854
    elif resolution_option == "Custom":
        scale_width = st.sidebar.number_input(
            "Max width (px)", min_value=0, value=0, step=100,
            help="Leave 0 to keep original resolution."
        )
    
    audio_bitrate = st.sidebar.selectbox(
        "Audio Bitrate",
        options=["192k", "128k", "96k", "64k"],
        index=["192k", "128k", "96k", "64k"].index(default_audio),
        help="Lower audio bitrate reduces file size but may affect audio quality."
    )
    
    # Advanced options
    with st.sidebar.expander("🔧 Advanced Options"):
        video_codec = st.selectbox(
            "Video Codec",
            options=["libx264", "libx265"],
            index=0,
            help="H.265 (libx265) provides better compression but slower encoding"
        )
        
        framerate_limit = st.number_input(
            "Max Frame Rate (fps)",
            min_value=0, max_value=60, value=0, step=1,
            help="Leave 0 to keep original framerate"
        )
    
    if st.button("🚀 Compress Video", type="primary"):
        # Create temporary files with proper handling
        try:
            # Input file
            input_suffix = os.path.splitext(uploaded.name)[1] or '.mp4'
            with tempfile.NamedTemporaryFile(delete=False, suffix=input_suffix) as in_tmp:
                in_tmp.write(uploaded.getvalue())  # Use getvalue() instead of read()
                in_tmp.flush()  # Ensure data is written
                in_path = in_tmp.name
            
            # Output file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as out_tmp:
                out_path = out_tmp.name
            
            # Verify input file exists and has content
            if not os.path.exists(in_path) or os.path.getsize(in_path) == 0:
                st.error("❌ Failed to create temporary input file")
                return
        
            # Build FFmpeg command
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output file
                "-i", in_path,
                "-vcodec", video_codec,
                "-crf", str(crf_value),
                "-acodec", "aac",
                "-b:a", audio_bitrate,
                "-movflags", "+faststart"  # Optimize for web streaming
            ]
        
            # Add video filters
            video_filters = []
            
            # Scale filter
            if scale_width and scale_width > 0:
                video_filters.append(f"scale='min({scale_width},iw)':'-2'")
            
            # Frame rate filter
            if framerate_limit and framerate_limit > 0:
                video_filters.append(f"fps=fps='min({framerate_limit},source_fps)'")
            
            # Apply filters if any
            if video_filters:
                cmd += ["-vf", ",".join(video_filters)]
            
            cmd.append(out_path)
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("🔄 Starting compression...")
            progress_bar.progress(10)
            
            # Debug: Show command being executed (remove in production)
            st.write("Debug - FFmpeg command:", " ".join(cmd))
            
            # Run FFmpeg with progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            progress_bar.progress(50)
            status_text.text("⚙️ Compressing video... This may take several minutes for large files.")
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                st.error(f"❌ Error during compression:")
                st.code(stderr, language="text")
                st.write("FFmpeg stdout:", stdout)
            else:
                progress_bar.progress(100)
                status_text.text("✅ Compression completed!")
                
                # Verify output file exists
                if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
                    st.error("❌ Output file was not created successfully")
                    return
                
                # Get file sizes
                original_size = uploaded.size / 1024 / 1024
                compressed_size = os.path.getsize(out_path) / 1024 / 1024
                compression_ratio = (1 - compressed_size / original_size) * 100
                
                # Success message with stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Original Size", f"{original_size:.2f} MB")
                with col2:
                    st.metric("Compressed Size", f"{compressed_size:.2f} MB")
                with col3:
                    st.metric("Size Reduction", f"{compression_ratio:.1f}%")
                
                # Download button
                with open(out_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download Compressed Video",
                        data=f.read(),
                        file_name=f"compressed_{uploaded.name}",
                        mime="video/mp4",
                        type="primary"
                    )
                
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            st.write("Error details:", str(e))
        
        finally:
            # Clean up temporary files
            try:
                if 'in_path' in locals() and os.path.exists(in_path):
                    os.remove(in_path)
                if 'out_path' in locals() and os.path.exists(out_path):
                    os.remove(out_path)
            except Exception as cleanup_error:
                st.write(f"Cleanup warning: {cleanup_error}")
            
            # Clear progress indicators
            if 'progress_bar' in locals():
                progress_bar.empty()
            if 'status_text' in locals():
                status_text.empty()

# Footer with usage tips
with st.expander("💡 Usage Tips"):
    st.markdown("""
    **For best results:**
    - **High Quality**: Use CRF 18-23 for minimal quality loss
    - **Balanced**: Use CRF 23-28 for good quality and reasonable size
    - **Small Size**: Use CRF 28-35 for maximum compression
    
    **Resolution tips:**
    - Keep original for high-quality content
    - Use 1080p for most web content
    - Use 720p or 480p for social media or mobile viewing
    
    **Codec comparison:**
    - **H.264 (libx264)**: Faster encoding, good compatibility
    - **H.265 (libx265)**: Better compression, slower encoding
    """)

st.markdown("---")
st.markdown("*Powered by FFmpeg • Built with Streamlit*")
