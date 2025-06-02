import streamlit as st
import tempfile
import subprocess
import os

st.set_page_config(page_title="Video Shrinker", layout="centered")
st.title("📹 Video Shrinker (using FFmpeg)")
st.markdown("Upload a video, choose compression settings, and download a smaller version.")

uploaded = st.file_uploader(
    "Upload a video file",
    type=["mp4", "mov", "avi", "mkv", "webm"],
    accept_multiple_files=False,
)

if uploaded is not None:
    st.write(f"Uploaded file: {uploaded.name} ({uploaded.type}, {uploaded.size/1024/1024:.2f} MB)")

    st.sidebar.header("Compression Settings")
    crf_value = st.sidebar.slider(
        "CRF (Constant Rate Factor)",
        min_value=18, max_value=35, value=28, step=1,
        help="Lower CRF → higher quality (but larger file). Raise CRF to shrink file size more."
    )
    scale_width = st.sidebar.number_input(
        "Max width (px)", min_value=0, value=0, step=100,
        help="Leave 0 to keep original resolution."
    )
    audio_bitrate = st.sidebar.selectbox(
        "Audio Bitrate",
        options=["128k", "96k", "64k"],
        index=0,
        help="Lower audio bitrate shrinks size but reduces audio fidelity."
    )

    if st.button("Compress Video"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded.name)[1]) as in_tmp:
            in_tmp.write(uploaded.read())
            in_path = in_tmp.name

        out_suffix = ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=out_suffix) as out_tmp:
            out_path = out_tmp.name

        cmd = [
            "ffmpeg",
            "-y",
            "-i", in_path,
            "-vcodec", "libx264",
            "-crf", str(crf_value),
            "-acodec", "aac",
            "-b:a", audio_bitrate,
        ]
        if scale_width and scale_width > 0:
            scale_filter = f"scale='min({scale_width},iw)':'-2'"
            cmd += ["-vf", scale_filter]
        cmd.append(out_path)

        try:
            with st.spinner("Compressing… this may take a moment"):
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            st.error(f"Error during compression:\n```\n{e.stderr.decode('utf-8')}\n```")
        else:
            compressed_size = os.path.getsize(out_path) / 1024 / 1024
            st.success(f"Compression complete! ℹ️ Compressed size: {compressed_size:.2f} MB")
            with open(out_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Compressed Video",
                    data=f.read(),
                    file_name=f"compressed_{os.path.basename(uploaded.name)}",
                    mime="video/mp4"
                )
        try:
            os.remove(in_path)
        except Exception:
            pass
