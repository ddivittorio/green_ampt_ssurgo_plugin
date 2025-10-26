# Use continuumio miniconda3 for better compatibility
FROM continuumio/miniconda3:latest

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CONDA_AUTO_UPDATE_CONDA=false
ENV PATH=/opt/conda/bin:$PATH

# Install system dependencies for geospatial libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Create conda environment with geospatial stack
RUN conda create -n green-ampt python=3.10 -y && \
    conda install -n green-ampt -c conda-forge \
        geopandas \
        rasterio \
        pandas \
        numpy \
        requests \
        gdal \
        proj \
        geos \
        -y

# Make RUN commands use the new environment
SHELL ["conda", "run", "-n", "green-ampt", "/bin/bash", "-c"]

# Install additional Python packages
RUN pip install \
    jupyter \
    jupyterlab \
    ipywidgets \
    ipyleaflet \
    matplotlib

# Set the working directory
WORKDIR /app

# Copy requirements and install any additional pip packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application code
COPY . .

# Make sure the external/pysda directory is properly set up
RUN if [ ! -d "external/pysda" ]; then \
        echo "PySDA not found, cloning..." && \
        git clone https://github.com/ncss-tech/pysda external/pysda; \
    fi

# Create necessary directories
RUN mkdir -p outputs/notebook_outputs

# Expose port for Jupyter notebook
EXPOSE 8888

# Set the default command to show help
CMD ["conda", "run", "-n", "green-ampt", "python", "green_ampt.py", "--help"]