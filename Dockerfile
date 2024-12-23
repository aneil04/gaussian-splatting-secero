# Chosen to match the CUDA 11.7 installed on this machine
FROM nvidia/cuda:12.0.1-devel-ubuntu22.04

# Install dependencies
ENV DEBIAN_FRONTEND noninteractive
RUN apt update -y
RUN apt install -y build-essential wget dpkg

#  for training
ENV CONDA_DIR /opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

#  for dataset conversion
RUN apt install -y colmap imagemagick

#  cleanup
RUN apt clean && rm -rf /var/lib/apt/lists/*

# Setup Python environment
RUN conda create -n "gaussian_splatting" python=3.10.12
RUN /bin/bash -c "conda init bash"
RUN echo "conda activate gaussian_splatting" >> /root/.bashrc

COPY . /gaussian-splatting-build
WORKDIR /gaussian-splatting-build
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=$CUDA_HOME/bin:$PATH

RUN conda install pip pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia

RUN CUDA_HOME=/usr/local/cuda pip install plyfile tqdm submodules/simple-knn submodules/diff-gaussian-rasterization
# COPY ./environment.yml /gaussian-splatting-build/environment.yml
# WORKDIR /gaussian-splatting-build
# RUN /bin/bash -c "conda init bash"
# RUN echo "conda activate gaussian_splatting" >> /root/.bashrc

# Now mount the actual directory, hopefully
VOLUME /gaussian-splatting-secero
WORKDIR /gaussian-splatting-secero