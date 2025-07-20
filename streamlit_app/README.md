## Instructions to build a Container Image 

  * Base Image : `python:3.9-slim`
  * Copy over everything in the build context (streamlit_app) path
  * Installing Dependencies : `pip install -r requirements.txt`
  * Port: 8501 
  * Launch Command : `streamlit run app.py --server.address=0.0.0.0`

## How to run the Docker Image

First, identify your image name. You can list available images with `docker images` and look for `celestialseeker`.

For example, if your image is `celestialseeker/house-price-predictor-ui:d60a432`, use one of the following commands:

*   **Random Port (recommended for development):**
    ```bash
    docker run -itdP celestialseeker/house-price-predictor-ui:d60a432
    ```
    This will map a random host port to the container's port 8501. You can find the mapped port using `docker ps`.

*   **Fixed Port (e.g., 8501):**
    ```bash
    docker run -itd -p 8501:8501 celestialseeker/house-price-predictor-ui:d60a432
    ```
    This will map host port 8501 to the container's port 8501.

**Notes:**
*   The `-P` flag (or `-p` with no specified host port) automatically maps a random host port to the container's exposed port.
*   To view the application logs, use `docker logs <container_id_or_name>`.
*   To find the random port mapped by `-P`, use `docker ps`. Look under the `PORTS` column. For example:
    ```
    CONTAINER ID   IMAGE                                            COMMAND                  CREATED         STATUS         PORTS                                       NAMES
    a1b2c3d4e5f6   celestialseeker/house-price-predictor-ui:d60a432 "streamlit run app.py"   2 seconds ago   Up 1 second    0.0.0.0:32768->8501/tcp, :::32768->8501/tcp   vigilant_hoover
    ```
    In this example, `32768` is the random host port mapped to the container's port 8501.


  