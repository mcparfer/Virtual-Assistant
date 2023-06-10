# Virtual-Assistant with Python

**Virtual-Assistant with Python** is a Python-based Virtual Assistant for Windows that aims to enhance user productivity by providing centralized access to various services. The assistant offers the following functionalities:

- Calendar and email services through integration with the available APIs on the Google Cloud Platform (GCP).
- A question and answer channel powered by Artificial Intelligence (AI).
- Local machine control options.

Link with executable: https://drive.google.com/drive/folders/1v6gu1lvAbh5OVVIZ56rSRK1CCT35cQjD?usp=sharing.

This document provides instructions on how to set up and install the project in a virtual environment using the `requirements.txt` file.

## Components

The project consists of the following three modules:

1. `main.py`: This module serves as the entry point of the application and provides the overall control flow and user interaction.

2. `gui.py`: This module contains the graphical user interface (GUI) components, allowing users to interact with the virtual assistant through an intuitive interface.

3. `ui_functions.py`: This module houses the core functionalities of the virtual assistant, including calendar and email services, AI-driven question and answer capabilities, and local machine control options.

4. `/assets` dir: This directory contains the necessary fonts, sounds, and icons used by the app.


## Prerequisites

Before proceeding with the installation, ensure that you have the following software installed on your system:

- Python (version 3.10.4)
- pip (version 23.0.1)
- virtualenv (version 20.23.0)

## Installation

To install and set up the project in a virtual environment, follow the steps below:

1. Clone the project repository from [GitHub](https://github.com/mcparfer/Virtual-Assistant) or download and extract the project ZIP file.

2. Open a terminal or command prompt and navigate to the project's root directory.

3. Create a virtual environment by executing the following command:

   ```bash
   virtualenv ven
   ```

4. Activate the virtual environment:

   ```bash
   venv\Scripts\activate
   ```
   
5. Once the virtual environment is activated, you should see (venv) in your command prompt.

6. Install the project dependencies from the requirements.txt file:

   ```bash
   pip install -r requirements.txt
   ```
   
This command will read the requirements.txt file and install all the necessary Python packages in your virtual environment.

## Google Cloud Platform Credentials

To use the **Virtual-Assistant with Python** project, you'll need to set up credentials on Google Cloud Platform. Follow these steps:

1. Create a project on https://console.cloud.google.com/.

2. Enable the necessary Google Calendar and Gmail APIs.

3. Generate service account credentials by following the instructions provided in https://cloud.google.com/docs/authentication/getting-started.

4. Download the JSON key file for your service account.

5. Store the JSON key file securely on the auth dir from the project. It should be named "credentials.json".
