"""Package the stream-processor and analytics-api Lambdas into build/*.zip.

Usage:
    python scripts/package-lambdas.py                 # build only
    python scripts/package-lambdas.py --upload BUCKET # build + upload to S3
    (BUCKET = `terraform output -raw s3_lambda_artifacts_bucket`)
"""

import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")

LAMBDAS = {
    "stream-processor": ("services/stream-processor", ["handler.py", "processors", "storage", "models", "utils"]),
    "analytics-api": ("api/analytics", ["handler.py", "queries", "utils"]),
}


def package(name: str, src_dir: str, items: list) -> str:
    out = os.path.join(BUILD, name)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-r",
         os.path.join(ROOT, src_dir, "requirements.txt"), "-t", out],
        check=True,
    )
    for item in items:
        src = os.path.join(ROOT, src_dir, item)
        dst = os.path.join(out, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(src, dst)
    zip_path = shutil.make_archive(out, "zip", out)
    print(f"{name}.zip created")
    return zip_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upload", metavar="BUCKET", help="S3 Lambda artifacts bucket")
    args = parser.parse_args()

    for name, (src_dir, items) in LAMBDAS.items():
        zip_path = package(name, src_dir, items)
        if args.upload:
            subprocess.run(
                ["aws", "s3", "cp", zip_path, f"s3://{args.upload}/{name}/{name}.zip"],
                check=True,
            )
    print("Done")


if __name__ == "__main__":
    main()
