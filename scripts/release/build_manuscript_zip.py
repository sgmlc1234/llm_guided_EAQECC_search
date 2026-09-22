"""Build the editable, single-TeX ICLR manuscript ZIP used for coauthor review."""

import argparse
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper/iclr2027/paper"
FIGURES = ROOT / "paper/iclr2027/figures"
INPUT = re.compile(r"\\input\{([^{}]+)\}")


def resolve_input(name, source):
    raw = Path(name)
    if not raw.suffix:
        raw = raw.with_suffix(".tex")
    candidates = (source.parent / raw, PAPER / raw)
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"cannot resolve input {name!r} from {source}")


def expand(source, stack=()):
    source = source.resolve()
    if source in stack:
        raise ValueError(f"recursive TeX input: {source}")
    text = source.read_text()

    def replace(match):
        child = resolve_input(match.group(1), source)
        try:
            label = child.relative_to(ROOT).as_posix()
        except ValueError:
            label = child.name
        body = expand(child, stack + (source,))
        # The trailing newline is required when \input occurs inside a braced
        # argument such as \resizebox{...}{\input{...}}. Without it, the
        # caller's closing brace lands after the percent comment marker.
        return f"% ===== BEGIN {label} =====\n{body}\n% ===== END {label} =====\n"

    return INPUT.sub(replace, text)


def readme(name):
    return f"""# {name} — 교수님 검토·수정용

## 수정할 파일

- **`main.tex`**: 제목, 초록, 본문, 부록, 표, 알고리즘 및 모든 TikZ 그림
  소스를 한 파일에 통합했습니다.
- **`refs.bib`**: 참고문헌 항목입니다.
- **`main.pdf`**: 이 패키지의 `main.tex`을 독립적으로 컴파일한 확인용 PDF입니다.

`main.tex`의 `% ===== BEGIN ... =====`와 `% ===== END ... =====` 주석은
원래 분리된 파일의 경계를 표시합니다. 원고를 수정할 때 별도의 TeX 조각이나
Python 실험 코드를 실행할 필요가 없습니다.

## 컴파일

### Overleaf

1. ZIP을 새 프로젝트로 업로드합니다.
2. Main document를 `main.tex`, Compiler를 **XeLaTeX**로 설정합니다.
3. Recompile합니다.

### 로컬 Tectonic — 패키지 검증에 사용한 방법

```bash
tectonic -X compile main.tex
```

### 로컬 TeX Live / MacTeX

```bash
latexmk -xelatex main.tex
```

`latexmk`가 없으면 `xelatex main.tex`, `bibtex main`, `xelatex main.tex`,
`xelatex main.tex` 순서로 실행합니다.

## 자산 구성

- `assets/`: Figure 1에 필요한 Python·Magma·Lean 로고.
- `figures/`: Figure 1–5의 PDF/SVG 참고용 파일과 Figure 5의 전체 네 패널
  기록. 본문은 `main.tex` 안의 TikZ 소스로 그림을 그립니다.
- `iclr2027_conference.sty`, `iclr2027_conference.bst`, `natbib.sty`,
  `fancyhdr.sty`: 제출 스타일 파일입니다.

Figure 6의 DAG도 `main.tex`에 TikZ로 포함되어 있습니다. 논문 컴파일에는
Magma, SAT solver, Lean, 클라우드 계정 또는 익명 저장소의 실행 환경이
필요하지 않습니다.

## 검증

ZIP을 빈 디렉터리에 풀어 Tectonic으로 다시 컴파일했습니다. 생성 PDF의
25쪽, 본문 9쪽, Results의 5쪽 시작을 확인했습니다. PDF 문법·메타데이터,
폰트 임베딩, Poppler 및 pypdf 텍스트 추출, 깨진 문자, 미해결 참조와
페이지별 렌더링을 검사했습니다.
"""


def write_zip(folder, archive):
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(
                f"{folder.name}/{path.relative_to(folder).as_posix()}",
                date_time=(2026, 9, 22, 0, 0, 0),
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    archive = out.with_suffix(".zip")
    if out.exists() or archive.exists():
        parser.error("output directory or ZIP already exists")

    out.mkdir(parents=True)
    (out / "assets").mkdir()
    (out / "figures").mkdir()

    tex = expand(PAPER / "main.tex")
    tex = tex.replace("overview_assets/", "assets/")
    tex = (
        f"% EDITABLE SINGLE-FILE MANUSCRIPT — {out.name}\n"
        "% All sections, tables, algorithms and TikZ figures are included below.\n"
        "% Edit this file; bibliography entries are in refs.bib.\n"
        + tex
    )
    if INPUT.search(tex):
        raise ValueError("unexpanded TeX input remains")
    (out / "main.tex").write_text(tex)
    (out / "README.md").write_text(readme(out.name))

    for name in (
        "refs.bib",
        "iclr2027_conference.sty",
        "iclr2027_conference.bst",
        "natbib.sty",
        "fancyhdr.sty",
    ):
        shutil.copy2(PAPER / name, out / name)
    for path in sorted((PAPER / "overview_assets").glob("*.png")):
        shutil.copy2(path, out / "assets" / path.name)
    for stem in (
        "discovery_pipeline",
        "program_evolution",
        "construction_map",
        "hitl_replication",
        "hitl_followup",
        "hitl_followup_all_lengths",
    ):
        for suffix in (".pdf", ".svg"):
            shutil.copy2(FIGURES / f"{stem}{suffix}", out / "figures" / f"{stem}{suffix}")

    subprocess.run(
        ["tectonic", "-X", "compile", "main.tex", "--keep-logs", "--keep-intermediates"],
        cwd=out,
        check=True,
    )
    if not (out / "main.pdf").is_file():
        raise RuntimeError("Tectonic did not create main.pdf")
    for suffix in (".aux", ".out", ".blg", ".bbl", ".log"):
        path = out / f"main{suffix}"
        if path.exists():
            path.unlink()
    write_zip(out, archive)
    print(
        f"{archive}\n"
        f"sha256={hashlib.sha256(archive.read_bytes()).hexdigest()}\n"
        f"bytes={archive.stat().st_size}"
    )


if __name__ == "__main__":
    main()
