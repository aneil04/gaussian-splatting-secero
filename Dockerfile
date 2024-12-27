# Use NVIDIA's base image with CUDA 12.4
FROM nvidia/cuda:12.4.0-devel-ubuntu20.04

# Set environment variables for CUDA
ENV DEBIAN_FRONTEND=noninteractive
ENV CUDA_VERSION=12.4
ENV PATH=/usr/local/cuda-${CUDA_VERSION}/bin:$PATH
ENV LD_LIBRARY_PATH=/usr/local/cuda-${CUDA_VERSION}/lib64:$LD_LIBRARY_PATH

# Update and install necessary tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev git wget ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# install COLMAP
RUN apt-get update && apt-get install -y \
    git \
    wget \
    cmake \
    ninja-build \
    build-essential \
    libboost-program-options-dev \
    libboost-graph-dev \
    libboost-system-dev \
    libeigen3-dev \
    libflann-dev \
    libfreeimage-dev \
    libmetis-dev \
    libgoogle-glog-dev \
    libgtest-dev \
    libgmock-dev \
    libsqlite3-dev \
    libglew-dev \
    qtbase5-dev \
    libqt5opengl5-dev \
    libcgal-dev \
    libceres-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install COLMAP
RUN git clone https://github.com/colmap/colmap.git && \
    cd colmap && \
    mkdir build && \
    cd build && \
    cmake .. -GNinja -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc && \
    ninja && \
    ninja install

# Clone repo
RUN git clone --recursive https://github.com/aneil04/gaussian-splatting-secero.git
WORKDIR /gaussian-splatting-secero

# Download and install Miniconda
ENV CONDA_DIR=/opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH
RUN conda create -n "gaussian_splatting" python=3.10.12
RUN /bin/bash -c "conda init bash"
RUN echo "conda activate gaussian_splatting" >> /root/.bashrc

# Get pytorch
RUN conda install -y pytorch torchvision torchaudio pytorch-cuda=12.4 -c pytorch -c nvidia

# Get submodules
RUN pip install -q plyfile tqdm ./submodules/diff-gaussian-rasterization ./submodules/simple-knn

CMD [ "python", "server.py" ]