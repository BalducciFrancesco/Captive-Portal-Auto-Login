#   AutoLoginCaptivePortal

##   Description

This tool is designed to help you automatically log in to captive portals. Captive portals are those login pages you often encounter when connecting to public Wi-Fi networks at places like cafes, airports, and hotels. They usually require you to enter a username/password or accept terms and conditions before you can access the internet.

This script uses a program called Selenium to automate the process of logging in. It's primarily intended to be run on a Linux server, which can be useful for maintaining a consistent network connection for other devices or processes.

##   Configuration Files

- Copy `template.ini` to a new `config.ini` file
- Edit all values under the `[captive_portal]` section according to your requirements
- Credentials should be stored in a file named `credentials.txt` in the same directory as the script, with the format:
  ```
  email
  password
  ```

##   How it Works

Here's a simplified breakdown of how the script works:

1.  **Opens a Web Browser:** The script starts by launching a web browser (Google Chrome) in the background.
2.  **Navigates to the Captive Portal:** The script then directs the browser to the URL of the captive portal login page. Sometimes this URL is automatically detected, but it's best to configure it in the script.
3.  **Locates Login Fields:** The script searches the web page for the username and password input fields. It looks for these fields using their HTML IDs (like "username" and "password").
4.  **Enters Credentials:** The script enters your username and password into the appropriate fields.
5.  **Submits the Form:** The script clicks the login button on the captive portal page, submitting your credentials.
6.  **Checks for Success:** The script then tries to determine if the login was successful. It might look for a specific message on the page, a change in the page title, or the disappearance of the login form.
7.  **Retries if Necessary:** If the login fails, the script will try again a few times.
8.  **Logs Output:** The script provides information about what it's doing in the command line, and it's a good idea to redirect this output to a log file.

##   Features

Here's a summary of the key features:

* **Automatic Login:** Eliminates the need to manually log in to captive portals every time you connect to a new network.
* **Linux Server Compatible:** Designed to run on Linux servers, making it suitable for automated tasks.
* **Headless Mode:** Can run Chrome in "headless" mode, meaning it doesn't need a visible graphical display. This is important for servers.
* **Cron Job Friendly:** Can be easily scheduled to run at regular intervals using the `cron` utility on Linux. This allows you to maintain a persistent connection.
* **Error Handling:** Includes basic error handling to deal with common issues, such as the captive portal being temporarily unavailable or the login failing.
* **Configuration:** The script is configured through variables at the beginning of the file, allowing you to easily customize the username, password, and captive portal URL.
* **Clear Output:** Provides informative messages in the command-line output, indicating the progress of the login process.

##   Dependencies

To use this tool, you'll need the following software:

* **Python 3:** The script is written in Python 3. You can check if you have it installed by typing `python3 --version` in your terminal. If not, you can download it from the Python website or install it using your Linux distribution's package manager.
* **Selenium:** Selenium is a powerful tool for automating web browsers. You can install it using pip, the Python package installer. Open a terminal and type:

    `pip install selenium`
* **ChromeDriver:** ChromeDriver is a special driver that allows Selenium to control Google Chrome. On Debian/Ubuntu-based systems, you can install it with:

    `sudo apt install chromium-driver`

    This should install a version of ChromeDriver that is compatible with the version of Chrome on your system.
* **crontab:** `crontab` is a standard Linux utility used for scheduling commands to run automatically at specific times or intervals. It's usually already installed on most Linux systems.
* **(Optional) Xvfb:** Xvfb is a "virtual framebuffer" that allows you to run graphical applications (like Chrome) without a physical display. This is necessary if you want to run the script in headless mode on a server that doesn't have a monitor. You can install it on Debian/Ubuntu with:

    `sudo apt install xvfb`

##   Installation

Here's how to get the script and make it ready to use:

1.  **Install Dependencies:** Make sure you have all the required software installed, as described in the "Dependencies" section above.
2.  **Download the Script:** You can download the script file (e.g., `captive_portal_login.py`) to your server. If you are using a Git repository, you can clone it using the `git clone` command. For example:

    `git clone https://github.com/your-repo/your-repo.git  # Replace with the actual URL`

    `cd your-repo`
3.  **Make the Script Executable:** You need to give the script permission to run as a program. Open a terminal and navigate to the directory where you saved the script. Then, use the `chmod` command:

    `chmod +x captive_portal_login.py`

##   Configuration

Before you can use the script, you need to configure it with your specific information. This is done by editing the variables at the beginning of the `captive_portal_login.py` file. You can use a text editor like `nano` or `vim` to edit the file. For example:

    `nano captive_portal_login.py`

Here are the variables you need to configure:

* `USERNAME`: Replace `"your_username"` with your actual username for the captive portal. For example:

    `USERNAME = "myusername123"`
* `PASSWORD`: Replace `"your_password"` with your actual password for the captive portal. For example:

    `PASSWORD = "mypassword456"`
* `URL`: Replace `""` with the URL of the captive portal login page, if you know it. For example:

    `URL = "http://captiveportal.example.com/login"`

    If you leave this empty, the script will try to figure out the URL automatically, but it's more reliable if you provide it.
