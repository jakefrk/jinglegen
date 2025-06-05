# Use the official AWS Lambda Python 3.10 base image
FROM public.ecr.aws/lambda/python:3.10

# Install build dependencies, the libsndfile shared library, and utilities for ffmpeg
# Includes general build tools and LLVM/Clang (dev versions)
# libsndfile is required by the soundfile Python library for audio I/O
# We add tar and xz to decompress the static ffmpeg build.
RUN yum update -y && \
    yum install -y gcc gcc-c++ make cmake llvm-devel clang libsndfile tar xz && \
    yum clean all -y && \
    rm -rf /var/cache/yum

# Download, extract, and install a static build of ffmpeg which includes ffprobe
# Static builds are self-contained and work well in minimal environments like Lambda
ADD https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz /tmp/
RUN tar -xf /tmp/ffmpeg-release-amd64-static.tar.xz -C /tmp && \
    mv /tmp/ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ && \
    mv /tmp/ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ && \
    rm -rf /tmp/ffmpeg-*

# Set the working directory in the container
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy the Lambda handler file and requirements file into the container
COPY lambda_function.py ${LAMBDA_TASK_ROOT}/
COPY requirements.txt ${LAMBDA_TASK_ROOT}/

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Set the CMD to your handler function
# The format is <filename_without_.py>.<handler_function_name>
CMD [ "lambda_function.lambda_handler" ] 