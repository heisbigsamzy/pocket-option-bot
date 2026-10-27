# Pocket Option Signal Bot Project

## How to Setup in VS Code:

1. Extract this `.zip` file into a folder on your computer.
2. Open **VS Code**, click **File > Open Folder...**, and select the extracted folder.
3. Open the VS Code Terminal (**Ctrl + `** or **Cmd + `**).
4. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Set your Pocket Option Session Token & User ID in your environment or directly inside `server.py`.
6. Start the WebSocket Relay Server:
   ```bash
   python server.py
   ```
7. Open `index.html` in your browser to view your live signal dashboard!
