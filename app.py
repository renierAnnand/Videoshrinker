import streamlit as st
import tempfile
import subprocess
import os

# Configure Streamlit
st.set_page_config(
    page_title="Video Shrinker", 
    layout="centered"
)

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
    
    if file_size_mb > 500:
        st.warning("⚠️ Large file detected. Compression may take several minutes.")
    
    st.sidebar.header("🎛️ Compression Settings")
    
    quality_preset = st.sidebar.selectbox(
        "Quality Preset",
        options=["Custom", "High Quality", "Balanced", "Small Size"],
        index=2,
        help="Quick presets for common use cases"
    )
    
    if quality_preset == "High Quality":
        default_crf, default_audio = 20, "192k"
    elif quality_preset == "Balanced":
        default_crf, default_audio = 23, "128k"
    elif quality_preset == "Small Size":
        default_crf, default_audio = 28, "96k"
    else:
        default_crf, default_audio = 23, "128k"
    
    crf_value = st.sidebar.slider(
        "CRF (Constant Rate Factor)",
        min_value=15, max_value=35, value=default_crf, step=1,
        help="Lower CRF = higher quality but larger file. Higher CRF = smaller file but lower quality."
    )
    
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

if uploaded is not None and st.button("🚀 Compress Video", type="primary"):
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, text=True)
        st.success("✅ FFmpeg detected successfully!")
        st.write("FFmpeg version:", result.stdout.split('\n')[0])
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        st.error("❌ FFmpeg is not installed or not found in system PATH.")
        
        st.write("**Debug Info:**")
        st.write("Error:", str(e))
        
        # Updated lookup paths
        common_paths = [
            # ← Update this to the exact location you verified:
            r"C:\Users\rannandale\OneDrive\Coding\video-shrinker\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
            "ffmpeg.exe",
            "ffmpeg"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                st.write(f"✅ Found FFmpeg at: {path}")
            else:
                st.write(f"❌ Not found at: {path}")
        
        path_env = os.environ.get('PATH', '')
        st.write("Current PATH contains:")
        for path_part in path_env.split(os.pathsep):
            if 'ffmpeg' in path_part.lower():
                st.write(f"🎯 {path_part}")
        
        st.info("""
        **Quick fixes to try:**
        
        1. **Restart Streamlit completely:**
           - Stop the app (Ctrl+C)
           - Close terminal
           - Open new Command Prompt
           - Run: `streamlit run app.py`
        
        2. **Try running from the directory where ffmpeg.exe is located**
        
        3. **Use absolute path test:**
           - Run: `C:\\Users\\rannandale\\OneDrive\\Coding\\video-shrinker\\ffmpeg-master-latest-win64-gpl\\bin\\ffmpeg.exe -version`
        """)
        
        demo_mode = st.checkbox("🧪 Enable Demo Mode (simulates compression without FFmpeg)")
        if not demo_mode:
            st.stop()
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        input_suffix = os.path.splitext(uploaded.name)[1] or '.mp4'
        with tempfile.NamedTemporaryFile(delete=False, suffix=input_suffix) as in_tmp:
            in_tmp.write(uploaded.getvalue())
            in_tmp.flush()
            in_path = in_tmp.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as out_tmp:
            out_path = out_tmp.name
        
        if not os.path.exists(in_path) or os.path.getsize(in_path) == 0:
            st.error("❌ Failed to create temporary input file")
        else:
            status_text.text("🔄 Starting compression...")
            progress_bar.progress(10)
            
            cmd = [
                "ffmpeg", "-y", "-i", in_path,
                "-vcodec", video_codec,
                "-crf", str(crf_value),
                "-acodec", "aac",
                "-b:a", audio_bitrate,
                "-movflags", "+faststart"
            ]
            
            video_filters = []
            if scale_width and scale_width > 0:
                video_filters.append(f"scale='min({scale_width},iw)':'-2'")
            if framerate_limit and framerate_limit > 0:
                video_filters.append(f"fps=fps='min({framerate_limit},source_fps)'")
            
            if video_filters:
                cmd += ["-vf", ",".join(video_filters)]
            
            cmd.append(out_path)
            
            st.write("Debug - FFmpeg command:", " ".join(cmd))
            
            if 'demo_mode' in locals() and demo_mode:
                progress_bar.progress(50)
                status_text.text("🧪 Demo mode: Simulating compression...")
                import time
                time.sleep(2)
                
                with open(out_path, 'wb') as f:
                    f.write(b"Demo compressed video file")
                
                progress_bar.progress(100)
                status_text.text("✅ Demo compression completed!")
                
                original_size = uploaded.size / 1024 / 1024
                simulated_compressed_size = original_size * 0.6
                compression_ratio = 40.0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Original Size", f"{original_size:.2f} MB")
                with col2:
                    st.metric("Simulated Size", f"{simulated_compressed_size:.2f} MB")
                with col3:
                    st.metric("Simulated Reduction", f"{compression_ratio:.1f}%")
                
                st.info("🧪 This is demo mode. Install FFmpeg for actual video compression.")
                
            else:
                progress_bar.progress(30)
                status_text.text("⚙️ Compressing video...")
                
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                    universal_newlines=True
                )
                stdout, stderr = process.communicate()
                
                progress_bar.progress(90)
                
                if process.returncode != 0:
                    st.error("❌ Error during compression:")
                    st.code(stderr, language="text")
                elif not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
                    st.error("❌ Output file was not created successfully")
                else:
                    progress_bar.progress(100)
                    status_text.text("✅ Compression completed!")
                    
                    original_size = uploaded.size / 1024 / 1024
                    compressed_size = os.path.getsize(out_path) / 1024 / 1024
                    compression_ratio = (1 - compressed_size / original_size) * 100
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Original Size", f"{original_size:.2f} MB")
                    with col2:
                        st.metric("Compressed Size", f"{compressed_size:.2f} MB")
                    with col3:
                        st.metric("Size Reduction", f"{compression_ratio:.1f}%")
                    
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
    
    finally:
        try:
            if 'in_path' in locals() and os.path.exists(in_path):
                os.remove(in_path)
            if 'out_path' in locals() and os.path.exists(out_path):
                os.remove(out_path)
        except:
            pass
        
        if 'progress_bar' in locals():
            progress_bar.empty()
        if 'status_text' in locals():
            status_text.empty()

if uploaded is not None:
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
