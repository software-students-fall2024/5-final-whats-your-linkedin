# SplitSmart

[![CI / CD](https://github.com/software-students-fall2024/5-final-whats-your-linkedin/actions/workflows/build.yml/badge.svg)](https://github.com/software-students-fall2024/5-final-whats-your-linkedin/actions/workflows/build.yml)

![event-logger](https://github.com/software-students-fall2024/5-final-whats-your-linkedin/actions/workflows/event-logger.yml/badge.svg)

**SplitSmart** is a group expense management service, enabling users to effortlessly create groups, add expenses, and evenly split costs among members. This makes it simple to settle shared expenses for trips, events, and more. SplitSmart ensures everyone pays their fair share.

---

## Table of Contents

1. [Features](#features)
2. [Demo](#demo)
3. [Container Image](#container-image)
4. [Teammates](#teammates)
5. [Installation](#installation)
6. [Usage](#usage)
7. [Development Guide](#development-guide)
8. [Contributing](#contributing)
9. [License](#license)
10. [Acknowledgements](#acknowledgements)

---

## Features

- **Group Expense Management**: Create groups and add members.
- **Expense Splitting**: Split expenses evenly or based on custom percentages.
- **Balance Tracking**: Automatically calculates remaining balances for each member.
- **Modern UI**: Visually Appealing UI for ease of use for user.
- **CI/CD**: CI/CD pipeline for consistent building and deployments.

---

## Demo

Add pictures of final product to demo the usage

---

## Container Image

Container images for webapp hosted on dockerhub: https://hub.docker.com/r/popilopi/webapp

---

## Teammates

[Hugo Bray](https://github.com/BringoJr)

[Ethan Cheng](https://github.com/ethanhcheng)

[Jessica Xu](https://github.com/Jessicakk0711)

[Hang Yin](https://github.com/Popilopi168)

---

## Installation

To set up this project locally, follow these steps:

1. **Clone the repository** (or download the files):
    ```bash
    git clone https://github.com/software-students-fall2024/5-final-whats-your-linkedin.git
    cd <repository-folder>
    ```
    
2. **Create a virtual environment**:
    - make sure to create `.env` file under both `web-app` and `machine-learning-client` folder
    - create a virtual environment
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the dependencies**:
    ```bash
    cd webapp/
    pip install -r requirements.txt
    ```

4a. **Build using Docker**:
    ```bash
    docker build -t webapp .
    docker run -p 5001:5000 webapp
    ```
    
- This will start the Flask app inside the container and map it to port 5001 on your host machine. You can access the application at http://127.0.0.1:5001/. 

4b. **Run Locally**:
    ```bash
    python app.py
    ```

---

## Usage

1. **Login/Registration**: Create an account or log in.
2. **Create Groups**: Add groups and members for shared expenses.
3. **Add Expenses**: Log expenses with details such as the payer and split percentage.
4. **View Balances**: See who owes whom and how much is owed.
5. **Group Details**: View all expenses added to the group and individual contribution

---

## Development Guide

### File Structure

- **webapp/**: Contains the main Flask app code, routes, HTML templates, and static files.
- **Dockerfile**: Instructions to build Docker image.

### Technologies Used

- **Frontend**: HTML, CSS, Javascript (Jinja)
- **Backend**: Flask
- **Database**: MongoDB
- **Containerization**: Docker
- **Version Control**: Git/GitHub

### Testing

Run the test file to validate the application:
    ```bash
    pytest
    ```
    
### Deployment

Automated CI/CD pipelines for easy deployment

---

## Contributing

Please follow the following steps to contribute!

1. Fork the repository.
2. Create a branch: `git checkout -b <feature/branch name>`.
3. Commit changes: `git commit -m "<comment about commit changes>"`.
4. Push to the branch: `git push origin <feature/branch name>`.
5. Open pull request.

---

## License

This project is licensed under the [GNU General Public License v3.0](./LICENSE).

You are free to use, modify, and distribute this software under the terms of the license. However, please ensure that any modifications and redistributed versions retain this same license and include proper attribution to the original authors. For full details, see the [LICENSE](./LICENSE) file included in this repository.

---

## Acknowledgments

- Flask Documentation: [Flask](https://flask.palletsprojects.com/)
- MongoDB Documentation: [MongoDB](https://www.mongodb.com/)
- Docker Documentation: [Docker](https://www.docker.com/)
- GitHub Actions for CI/CD
