"""film.py render 결과(무음 영상 + 음악)에 소리를 입혀 완성 MP4를 만든다. 자막은 film.py가 이미 영상 안에 그렸다.
사용: python -X utf8 finish.py --dir <film.py의 --out 폴더> --out <완성.mp4> [--audio <음성.wav|mp3>] [--music-vol 0.35]
음성이 없으면 음악만 넣는다. ffmpeg은 PATH에서 찾고, 없으면 imageio-ffmpeg에 든 것을 쓴다."""
import argparse
import os
import shutil
import subprocess


def find_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        raise SystemExit("ffmpeg을 찾지 못했습니다. PATH에 ffmpeg을 두거나 imageio-ffmpeg을 설치했는지 사용자에게 확인하세요.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="out", help="video_silent.mp4와 music.wav가 있는 폴더")
    ap.add_argument("--out", required=True, help="완성 MP4 경로")
    ap.add_argument("--audio", default=None, help="내레이션 음성(선택)")
    ap.add_argument("--music-vol", type=float, default=None, help="음악 크기. 기본은 음성이 있으면 0.35, 없으면 1.0")
    a = ap.parse_args()

    video = os.path.join(a.dir, "video_silent.mp4")
    music = os.path.join(a.dir, "music.wav")
    for p in (video, music) + ((a.audio,) if a.audio else ()):
        if not os.path.exists(p):
            raise SystemExit(f"파일이 없습니다: {p}")
    vol = a.music_vol if a.music_vol is not None else (0.35 if a.audio else 1.0)

    cmd = [find_ffmpeg(), "-y", "-loglevel", "error", "-i", video, "-i", music]
    if a.audio:
        cmd += ["-i", a.audio]
        af = (f"[1:a]aresample=48000,aformat=channel_layouts=stereo,volume={vol}[m];"
              "[2:a]aresample=48000,aformat=channel_layouts=stereo[n];"
              "[m][n]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=9,aresample=48000,apad[a]")
    else:
        af = f"[1:a]aresample=48000,aformat=channel_layouts=stereo,volume={vol},loudnorm=I=-16:TP=-1.5:LRA=9,aresample=48000,apad[a]"
    # 영상은 다시 인코딩하지 않는다. 소리는 영상 길이에서 끊는다(-shortest).
    cmd += ["-filter_complex", af, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)
    print("saved", a.out)


if __name__ == "__main__":
    main()