* `HEADLESS`: This variable controls whether the script runs Chrome in headless mode.
    * `HEADLESS = True`: (Recommended for servers) Runs Chrome in the background, without a visible window.
    * `HEADLESS = False`: Runs Chrome with a visible window. This can be useful for debugging, but it requires a graphical display.

    For example, to run in headless mode:

    `HEADLESS = True`

Save the changes you make to the `captive_portal_login.py` file.

##   Usage

Once you've installed the dependencies and configured the script, you can use it to log in to captive portals.

1.  **Save the Script:** Make sure you've saved the script (e.g., as `captive_portal_login.py`).
2.  **Make it Executable:** Use the `chmod +x captive_portal_login.py` command to make the script executable.
3.  **Edit Configuration:** Configure the `USERNAME`, `PASSWORD`, and `URL` variables in the script.
4.  **Run Manually:** You can run the script manually from the command line:

    `./captive_portal_login.py`

    This will run the script once and attempt to log in to the captive portal.

##   Setting up Automatic Login with Cron

To automate the login process, you can use `cron`, a job scheduler in Linux. This allows you to schedule the script to run at regular intervals.

1.  **Open the Crontab Editor:** Open a terminal and type the following command:

    `crontab -e`

    This will open the crontab file in a text editor (usually `nano` or `vi`).

2.  **Add a Cron Job:** Add a line to the crontab file that specifies when and how to run the script. Here's an example to run the script every 30 minutes:

    `*/30 * * * * /usr/bin/python3 /path/to/captive_portal_login.py > /var/log/captive_portal_login.log 2>&1`

    Let's break down this line:

    * `*/30 * * * *`: This part specifies the schedule. In this case, it means "run every 30 minutes."
        * The first `*` is for minutes (0-59). `*/30` means "every 30 minutes".
        * The second `*` is for hours (0-23).
        * The third `*` is for the day of the month (1-31).
        * The fourth `*` is for the month (1-12).
        * The fifth `*` is for the day of the week (0-6, where 0 is Sunday).
    * `/usr/bin/python3`: This is the path to the Python 3 executable on your system. You can find the correct path by typing `which python3` in your terminal.
    * `/path/to/captive_portal_login.py`: This is the path to the `captive_portal_login.py` script that you downloaded. Replace this with the actual path. For example, if you saved the script in your home directory, it might be `/home/yourusername/captive_portal_login.py`.
    * `> /var/log/captive_portal_login.log 2>&1`: This part redirects the output of the script to a log file.
        * `>` redirects the standard output (what the script prints) to the file `/var/log/captive_portal_login.log`.
        * `2>&1` redirects the standard error (error messages) to the same file.
        * It's highly recommended to use a log file so you can check for any errors or problems.

    Here are a few more examples of cron schedules:

    * Every hour: `0 * * * * /usr/bin/python3 /path/to/your/script.py`
    * Every day at 6 AM: `0 6 * * * /usr/bin/python3 /path/to/your/script.py`
    * Every Monday at 8 AM: `0 8 * * 1 /usr/bin/python3 /path/to/your/script.py`

3.  **Save the Crontab File:** After adding the line to the crontab file, save the file and exit the editor. If you're using `nano`, press `Ctrl+O` to save and `Ctrl+X` to exit. If you're using `vi` or `vim`, press `Esc`, then type `:wq` and press `Enter`.

##   Important Notes

* **Password Security:** This script stores your captive portal password in plain text within the script file. This is generally not the most secure way to store passwords. If security is a major concern, you might want to explore more secure methods, such as using a keyring application or an environment variable (though these add complexity). For a simple, automated login on a server you control, this method is often used, but be aware of the risk. **Do not share your script with anyone you don't trust.**
* **Captive Portal Changes:** Captive portals can change their website layout or login process. If this happens, the script may stop working, and you'll need to update the script to reflect the changes. This usually involves inspecting the HTML of the login page and adjusting the element selectors in the script.
* **Check the Logs:** It's crucial to monitor the log file (e.g., `/var/log/captive_portal_login.log`) for any error messages or unexpected behavior. This will help you troubleshoot problems and ensure the script is running correctly.
* **Network Connectivity:** The server running this script must have a working internet connection. The script itself does not establish the initial network connection; it only handles the captive portal login.
* **Crontab:** Crontab is a powerful tool, but it can be a bit tricky to get the syntax right. Be sure to double-check your cron schedule to make sure it's doing what you intend. You can use online cron schedule generators to help you create the correct syntax. Also, remember that cron might not run immediately. It will run at the next scheduled time.
* **Browser Updates:** Keep your Chrome browser and ChromeDriver up-to-date. Incompatibilities between Chrome and ChromeDriver can cause Selenium to fail. The `apt install chromium-driver` command should help with this.

##   Disclaimer

This script is provided "as is," without any warranty. Use it responsibly and at your own risk. I am not responsible for any issues that may arise from its use, including any problems with your network connection or any unintended consequences. Always ensure that you are complying with the terms of service of the network you are connecting to. Using this script to bypass captive portals in an unauthorized way may be against the terms of service and could have consequences.
