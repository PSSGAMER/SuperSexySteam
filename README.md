# SuperSexySteam

This is a tool that makes use of the lack of verification to download games, and works in conjuction with GreenLuma. This is a beta release. I have packed GreenLuma by Steam006 with my code for convinience. Steam006 can contact me if they have issues with it and I will remove it. The eventual plan is to move away from GreenLuma due to its closed source nature and implement my own emulator. I don't have enough knowledge currently to do so

## ⚠️ Why is this in Beta?

This project is currently in beta due to compilation challenges. I'm experiencing trouble compiling all the code into a single executable file (.exe). Once I'm able to successfully compile everything into a standalone executable, I will release the official v1.0. Until then, the project remains in beta and requires manual setup with Python dependencies. I will look into any PRs that help me with this, and also with anything in general. If you have an improvement, dont hesitate to make a PR

## 🚀 Getting Started

Follow these instructions to get a copy of SuperSexySteam up and running on your local machine.

### Prerequisites

Before you begin, ensure you have the following software installed on your system:

*   **Python:** Version 3.8 or newer. You can download it from [python.org](https://www.python.org/downloads/).
*   **Git:** Required to clone the repository. You can download it from [git-scm.com](https://git-scm.com/downloads).

### Installation

These steps will guide you through cloning the repository and setting up a clean, isolated environment for the project.

1.  **Clone the Repository**

    Open your terminal or command prompt and run the following command to download the project files:
    ```sh
    git clone https://github.com/PSSGAMER/SuperSexySteam.git
    ```

2.  **Navigate to the Project Directory**

    Change your current directory to the newly created project folder:
    ```sh
    cd SuperSexySteam
    ```

3.  **Create a Virtual Environment**

    It is highly recommended to use a virtual environment to keep project dependencies isolated from your system's global Python installation. Run the following command:
    ```sh
    python -m venv venv
    ```
    This creates a new folder named `venv` in your project directory.

4.  **Activate the Virtual Environment**

    You must activate the environment before installing packages. The command differs based on your operating system.

    *   **On Windows (Command Prompt or PowerShell):**
        ```sh
        venv\Scripts\activate
        ```

    Your terminal prompt should now be prefixed with `(venv)`, indicating the environment is active.

5.  **Install Required Packages**

    With your virtual environment active, use `pip` to install the necessary Python libraries for the application:
    ```sh
    pip install customtkinter tkinterdnd2 Pillow steam protobuf==3.20.3 gevent-eventemitter
    ```

### Running the Application

Once the setup is complete, you can launch SuperSexySteam with a single command:

```sh
python SuperSexySteam.py
```

#### First-Time Setup

The very first time you run the application, it will detect that `config.ini` is missing and will guide you through a one-time setup:

1.  A pop-up window will ask for your **Steam installation path**. You can leave it empty to use the default (`C:\Program Files (x86)\Steam`).
2.  A second pop-up will ask for your **GreenLuma directory**. You can leave it empty to default to a `GreenLuma` folder present inside the project directory.

After confirming these paths, the settings will be saved to `config.ini`, and the main application will launch. This setup process will not occur on subsequent launches.

## 🎮 Starting Steam with GreenLuma

To run Steam with the SuperSexySteam setup:

1.  **Launch GreenLuma:** Navigate to the `GreenLuma/NormalMode` folder and double-click on `DLLInjector.exe` to start Steam with GreenLuma integration.

2.  **Run Refresh Script:** Always run the refresh script before starting Steam. You should also run it anytime you encounter problems while downloading games. This ensures your cache and configuration are properly synchronized.

**Important:** Make sure to run the refresh script whenever you experience download issues or before each Steam session for optimal performance.
