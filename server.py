from fastapi import FastAPI, HTTPException, Query
from supabase import create_client, Client
import os
import subprocess

# Initialize FastAPI app
app = FastAPI()

# Configure Supabase client
SUPABASE_URL = "https://lserxyzflqtvvasfturo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzZXJ4eXpmbHF0dnZhc2Z0dXJvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjkzNjkzMzMsImV4cCI6MjA0NDk0NTMzM30.BPAeLEFsLbAS63KIpq-at3ZSVaNaedg-gfHuboGrq7Y"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Directories to save files
DATA_DIR = "./project_data" # directory to save project data to
OUTPUT_DIR = "./output" # directory that .ply files get saved to
os.makedirs(DATA_DIR, exist_ok=True)

# Pipeline specific variables
FFMPEG_FRAME_RATE = 2

@app.get("/process_video")
def process_video(bucket_name: str = Query(...), file_path: str = Query(...)):
  """
  Process a video and train splats from it.
  :param bucket_name: The name of the Supabase storage bucket.
  :param file_path: The path of the file in the Supabase bucket.
  :return: The local path where the file was saved.
  """
  
  try:
    start_pipeline(bucket_name=bucket_name, file_path=file_path)
    return {"message": "trained successfully"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/test")
def test_route():
  """
  A test route to verify the API is running.
  """
  return {"message": "API is running successfully!"}


# HELPER FUNCTIONS FOR TRAINING PIPELINE:

def start_pipeline(bucket_name, file_path):
  # create project folder
  proj_path = create_proj_folder()
  
  # download the raw input video
  video_path = download_file(bucket_name=bucket_name, file_path=file_path, local_path=proj_path)
  
  # todo: find the length of the video and calcualte optimal number of frames
  
  # extract frames using ffmpeg
  input_path = os.path.join(proj_path, "/input")
  extract_frames(video_path=video_path, input_path=input_path)
  
  # run colmap for SFM
  run_colmap(proj_path)
  
  # train gaussians
  train_gaussians(proj_path)
  
  # upload .ply file to supabase
  upload_to_supabase(loal_file_path=OUTPUT_DIR, bucket_name=bucket_name, bucket_file_path="path")
  
  # cleanup files
  cleanup_files()

def create_proj_folder(proj_name):
  # Create project folder
  proj_path = os.path.join(DATA_DIR, f"/{proj_name}")
  os.makedirs(proj_path)
  
  # Create /input folder
  input_path = os.path.join(proj_path, "/input")
  os.makedirs(input_path)
  
  return proj_path

def download_file(bucket_name, file_path, local_path):
  """
  Download the video file from supabase
  """
  # Fetch the file from Supabase
  response = supabase.storage.from_(bucket_name).download(file_path)
  
  # Save the file locally
  local_file_path = os.path.join(local_path, os.path.basename(file_path))
  with open(local_file_path, "wb") as f:
    f.write(response)
    
  return local_file_path

def extract_frames(video_path, input_path):
  """
  Extact frames from the video file
  """
  
  command = f"ffmpeg -i {video_path} -qscale:v 1 -qmin 1 -vf fps={FFMPEG_FRAME_RATE} {input_path}/%04d.jpg"
  subprocess.run(command, shell=True, check=True)

def run_colmap(image_folder):
  """
  Run colmap on input images for SFM and generate a COLMAP dataset
  """
  
  command = f"python convert.py -s {image_folder}"
  subprocess.run(command, shell=True, check=True)

def train_gaussians(colmap_path):
  """
  Train gaussians from the COLMAP dataset
  """
  
  command = f"python train.py -s {colmap_path}"
  subprocess.run(command, shell=True, check=True)

def upload_to_supabase(loal_file_path, bucket_name, bucket_file_path):
  """
  Upload the .ply file to supabase
  """
  
  with open(loal_file_path, 'rb') as f:
    response = supabase.storage.from_(bucket_name).upload(
        file=f,
        path=bucket_file_path,
        file_options={"cache-control": "3600", "upsert": "false"},
    )
    
    return response
  
def cleanup_files():
  """
  Removes any directories and files created during the training process
  """
  return 0