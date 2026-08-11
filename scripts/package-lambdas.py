import os
import shutil
import subprocess

build_dir = "build"
os.makedirs(build_dir, exist_ok=True)

print("Packaging stream-processor...")
sp_dir = os.path.join(build_dir, "stream-processor")
os.makedirs(sp_dir, exist_ok=True)
subprocess.run(["py", "-m", "pip", "install", "-q", "-r", "services/stream-processor/requirements.txt", "-t", sp_dir])
for item in ["handler.py", "processors", "storage", "models", "utils"]:
    src = os.path.join("services/stream-processor", item)
    dst = os.path.join(sp_dir, item)
    if os.path.isdir(src): shutil.copytree(src, dst, dirs_exist_ok=True)
    else: shutil.copy2(src, dst)
shutil.make_archive(os.path.join(build_dir, "stream-processor"), 'zip', sp_dir)
print("stream-processor.zip created")

print("Packaging analytics-api...")
aa_dir = os.path.join(build_dir, "analytics-api")
os.makedirs(aa_dir, exist_ok=True)
subprocess.run(["py", "-m", "pip", "install", "-q", "-r", "api/analytics/requirements.txt", "-t", aa_dir])
for item in ["handler.py", "queries", "utils"]:
    src = os.path.join("api/analytics", item)
    dst = os.path.join(aa_dir, item)
    if os.path.isdir(src): shutil.copytree(src, dst, dirs_exist_ok=True)
    else: shutil.copy2(src, dst)
shutil.make_archive(os.path.join(build_dir, "analytics-api"), 'zip', aa_dir)
print("analytics-api.zip created")

print("Uploading to S3...")
subprocess.run(["aws", "s3", "cp", os.path.join(build_dir, "stream-processor.zip"), "s3://heycloud-dev-lambda-artifacts-696419969711/stream-processor/stream-processor.zip"])
subprocess.run(["aws", "s3", "cp", os.path.join(build_dir, "analytics-api.zip"), "s3://heycloud-dev-lambda-artifacts-696419969711/analytics-api/analytics-api.zip"])
print("Done")
