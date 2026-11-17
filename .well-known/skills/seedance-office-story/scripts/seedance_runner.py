"""Offline-first Seedance preparation, explicit submission, and human-review QC.

Only submit --execute, status, and result perform network requests. API keys stay
in the server environment. A queue result is never visual quality approval.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import ipaddress
import json
import math
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CANONICAL_ENDPOINT = "bytedance/seedance-2.5/us/reference-to-video"
FAL_QUEUE_BASE = "https://queue.fal.run"
MAX_IMAGE_BYTES = 30 * 1024 * 1024
ALLOWED_INPUT_PARAMETERS = {
    "image_urls": list, "aspect_ratio": str, "draft": bool,
    "seed": (int, type(None)), "generate_audio": bool, "resolution": str,
    "end_user_id": (str, type(None)), "video_urls": list, "audio_urls": list,
    "codec": str, "bitrate_mode": str, "task": str, "duration": str,
    "prompt": (str, type(None)),
}
ALLOWED_DURATIONS = {str(i) for i in range(4, 31)}
FIXED_INPUT = {"aspect_ratio": "9:16", "draft": False, "generate_audio": False,
               "resolution": "1080p", "codec": "H264", "task": "reference"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as output:
            output.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8"))
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load_plan(plan_path: Path) -> dict[str, Any]:
    value = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def _https_url(value: Any, *, queue: bool = False) -> str:
    if not isinstance(value, str) or not value or any(c.isspace() or ord(c) < 32 for c in value) or "\\" in value:
        raise ValueError("Expected a valid HTTPS URL")
    try:
        parsed = urllib.parse.urlsplit(value)
        host, port = parsed.hostname, parsed.port
    except ValueError as error:
        raise ValueError("Invalid HTTPS URL") from error
    if parsed.scheme != "https" or not host or parsed.username is not None or parsed.password is not None or parsed.fragment or port not in (None, 443):
        raise ValueError("HTTPS URL must have no credentials, fragment, or nonstandard port")
    if queue:
        if host != "queue.fal.run" or not parsed.path.startswith("/"):
            raise ValueError("Authenticated requests only trust queue.fal.run")
    else:
        if host == "localhost" or host.endswith((".localhost", ".local")):
            raise ValueError("Reference URLs must be publicly reachable HTTPS URLs")
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            address = None
        if address and not address.is_global:
            raise ValueError("Private or loopback reference address is not allowed")
    return value  # Preserve the provider's exact signed URL/route.


def _image_mime(data: bytes) -> str:
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Reference image must contain 1..30 MiB of actual image bytes")
    if len(data) >= 33 and data.startswith(b"\x89PNG\r\n\x1a\n") and data[12:16] == b"IHDR" and b"IEND" in data[-24:]:
        return "image/png"
    if len(data) >= 20 and data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9"):
        return "image/jpeg"
    if len(data) >= 20 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise ValueError("Reference bytes are not a complete JPG, PNG, or WebP image")


def data_uri_for_file(path: Path) -> str:
    data = path.read_bytes()
    mime = _image_mime(data)
    allowed = {"image/png": {".png"}, "image/jpeg": {".jpg", ".jpeg"}, "image/webp": {".webp"}}
    if path.suffix.lower() not in allowed[mime]:
        raise ValueError(f"Image extension does not match bytes: {path.name}")
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _reference_url(value: Any, *, image: bool) -> None:
    if isinstance(value, str) and value.startswith("data:"):
        if not image:
            raise ValueError("Only image data URIs are supported by this workflow")
        match = re.fullmatch(r"data:(image/(?:png|jpeg|webp));base64,([A-Za-z0-9+/=]+)", value)
        if not match or len(value) > MAX_IMAGE_BYTES * 4 // 3 + 128:
            raise ValueError("Invalid or oversized image data URI")
        try:
            content = base64.b64decode(match[2], validate=True)
        except binascii.Error as error:
            raise ValueError("Invalid base64 reference") from error
        if _image_mime(content) != match[1]:
            raise ValueError("Data URI MIME does not match image bytes")
    else:
        _https_url(value)


def validate_input(endpoint: Any, payload: Any) -> None:
    """Enforce the reviewed production contract, not merely vendor defaults."""
    if endpoint != CANONICAL_ENDPOINT:
        raise ValueError("Only the reviewed canonical Seedance endpoint is allowed")
    if not isinstance(payload, dict):
        raise ValueError("input must be an object")
    unknown = set(payload) - set(ALLOWED_INPUT_PARAMETERS)
    if unknown:
        raise ValueError(f"Unsupported input parameter(s): {sorted(unknown)}")
    for key, value in payload.items():
        allowed = ALLOWED_INPUT_PARAMETERS[key]
        types = allowed if isinstance(allowed, tuple) else (allowed,)
        if type(value) not in types:
            raise ValueError(f"Invalid type for input.{key}")
    for key, value in FIXED_INPUT.items():
        if key not in payload or type(payload[key]) is not type(value) or payload[key] != value:
            raise ValueError(f"Production contract requires {key}={value!r} explicitly")
    if payload.get("duration") not in ALLOWED_DURATIONS:
        raise ValueError("duration must be a string integer between 4 and 30")
    if not isinstance(payload.get("prompt"), str) or not payload["prompt"].strip():
        raise ValueError("A nonempty prompt string is required")
    if payload.get("bitrate_mode", "standard") not in {"standard", "high"}:
        raise ValueError("Unknown bitrate_mode")
    total = 0
    for key, maximum in (("image_urls", 30), ("video_urls", 10), ("audio_urls", 10)):
        values = payload.get(key, [])
        if not isinstance(values, list) or len(values) > maximum:
            raise ValueError(f"Invalid {key} reference count")
        if key == "image_urls" and not values:
            raise ValueError("This character-reference workflow requires image_urls")
        for value in values:
            _reference_url(value, image=key == "image_urls")
        total += len(values)
    if total > 50:
        raise ValueError("Total references exceed 50")
    for tag in re.findall(r"@Image(\d+)", payload["prompt"]):
        if not 1 <= int(tag) <= len(payload["image_urls"]):
            raise ValueError(f"Prompt @Image{tag} has no corresponding image_urls entry")


def validate_plan(plan: dict[str, Any], plan_path: Path) -> list[str]:
    if plan.get("endpoint") != CANONICAL_ENDPOINT:
        raise ValueError("Plan endpoint must be the canonical reviewed endpoint")
    units, canon = plan.get("units"), plan.get("canon_assets")
    if not isinstance(units, list) or not units or not isinstance(canon, dict):
        raise ValueError("Plan requires nonempty units and canon_assets")
    warnings, ids, duration_sum = [], set(), 0
    timed = any("timeline_start_sec" in unit or "timeline_end_sec" in unit for unit in units)
    previous_end = 0
    for unit in units:
        if not isinstance(unit, dict) or not isinstance(unit.get("id"), str) or not unit["id"] or unit["id"] in ids:
            raise ValueError("Unit IDs must be unique nonempty strings")
        name = unit["id"]
        ids.add(name)
        duration = unit.get("duration_sec")
        if type(duration) is not int or duration not in range(4, 31):
            raise ValueError(f"Unit {name}: duration must be an integer from 4 to 30")
        duration_sum += duration
        if timed:
            start, end = unit.get("timeline_start_sec"), unit.get("timeline_end_sec")
            if type(start) not in (int, float) or type(end) not in (int, float) or not math.isfinite(start) or not math.isfinite(end) or start != previous_end or end - start != duration:
                raise ValueError(f"Unit {name}: timeline must be contiguous, nonoverlapping, and match duration")
            previous_end = end
        refs = unit.get("references")
        if not isinstance(refs, list) or not 1 <= len(refs) <= 30 or any(not isinstance(key, str) for key in refs) or len(set(refs)) != len(refs):
            raise ValueError(f"Unit {name}: expected 1..30 distinct ordered reference keys")
        for key in refs:
            if key not in canon or not isinstance(canon[key], dict):
                raise ValueError(f"Unit {name}: unknown canonical reference {key}")
            source = canon[key].get("path")
            if not isinstance(source, str) or not source or not (plan_path.parent / source).is_file():
                warnings.append(f"Unit {name}: canonical file not present: {key}")
        prompt_file = unit.get("prompt_file")
        if not isinstance(prompt_file, str) or not prompt_file:
            raise ValueError(f"Unit {name}: prompt_file required")
        prompt_path = plan_path.parent / prompt_file
        if not prompt_path.is_file():
            warnings.append(f"Unit {name}: prompt file missing: {prompt_file}")
            continue
        prompt = prompt_path.read_text(encoding="utf-8-sig")
        for index in re.findall(r"@Image(\d+)", prompt):
            if not 1 <= int(index) <= len(refs):
                raise ValueError(f"Unit {name}: @Image{index} exceeds ordered reference count")
        lower = prompt.lower()
        if "continuous take" in lower and ("hard cut" in lower or "cut to" in lower):
            warnings.append(f"Unit {name}: legacy prompt mixes continuous take and cuts; human review required")
        shots = unit.get("expected_shots")
        cuts = unit.get("expected_internal_cuts")
        if shots is not None and type(shots) is int and shots > 1 and "single continuous generation" in lower:
            warnings.append(f"Unit {name}: legacy multi-shot prompt says single continuous generation; scope must be reviewed")
        if "room tone only" in lower and "no room tone" in lower:
            warnings.append(f"Unit {name}: legacy sound directions conflict; generate_audio=false and final stream inspection still apply")
        if shots is not None and (type(shots) is not int or shots < 1):
            raise ValueError(f"Unit {name}: expected_shots must be a positive integer")
        if cuts is not None and (type(cuts) is not int or cuts < 0):
            raise ValueError(f"Unit {name}: expected_internal_cuts must be a nonnegative integer")
        if shots is not None and cuts is not None and cuts != shots - 1:
            warnings.append(f"Unit {name}: proposed internal cuts do not equal shots minus one")
        numbered = {int(n) for n in re.findall(r"\bshot\s*(\d+)\b", lower)}
        number_words = {word: i for i, word in enumerate(("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"))}
        declared = re.search(r"\b(\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten)\s+hard\s+cuts?\b", lower)
        inferred_shots = shots or (max(numbered) if numbered else None)
        declared_count = (int(declared[1]) if declared[1].isdigit() else number_words[declared[1]]) if declared else None
        if declared and inferred_shots and declared_count != inferred_shots - 1:
            warnings.append(f"Unit {name}: explicit cut count conflicts with shot count; legacy prompt preserved")
    if duration_sum > 30:
        raise ValueError("Total unit duration must not exceed 30 seconds")
    return warnings


def prepare_payloads(plan_path: Path, bindings_path: Path | None = None, use_data_uris: bool = False) -> dict[str, Any]:
    plan_path = plan_path.resolve()
    plan = load_plan(plan_path)
    warnings = validate_plan(plan, plan_path)
    bindings = load_plan(bindings_path) if bindings_path else {}
    canon = plan["canon_assets"]
    if set(bindings) - set(canon):
        raise ValueError(f"Unknown binding keys: {sorted(set(bindings) - set(canon))}")
    for url in bindings.values():
        _https_url(url)
    used = list(dict.fromkeys(key for unit in plan["units"] for key in unit["references"]))
    resolved, sources, missing = {}, {}, []
    for key in used:
        definition = canon[key]
        local = (plan_path.parent / definition["path"]).resolve() if definition.get("path") else None
        present = local is not None and local.is_file()
        if key in bindings:
            resolved[key] = bindings[key]
        elif use_data_uris and present:
            resolved[key] = data_uri_for_file(local)
        else:
            missing.append(key)
            continue
        sources[key] = {"key": key, "role": definition.get("role", "unspecified"),
                        "source": "https_binding" if key in bindings else "local_data_uri",
                        "local_file": str(local) if present else None,
                        "local_sha256": sha256_file(local) if present else None,
                        "size_bytes": local.stat().st_size if present else None,
                        "binding_verified_online": False,
                        "binding_content_sha256": None if key in bindings else sha256_file(local)}
    if missing:
        raise FileNotFoundError(f"Cannot prepare runnable payload: {len(missing)} canon reference(s) missing or unbound: {missing}. Supply HTTPS bindings or actual local files with --data-uris.")
    output = []
    for unit in plan["units"]:
        prompt_path = (plan_path.parent / unit["prompt_file"]).resolve()
        prompt = prompt_path.read_text(encoding="utf-8-sig")
        payload = {**FIXED_INPUT, "image_urls": [resolved[key] for key in unit["references"]],
                   "prompt": prompt, "seed": unit.get("seed"), "bitrate_mode": "standard", "duration": str(unit["duration_sec"])}
        validate_input(CANONICAL_ENDPOINT, payload)
        role_map = [{**sources[key], "image_index": index, "prompt_tag": f"@Image{index}"} for index, key in enumerate(unit["references"], 1)]
        output.append({"unit_id": unit["id"], "endpoint": CANONICAL_ENDPOINT, "input": payload,
                       "metadata": {"duration_sec": unit["duration_sec"], "references": unit["references"],
                                    "reference_role_map": role_map, "prompt_file": str(prompt_path),
                                    "prompt_sha256": sha256_file(prompt_path),
                                    "input_sha256": hashlib.sha256(_json_bytes(payload)).hexdigest(),
                                    "warnings": [w for w in warnings if f"Unit {unit['id']}:" in w],
                                    "human_review_required": True}})
    return {"version": "1.1.0", "prepared_at": now(), "plan_path": str(plan_path),
            "plan_sha256": sha256_file(plan_path), "endpoint": CANONICAL_ENDPOINT,
            "prepared_units": output, "plan_warnings": warnings, "network_performed": False}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "Redirect refused", headers, fp)


def _request_json(url: str, method: str, key: str, body: bytes | None = None) -> dict[str, Any]:
    _https_url(url, queue=True)
    request = urllib.request.Request(url, data=body, headers={"Authorization": f"Key {key}", "Content-Type": "application/json", "User-Agent": "SeedanceRunner/1.1"}, method=method)
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=30) as response:
            if response.geturl() != url:
                raise ValueError("Unexpected response URL; credentials are never forwarded across redirects")
            data = response.read(2 * 1024 * 1024 + 1)
    except urllib.error.HTTPError as error:
        error.close()
        raise
    if len(data) > 2 * 1024 * 1024:
        raise ValueError("Provider response is too large")
    parsed = json.loads(data.decode("utf-8-sig"))
    if not isinstance(parsed, dict):
        raise ValueError("Provider response must be an object")
    return parsed


def _key() -> str:
    value = os.environ.get("FAL_KEY", "").strip()
    if not value or any(c.isspace() for c in value):
        raise RuntimeError("A valid FAL_KEY server environment variable is required")
    return value


def submit_job(prepared_path: Path, job_path: Path, unit_id: str | None = None, execute: bool = False) -> dict[str, Any]:
    prepared = load_plan(prepared_path)
    if prepared.get("endpoint") != CANONICAL_ENDPOINT:
        raise ValueError("Prepared endpoint is not approved")
    units = prepared.get("prepared_units")
    if not isinstance(units, list) or not units:
        raise ValueError("No prepared units")
    names = [unit.get("unit_id") for unit in units if isinstance(unit, dict)]
    if len(names) != len(units) or any(not isinstance(name, str) or not name for name in names) or len(set(names)) != len(names):
        raise ValueError("Prepared unit IDs must be unique")
    if unit_id is None and len(units) != 1:
        raise ValueError("Multiple units require an explicit --unit selection")
    selected = unit_id if unit_id is not None else names[0]
    if selected not in names:
        raise ValueError("Selected unit does not exist")
    unit = units[names.index(selected)]
    validate_input(unit.get("endpoint"), unit.get("input"))
    body = _json_bytes(unit["input"])
    record = {"unit_id": selected, "endpoint": CANONICAL_ENDPOINT,
              "payload_hash": hashlib.sha256(body).hexdigest(), "prepared_file_sha256": sha256_file(prepared_path),
              "status": "submission_pending" if execute else "dry_run_ready", "mode": "live" if execute else "dry-run",
              "created_at": now(), "updated_at": now(), "request_id": None, "status_url": None,
              "response_url": None, "error": None, "automatic_resubmit_allowed": False,
              "qc_status": "not_reviewed", "reference_role_map": unit.get("metadata", {}).get("reference_role_map", [])}
    job_path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive intent file is written/fsynced BEFORE POST; even a crash or a
    # partially written file blocks a second submission using this job path.
    with job_path.open("xb") as output:
        output.write(_json_bytes(record))
        output.flush()
        os.fsync(output.fileno())
    if not execute:
        return record
    try:
        key = _key()
    except RuntimeError:
        record.update(status="failed_config", error="FAL_KEY is missing or invalid", updated_at=now())
        _atomic_json(job_path, record)
        raise
    try:
        response = _request_json(f"{FAL_QUEUE_BASE}/{CANONICAL_ENDPOINT}", "POST", key, body)
        request_id = response.get("request_id")
        if not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,200}", request_id):
            raise ValueError("Missing or malformed request_id")
        record["request_id"] = request_id  # Retain known ID even if returned routes need manual review.
        status_url = _https_url(response.get("status_url"), queue=True)
        response_url = _https_url(response.get("response_url"), queue=True)
        record.update(request_id=request_id, status_url=status_url, response_url=response_url, status="submitted")
    except urllib.error.HTTPError as error:
        record.update(status="submission_rejected" if 400 <= error.code < 500 and error.code != 408 else "submission_unknown", error=f"HTTP {error.code}; no automatic retry")
        error.close()
    except Exception as error:
        record.update(status="submission_unknown", error=f"Ambiguous POST outcome ({type(error).__name__}); do not resubmit automatically")
    record["updated_at"] = now()
    _atomic_json(job_path, record)
    return record


def _load_live_job(path: Path) -> dict[str, Any]:
    record = load_plan(path)
    if record.get("endpoint") != CANONICAL_ENDPOINT or record.get("mode") != "live" or not isinstance(record.get("request_id"), str) or not record["request_id"]:
        raise ValueError("A saved live submission with a request_id is required")
    _https_url(record.get("status_url"), queue=True)
    _https_url(record.get("response_url"), queue=True)
    return record


def _provider_error(data: dict[str, Any]) -> bool:
    return ("error" in data and data["error"] is not None) or bool(data.get("errors")) or data.get("status") in {"ERROR", "FAILED", "CANCELLED"}


def poll_status(job_path: Path) -> dict[str, Any]:
    record = _load_live_job(job_path)
    data = _request_json(record["status_url"], "GET", _key())
    record.update(last_poll_status=data.get("status"), remote_data=data, updated_at=now(), qc_status="not_reviewed")
    if _provider_error(data):
        record["status"] = "failed"
    elif data.get("status") == "COMPLETED":
        record["status"] = "completed_result_unchecked"
    elif data.get("status") in {"IN_QUEUE", "IN_PROGRESS"}:
        record["status"] = data["status"].lower()
    else:
        record["status"] = "remote_status_unknown"
    _atomic_json(job_path, record)
    return record


def fetch_result(job_path: Path, result_path: Path) -> dict[str, Any]:
    if job_path.resolve() == result_path.resolve():
        raise ValueError("Result path must not overwrite the saved job record")
    record = _load_live_job(job_path)
    data = _request_json(record["response_url"], "GET", _key())
    error = _provider_error(data)
    video = data.get("video")
    video_url = video.get("url") if isinstance(video, dict) else None
    if video_url is not None:
        try:
            _https_url(video_url)
        except ValueError:
            error = True
            video_url = None
    if not video_url:
        error = True
    _atomic_json(result_path, data)
    record.update(status="failed" if error else "result_received_unreviewed", result_file=str(result_path.resolve()),
                  result_sha256=sha256_file(result_path), updated_at=now(), qc_status="not_reviewed")
    _atomic_json(job_path, record)
    return {"job_file": str(job_path), "result_file": str(result_path), "video_url": None if error else video_url,
            "has_error": error, "status": record["status"], "qc_status": "not_reviewed", "download_performed": False}


def _number(value: Any) -> float | None:
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (ValueError, TypeError):
        return None


def _fps(value: Any) -> float | None:
    if isinstance(value, str) and "/" in value:
        numerator, denominator = value.split("/", 1)
        n, d = _number(numerator), _number(denominator)
        return n / d if n is not None and d and n > 0 else None
    value = _number(value)
    return value if value and value > 0 else None


def _frames(value: Any) -> int | None:
    number = _number(value)
    return int(number) if number is not None and number >= 0 and number.is_integer() else None


def inspect_qc(video_path: Path, out_dir: Path) -> dict[str, Any]:
    video_path = video_path.resolve()
    if not video_path.is_file():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    if (out_dir / "qc_report.json").resolve() == video_path:
        raise ValueError("QC output must not overwrite the inspected source")
    out_dir.mkdir(parents=True, exist_ok=True)
    initial = video_path.stat()
    source_hash = sha256_file(video_path)
    report: dict[str, Any] = {
        "video_file": str(video_path), "sha256": source_hash, "file_size_bytes": initial.st_size,
        "source_mtime_ns": initial.st_mtime_ns, "inspected_at": now(), "inspection_status": "probe_not_run",
        "ffprobe_available": False, "streams": {}, "qc_status": "human_review_required",
        "nominal_checks": {"target_aspect": "1080x1920 (9:16)", "target_fps": 24,
                           "target_final_duration_sec": 30.0, "target_final_frames": 720, "needs_trim": None,
                           "human_review_required": True, "human_review_checklist": ["face_identity_stability",
                           "geometry_and_perspective_consistency", "clothing_and_badge_plausibility",
                           "no_spurious_text_or_watermarks", "body_motion_naturalness"]},
        "contact_sheet_status": "not_generated", "sample_frames": [],
        "scene_detection": {"performed": False, "note": "Cut heuristics cannot establish shot success."},
    }
    command = ["ffprobe", "-v", "error", "-count_frames", "-show_entries",
               "stream=codec_type,width,height,r_frame_rate,avg_frame_rate,nb_frames,nb_read_frames,codec_name:format=duration,size",
               "-of", "json", str(video_path)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=180)
        data = json.loads(result.stdout)
        stream_list = data.get("streams", [])
        videos = [s for s in stream_list if s.get("codec_type") == "video"]
        audios = [s for s in stream_list if s.get("codec_type") == "audio"]
        report.update(ffprobe_available=True, inspection_status="metadata_inspected", raw_probe=data)
        if not videos:
            raise ValueError("No video stream found")
        video = videos[0]
        width, height = video.get("width"), video.get("height")
        duration = _number(data.get("format", {}).get("duration"))
        fps = _fps(video.get("avg_frame_rate")) or _fps(video.get("r_frame_rate"))
        frames = _frames(video.get("nb_frames"))
        frame_source = "nb_frames"
        if frames is None:
            frames = _frames(video.get("nb_read_frames"))
            frame_source = "nb_read_frames" if frames is not None else "unknown"
        report["streams"] = {"width": width, "height": height, "fps": fps, "codec": video.get("codec_name"),
                             "duration_sec": duration, "frames": frames, "frame_count_source": frame_source,
                             "video_stream_count": len(videos), "audio_stream_count": len(audios),
                             "audio_codecs": [a.get("codec_name") for a in audios]}
        checks = report["nominal_checks"]
        checks.update(resolution_matches=width == 1080 and height == 1920,
                      aspect_ratio_matches=bool(width and height and abs(width / height - 9 / 16) < 0.001),
                      fps_matches=abs(fps - 24) < 0.001 if fps is not None else None,
                      codec_matches=video.get("codec_name") == "h264", raw_audio_absent=len(audios) == 0,
                      duration_within_limit=duration <= 30.001 if duration is not None else None,
                      final_30s_duration_matches=abs(duration - 30) <= 0.001 if duration is not None else None,
                      final_720_frames_match=frames == 720 if frames is not None else None,
                      needs_trim=duration > 30.001 if duration is not None else None)
        if checks["needs_trim"]:
            checks["warning"] = f"Clip duration {duration:.6f}s exceeds nominal 30.0s; inspect and trim in Remotion."
        # Select decoded frame indices and retain actual showinfo PTS timecodes.
        count = frames or (max(1, int(duration * fps)) if duration and fps else None)
        if count:
            indices = sorted({min(count - 1, int(i * count / 16)) for i in range(16)})
            selection = "+".join(f"eq(n,{index})" for index in indices)
            sheet = out_dir / f"contact_sheet_{source_hash[:12]}_{uuid.uuid4().hex[:8]}.jpg"
            vf = f"select='{selection}',showinfo,scale=270:480:force_original_aspect_ratio=decrease,pad=270:480:(ow-iw)/2:(oh-ih)/2,tile=4x4:nb_frames={len(indices)}"
            grid = subprocess.run(["ffmpeg", "-hide_banner", "-v", "info", "-i", str(video_path), "-map", "0:v:0", "-vf", vf, "-frames:v", "1", "-q:v", "3", str(sheet)], capture_output=True, text=True, check=False, timeout=180)
            times = [_number(value) for value in re.findall(r"\bpts_time:([-+0-9.eE]+)", grid.stderr or "")]
            if grid.returncode == 0 and sheet.is_file() and sheet.stat().st_size > 0 and len(times) >= len(indices):
                report.update(contact_sheet=str(sheet.resolve()), contact_sheet_status="generated_for_human_review", contact_sheet_sha256=sha256_file(sheet))
                report["sample_frames"] = [{"cell": i + 1, "source_frame_index": index, "source_pts_time_sec": times[i], "source_sha256": source_hash} for i, index in enumerate(indices)]
            else:
                report["contact_sheet_status"] = "generation_failed_or_unverified"
                sheet.unlink(missing_ok=True)
    except FileNotFoundError:
        report["inspection_status"] = "tool_unavailable"
    except (subprocess.SubprocessError, ValueError, TypeError, KeyError):
        report["inspection_status"] = "inspection_incomplete"
    current = video_path.stat()
    report["source_unchanged"] = current.st_size == initial.st_size and current.st_mtime_ns == initial.st_mtime_ns and sha256_file(video_path) == source_hash
    if not report["source_unchanged"]:
        report["inspection_status"] = "source_changed_during_inspection"
    _atomic_json(out_dir / "qc_report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Seedance offline preparation and explicit queue workflow")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate"); validate.add_argument("plan", type=Path)
    prepare = sub.add_parser("prepare"); prepare.add_argument("plan", type=Path); prepare.add_argument("--out", type=Path, required=True); prepare.add_argument("--bindings", type=Path); prepare.add_argument("--data-uris", action="store_true")
    submit = sub.add_parser("submit"); submit.add_argument("prepared", type=Path); submit.add_argument("--job", type=Path, required=True); submit.add_argument("--unit"); submit.add_argument("--execute", action="store_true")
    status = sub.add_parser("status"); status.add_argument("job", type=Path)
    result = sub.add_parser("result"); result.add_argument("job", type=Path); result.add_argument("--out", type=Path, required=True)
    qc = sub.add_parser("qc"); qc.add_argument("video", type=Path); qc.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "validate":
        warnings = validate_plan(load_plan(args.plan), args.plan)
        print(f"Plan structure checked; {len(warnings)} warning(s). Assets and human review may still be pending.")
        for warning in warnings: print(f"  - {warning}")
    elif args.command == "prepare":
        data = prepare_payloads(args.plan, args.bindings, args.data_uris); _atomic_json(args.out, data)
        print(f"Prepared {len(data['prepared_units'])} unit(s); no network request performed -> {args.out}")
    elif args.command == "submit":
        record = submit_job(args.prepared, args.job, args.unit, args.execute); print(f"Job recorded: {record['status']} -> {args.job}")
    elif args.command == "status": print(f"Queue state: {poll_status(args.job)['status']}; visual QC remains pending")
    elif args.command == "result": print(json.dumps(fetch_result(args.job, args.out), ensure_ascii=False))
    elif args.command == "qc":
        report = inspect_qc(args.video, args.out); print(f"Inspection: {report['inspection_status']}; human review remains required -> {args.out}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(2)
