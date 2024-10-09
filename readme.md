# Dagster MongoDB Stock Data Pipeline Demo

## Overview

This repository contains a **demo** pipeline built using **Dagster** to fetch stock data, store it in **MongoDB**, and create a golden layer of the latest stock records. The purpose of this project is to demonstrate basic functionality, and it is **not intended to be a fully-fledged production project**.

## Features

- Pull stock data using **yfinance** for S&P 500 companies.
- Store raw stock data in MongoDB (`stocks_raw_layer`).
- Use MongoDB's aggregation pipeline to extract and transform the freshest data (latest 1 minute) into a golden layer (`stocks_golden_layer`).
- **Dagster** orchestrates the pipeline flow.
- Integration with Docker to manage services such as Dagster, MongoDB, and the pipeline components.

## Structure

- `assets/`: Contains Dagster assets responsible for:
  - Fetching stock data (`pull_stock_data`)
  - Pushing data to the raw MongoDB layer (`push_to_mongo`)
  - Transforming and pushing data to the golden MongoDB layer (`push_to_golden_layer`)

- `docker/`: Contains Docker-related files for setting up the environment, including:
  - Dockerfile for Dagster services
  - `docker-compose.yml` for managing the containerized setup.

- `requirements.txt`: Contains dependencies needed for the project, including Dagster, yfinance, MongoDB, and other related libraries.

## Installation

To run the project, use Docker Compose. This will build and start the necessary services, including Dagster and MongoDB.

```bash
docker compose up --build
