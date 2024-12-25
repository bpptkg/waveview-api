============
Installation
============

This guide will walk you through the installation of the `waveview-api` package.

Requirements

- Python 3.11 or higher
- TimescaleDB 13 or higher
- Redis 6 or higher
- RabbitMQ 3.8 or higher

Installation

Clone the repository:

.. code-block:: bash

    git clone https://github.com/bpptkg/waveview-api.git

Change directory to the project root:

.. code-block:: bash

    cd waveview-api

Create a virtual environment:

.. code-block:: bash

    python3 -m venv venv

Activate the virtual environment:

.. code-block:: bash

    source venv/bin/activate

Install Poetry:

.. code-block:: bash

    pip install poetry

Install the required packages:

.. code-block:: bash

    poetry install

Create a `.env` file:

.. code-block:: bash

    cp .env.example .env

Edit the `.env` file and set the environment variables:

.. code-block:: bash

    vim .env

Create a new Docker volume for TimescaleDB:

.. code-block:: bash

    docker volume create --name=waveview-data

.. warning::

    Store the volume in a safe location. If you delete the volume, all the data
    will be lost. You can also use a bind mount to store the data in a specific
    location on your host machine. For more information, see the Docker
    documentation.

Install TimescaleDB using Docker:

.. code-block:: bash

    docker run --name timescaledb --restart unless-stopped -p 5432:5432 -v waveview-data:/home/postgres/pgdata/data -e POSTGRES_PASSWORD=test -d timescale/timescaledb-ha:pg16

Install Memcached using Docker:

.. code-block:: bash

    docker run -d --restart unless-stopped --name memcached -p 11211:11211 memcached:1.6.32

Install Redis using Docker:

.. code-block:: bash

    docker run --name redis --restart unless-stopped -p 6379:6379 -d redis

Install RabbitMQ using Docker:

.. code-block:: bash

    docker run -d --restart unless-stopped --hostname rabbitmq --name rabbitmq -e RABBITMQ_DEFAULT_USER=user -e RABBITMQ_DEFAULT_PASS=password -p 5672:5672 -p 15672:15672 rabbitmq:3-management

Run the migrations:

.. code-block:: bash

    python manage.py migrate

Create a superuser:

.. code-block:: bash

    python manage.py createsuperuser

Run the server:

.. code-block:: bash

    python manage.py runserver

Run the Celery worker:

.. code-block:: bash

    celery -A waveview worker -l info

Run the Celery beat:

.. code-block:: bash

    celery -A waveview beat -l info

Open your browser and go to ``http://127.0.0.1:8000/admin/`` to access the admin
panel.
