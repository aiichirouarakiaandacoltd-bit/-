import json
import math
import os
import subprocess
import struct
import wave

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_settings():
    path = os.path.join(BASE_DIR, "config", "settings.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_visual_frames(script, output_dir, settings):
    os.makedirs(output_dir, exist_ok=True)
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return _generate_frames_ffmpeg(script, output_dir, settings)

    width = settings["video"]["width"]
    height = settings["video"]["height"]

    font_path = _find_font()
    sections = script["sections"]

    frame_specs = []

    title_img = _create_title_frame(
        script["topic"], script["player"], width, height, font_path
    )
    title_path = os.path.join(output_dir, "frame_000_title.png")
    title_img.save(title_path)
    frame_specs.append({"path": title_path, "duration": 2.0, "label": "title"})

    colors = [
        (20, 20, 60),
        (30, 30, 80),
        (25, 40, 70),
        (20, 50, 60),
        (35, 25, 75),
    ]

    for i, section in enumerate(sections[1:], 1):
        bg_color = colors[i % len(colors)]
        img = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        try:
            font_large = ImageFont.truetype(font_path, 52) if font_path else ImageFont.load_default()
            font_small = ImageFont.truetype(font_path, 36) if font_path else ImageFont.load_default()
            font_label = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
        except Exception:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_label = ImageFont.load_default()

        _draw_court_bg(draw, width, height, bg_color)

        label_text = f"[ {section['label']} ]"
        draw.text((width // 2, 180), label_text, fill=(180, 180, 220), font=font_label, anchor="mm")

        player_text = script["player"]
        draw.text((width // 2, 300), player_text, fill=(255, 215, 0), font=font_large, anchor="mm")

        text = section["text"]
        lines = _wrap_text(text, 15)
        y_start = height // 2 - len(lines) * 30
        for j, line in enumerate(lines):
            draw.text((width // 2, y_start + j * 60), line, fill=(255, 255, 255), font=font_small, anchor="mm")

        draw.text((width // 2, height - 120), "ザ・ダンク", fill=(255, 165, 0), font=font_label, anchor="mm")

        frame_path = os.path.join(output_dir, f"frame_{i:03d}_{section['label']}.png")
        img.save(frame_path)

        time_parts = section["time"].split("-")
        try:
            start_sec = _parse_time(time_parts[0])
            end_sec = _parse_time(time_parts[1]) if len(time_parts) > 1 else start_sec + 10
            duration = end_sec - start_sec
        except (ValueError, IndexError):
            duration = 10.0

        frame_specs.append({"path": frame_path, "duration": duration, "label": section["label"]})

    return frame_specs


def _create_title_frame(topic, player, width, height, font_path):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (width, height), (10, 10, 40))
    draw = ImageDraw.Draw(img)

    _draw_court_bg(draw, width, height, (10, 10, 40))

    try:
        font_title = ImageFont.truetype(font_path, 60) if font_path else ImageFont.load_default()
        font_channel = ImageFont.truetype(font_path, 40) if font_path else ImageFont.load_default()
        font_player = ImageFont.truetype(font_path, 72) if font_path else ImageFont.load_default()
    except Exception:
        font_title = ImageFont.load_default()
        font_channel = ImageFont.load_default()
        font_player = ImageFont.load_default()

    draw.text((width // 2, 250), "ザ・ダンク", fill=(255, 165, 0), font=font_channel, anchor="mm")

    draw.text((width // 2, height // 2 - 100), player, fill=(255, 255, 255), font=font_player, anchor="mm")

    topic_lines = _wrap_text(topic, 14)
    for i, line in enumerate(topic_lines):
        draw.text(
            (width // 2, height // 2 + 50 + i * 70),
            line, fill=(255, 215, 0), font=font_title, anchor="mm"
        )

    _draw_basketball(draw, width // 2, height - 350, 60)

    return img


def _draw_court_bg(draw, width, height, base_color):
    r, g, b = base_color
    line_color = (r + 30, g + 30, b + 30)
    draw.line([(100, height // 2 - 200), (width - 100, height // 2 - 200)], fill=line_color, width=2)
    draw.line([(100, height // 2 + 400), (width - 100, height // 2 + 400)], fill=line_color, width=2)
    draw.arc(
        [(width // 2 - 150, height // 2 + 200), (width // 2 + 150, height // 2 + 500)],
        0, 360, fill=line_color, width=2
    )


def _draw_basketball(draw, cx, cy, radius):
    draw.ellipse(
        [(cx - radius, cy - radius), (cx + radius, cy + radius)],
        fill=(200, 100, 20), outline=(150, 70, 10), width=3
    )
    draw.line([(cx - radius, cy), (cx + radius, cy)], fill=(100, 50, 5), width=2)
    draw.line([(cx, cy - radius), (cx, cy + radius)], fill=(100, 50, 5), width=2)


def _wrap_text(text, max_chars):
    lines = []
    current = ""
    for char in text:
        current += char
        if len(current) >= max_chars:
            if char in "。、,.!?！？ ":
                lines.append(current.strip())
                current = ""
            elif len(current) >= max_chars + 2:
                lines.append(current.strip())
                current = ""
    if current.strip():
        lines.append(current.strip())
    return lines if lines else [text]


def _parse_time(time_str):
    s = time_str.strip().replace("秒", "")
    return float(s)


def _find_font():
    candidates = [
        "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
        "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def _generate_frames_ffmpeg(script, output_dir, settings):
    width = settings["video"]["width"]
    height = settings["video"]["height"]
    frame_specs = []

    for i, section in enumerate(script["sections"]):
        frame_path = os.path.join(output_dir, f"frame_{i:03d}.png")
        color = "0x141432" if i == 0 else f"0x{20+i*5:02x}{20+i*3:02x}{50+i*10:02x}"
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            f"color=c={color}:s={width}x{height}:d=1",
            "-frames:v", "1", frame_path
        ], capture_output=True, timeout=10)

        time_parts = section["time"].split("-")
        try:
            start_sec = _parse_time(time_parts[0])
            end_sec = _parse_time(time_parts[1]) if len(time_parts) > 1 else start_sec + 10
            duration = end_sec - start_sec
        except (ValueError, IndexError):
            duration = 10.0

        frame_specs.append({"path": frame_path, "duration": duration, "label": section.get("label", f"section_{i}")})

    return frame_specs


def create_video_from_frames(frame_specs, narration_path, subtitle_ass, output_path, settings, bgm_path=None):
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    width = settings["video"]["width"]
    height = settings["video"]["height"]
    fps = settings["video"]["fps"]

    temp_dir = os.path.join(os.path.dirname(output_path), "_temp")
    os.makedirs(temp_dir, exist_ok=True)

    segment_files = []
    for i, spec in enumerate(frame_specs):
        seg_path = os.path.join(temp_dir, f"seg_{i:03d}.mp4")
        dur = max(0.5, spec["duration"])
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", spec["path"],
            "-t", str(dur),
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-r", str(fps),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-an",
            seg_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)
        if os.path.exists(seg_path) and os.path.getsize(seg_path) > 0:
            segment_files.append(seg_path)

    concat_list_path = os.path.join(temp_dir, "concat.txt")
    with open(concat_list_path, "w") as f:
        for sf in segment_files:
            f.write(f"file '{sf}'\n")

    raw_video = os.path.join(temp_dir, "raw_video.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-r", str(fps),
        raw_video
    ], capture_output=True, timeout=60)

    narration_aac = os.path.join(temp_dir, "narration.aac")
    subprocess.run([
        "ffmpeg", "-y", "-i", narration_path,
        "-ar", "44100", "-ac", "1",
        "-c:a", "aac", "-b:a", "128k",
        narration_aac
    ], capture_output=True, timeout=30)

    audio_final = narration_aac
    if bgm_path and os.path.exists(bgm_path):
        bgm_vol = settings["bgm"]["volume_ratio"]
        mixed_audio = os.path.join(temp_dir, "mixed_audio.aac")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", narration_aac, "-i", bgm_path,
            "-filter_complex",
            f"[0:a]aformat=sample_rates=44100:channel_layouts=mono[a0];"
            f"[1:a]aformat=sample_rates=44100:channel_layouts=mono,volume={bgm_vol}[a1];"
            f"[a0][a1]amix=inputs=2:duration=shortest[out]",
            "-map", "[out]",
            "-c:a", "aac", "-b:a", "128k",
            mixed_audio
        ], capture_output=True, timeout=30)
        if os.path.exists(mixed_audio) and os.path.getsize(mixed_audio) > 0:
            audio_final = mixed_audio

    narration_dur = _get_duration_ffprobe(audio_final)
    video_dur = _get_duration_ffprobe(raw_video)

    target_dur = narration_dur if narration_dur else video_dur

    video_adjusted = raw_video
    if video_dur and narration_dur and abs(video_dur - narration_dur) > 0.5:
        video_adjusted = os.path.join(temp_dir, "video_adjusted.mp4")
        if video_dur < narration_dur:
            speed = video_dur / narration_dur
            if speed < 0.5:
                speed = 0.5
            subprocess.run([
                "ffmpeg", "-y", "-i", raw_video,
                "-vf", f"setpts={1/speed}*PTS",
                "-r", str(fps),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-an", video_adjusted
            ], capture_output=True, timeout=60)
        else:
            subprocess.run([
                "ffmpeg", "-y", "-i", raw_video,
                "-t", str(narration_dur),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-an", video_adjusted
            ], capture_output=True, timeout=60)

        if not os.path.exists(video_adjusted) or os.path.getsize(video_adjusted) == 0:
            video_adjusted = raw_video

    pre_subtitle = os.path.join(temp_dir, "pre_subtitle.mp4")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_adjusted, "-i", audio_final,
        "-c:v", "copy", "-c:a", "aac",
        "-shortest",
        pre_subtitle
    ], capture_output=True, timeout=60)

    if subtitle_ass and os.path.exists(subtitle_ass):
        ass_escaped = subtitle_ass.replace("\\", "/").replace(":", "\\:")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", pre_subtitle,
            "-vf", f"ass={ass_escaped}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            output_path
        ], capture_output=True, timeout=120)
    else:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", pre_subtitle,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            output_path
        ], capture_output=True, timeout=120)

    _cleanup_temp(temp_dir)

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise RuntimeError(f"動画生成に失敗しました: {output_path}")

    return output_path


def _get_duration_ffprobe(path):
    if not os.path.exists(path):
        return None
    try:
        r = subprocess.run([
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "json", path
        ], capture_output=True, text=True, timeout=10)
        data = json.loads(r.stdout)
        return float(data["format"]["duration"])
    except Exception:
        return None


def _cleanup_temp(temp_dir):
    import shutil
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass


def generate_bgm_tone(output_path, duration=60.0, sample_rate=44100):
    n_samples = int(sample_rate * duration)
    amplitude = 2000

    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        val = int(amplitude * (
            0.5 * math.sin(2 * math.pi * 110 * t) +
            0.3 * math.sin(2 * math.pi * 165 * t) +
            0.2 * math.sin(2 * math.pi * 220 * t)
        ))
        val = max(-32768, min(32767, val))
        samples.append(val)

    with wave.open(output_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    return output_path


def generate_screenshots(video_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    duration = _get_duration_ffprobe(video_path) or 55.0

    timestamps = {
        "start.png": 1.0,
        "middle.png": duration / 2,
        "end.png": max(1, duration - 2),
    }

    for filename, ts in timestamps.items():
        out = os.path.join(output_dir, filename)
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(ts),
            "-i", video_path,
            "-frames:v", "1",
            "-q:v", "2",
            out
        ], capture_output=True, timeout=10)

    return output_dir
