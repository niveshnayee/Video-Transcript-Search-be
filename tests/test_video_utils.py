from unittest.mock import Mock, patch

import pytest

from app.utils.video_utils import VideoUtils


def test_extract_audio_runs_ffmpeg_command(tmp_path):
    video_path = tmp_path / "sample.mp4"
    audio_path = tmp_path / "sample.wav"
    video_path.write_bytes(b"fake-video")

    completed = Mock(returncode=0, stdout="", stderr="")
    with patch("app.utils.video_utils.VideoUtils.get_ffmpeg_executable", return_value="/opt/homebrew/bin/ffmpeg"):
        with patch("app.utils.video_utils.subprocess.run", return_value=completed) as run:
            result = VideoUtils.extract_audio(str(video_path), str(audio_path))

    assert result == str(audio_path)
    command = run.call_args.args[0]
    assert command[:4] == ["/opt/homebrew/bin/ffmpeg", "-y", "-i", str(video_path)]
    assert command[-1] == str(audio_path)


def test_get_ffmpeg_executable_uses_env_value(tmp_path, monkeypatch):
    ffmpeg_path = tmp_path / "ffmpeg"
    ffmpeg_path.write_text("")
    monkeypatch.setenv("FFMPEG_BINARY", str(ffmpeg_path))

    assert VideoUtils.get_ffmpeg_executable() == str(ffmpeg_path)


def test_get_ffmpeg_executable_uses_homebrew_path_when_not_in_path(tmp_path, monkeypatch):
    ffmpeg_path = tmp_path / "ffmpeg"
    ffmpeg_path.write_text("")
    monkeypatch.delenv("FFMPEG_BINARY", raising=False)
    monkeypatch.setattr(VideoUtils, "HOMEBREW_FFMPEG_PATHS", (str(ffmpeg_path),))

    with patch("app.utils.video_utils.shutil.which", return_value=None):
        assert VideoUtils.get_ffmpeg_executable() == str(ffmpeg_path)


def test_get_ffmpeg_executable_uses_imageio_fallback(monkeypatch):
    monkeypatch.delenv("FFMPEG_BINARY", raising=False)
    imageio_ffmpeg = Mock()
    imageio_ffmpeg.get_ffmpeg_exe.return_value = "/tmp/imageio-ffmpeg"

    with patch("app.utils.video_utils.shutil.which", return_value=None):
        with patch("app.utils.video_utils.Path.exists", return_value=False):
            with patch.dict("sys.modules", {"imageio_ffmpeg": imageio_ffmpeg}):
                assert VideoUtils.get_ffmpeg_executable() == "/tmp/imageio-ffmpeg"


def test_extract_audio_uses_system_ffmpeg_from_path(tmp_path):
    video_path = tmp_path / "sample.mp4"
    audio_path = tmp_path / "sample.wav"
    video_path.write_bytes(b"fake-video")

    completed = Mock(returncode=0, stdout="", stderr="")
    with patch("app.utils.video_utils.shutil.which", return_value="/usr/local/bin/ffmpeg"):
        with patch("app.utils.video_utils.subprocess.run", return_value=completed) as run:
            result = VideoUtils.extract_audio(str(video_path), str(audio_path))

    assert result == str(audio_path)
    command = run.call_args.args[0]
    assert command[:4] == ["/usr/local/bin/ffmpeg", "-y", "-i", str(video_path)]
    assert command[-1] == str(audio_path)


def test_extract_audio_raises_runtime_error_on_ffmpeg_failure(tmp_path):
    video_path = tmp_path / "sample.mp4"
    audio_path = tmp_path / "sample.wav"
    video_path.write_bytes(b"fake-video")

    completed = Mock(returncode=1, stdout="", stderr="no audio stream")
    with patch("app.utils.video_utils.VideoUtils.get_ffmpeg_executable", return_value="ffmpeg"):
        with patch("app.utils.video_utils.subprocess.run", return_value=completed):
            with pytest.raises(RuntimeError, match="Failed to extract audio: no audio stream"):
                VideoUtils.extract_audio(str(video_path), str(audio_path))


def test_extract_audio_raises_runtime_error_when_ffmpeg_missing(tmp_path):
    video_path = tmp_path / "sample.mp4"
    audio_path = tmp_path / "sample.wav"
    video_path.write_bytes(b"fake-video")

    with patch("app.utils.video_utils.VideoUtils.get_ffmpeg_executable", return_value="ffmpeg"):
        with patch("app.utils.video_utils.subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(RuntimeError, match="ffmpeg is required"):
                VideoUtils.extract_audio(str(video_path), str(audio_path))


def test_extract_audio_rejects_missing_paths():
    with pytest.raises(RuntimeError, match="Invalid paths provided"):
        VideoUtils.extract_audio("", "")
