# Sound File Explorer

Sound File Explorer is a Python application that allows users to explore and manage sound files in a library. 

## Features

- **Graphical User Interface (GUI):** The application provides a user-friendly GUI that displays directories and files in a tree view.
- **Search Functionality:** Users can search for specific sound files using keywords.
- **Playback:** The application supports playback of sound files.
- **Directory Management:** Users have the ability to add and remove directories from the library.
- **File Information:** Detailed information about the sound files is displayed in a table when a directory is selected.
- **Persistent Storage:** The application stores library information persistently using a pickled file.

## Work in Progress

The following features are currently under development:

- **File Navigation:** The ability to open the location of the original files is being added.

## Setup

This project uses a virtual environment to manage dependencies. To set up the project:

1. Clone the repository:
https://github.com/paolini-sounds/sound_file_explorer

3. Navigate to the project directory:
  cd repository

4. Create a virtual environment:
  python3 -m venv env

5. Activate the virtual environment:
- On Windows:
  ```
  .\env\Scripts\activate
  ```
- On Unix or MacOS:
  ```
  source env/bin/activate
  ```
5. Install the required packages:
   pip install -r requirements.txt

## Dependencies

The application requires the following Python libraries:

- `PySimpleGUI`: For creating the graphical user interface.
- `pygame`: For playing sound files.
- `mutagen`: For extracting metadata from sound files.
- `wave`: For reading WAV files.
- `contextlib`: For managing context.
- `threading`: For handling concurrent tasks.
- `queue`: For implementing queues.

## Usage

1. Run the script.
2. Use the GUI to navigate directories and search for sound files.
3. Play or delete sound files as needed.
4. Add or remove directories from the library.
5. Open files in their original location if required.

## How to Run

Ensure you have Python installed on your system. Then, install the required dependencies using pip:

```bash
pip install PySimpleGUI pygame mutagen wave contextlib threading queue

Finally, run the script:

python sound_file_explorer.py

Note
This script currently supports WAV, MP3, and AIFF file formats.
Ensure that sound files are properly formatted and accessible in the specified directories.
Please ensure that the script has the necessary permissions to read from and write to the directories where your sound files are stored. If the script does not have these permissions, it may not function as expected.
Feel free to modify and extend the script according to your requirements.

