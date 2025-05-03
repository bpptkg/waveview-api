===================
Docker Installation
===================

The application can be run in a Docker container. The following steps will guide
you through the process.

Requirements
------------

- Docker 20.10 or higher
- Docker Compose 1.29 or higher

Installation
------------

Clone the repository:

.. code-block:: bash

    git clone https://github.com/bpptkg/waveview-api.git

Change directory to the project root:

.. code-block:: bash

    cd waveview-api

Create a `.env` file:

.. code-block:: bash

    cp .env.example .env

Edit the `.env` file and set the environment variables:

.. code-block:: bash

    vim .env

If you are using custom storage directory, make sure to set the `STORAGE_DIR`
variable to the correct path. The default value is `<PROJECT_ROOT>/storage`.

Because docker containers are isolated from the host system, you need to create
the storage directories in the host system. The following command will create
the necessary directories:

.. code-block:: bash

    mkdir -p storage/{backup,db,logs,media,run,static}

Build the Docker container:

.. code-block:: bash

    docker-compose up --build

The application will be available at http://127.0.0.1:8000.

To create a superuser, run the following command:

.. code-block:: bash

    docker-compose exec web python manage.py createsuperuser

To stop the application, run the following command:

.. code-block:: bash

    docker-compose down

.. warning::

    In the long run, WaveView stream data can be very large (more than 1TB).
    Make sure to have enough disk space available. You can also change the
    docker data volume location to refer to another disk that has more space.
