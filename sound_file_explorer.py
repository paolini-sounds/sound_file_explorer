"""
A Python script to explore sound files in a library.
- The app has a GUI that displays the directories and files in a tree view.
- The user can search for sound files by keyword.
- The user can play and delete sound files.
- The user can add and remove directories from the library.
- Users can choose to open the file in its orginal location.
- When certain directories are selected, the user will be able to view the files in the table.
- Library information is stored in a pickled file.
"""

import sys
import os
import pickle
import PySimpleGUI as sg
import subprocess
import math
import pygame as pg
import time
import wave
import contextlib
import threading
from queue import Queue
from mutagen.mp3 import MP3
from mutagen.aiff import AIFF



class Gui:        
    def __init__(self):
        
        #layout for the GUI
        
        #table layout      
        headings = ['File Name', 'Type', 'Length']
        self.tableData = []
        table = [sg.Table(values=self.tableData, headings=headings, key='-TABLE-',
                           num_rows=50, justification='right', alternating_row_color='black',
                           enable_click_events=True, bind_return_key=True,
                           auto_size_columns=False, col_widths=[30, 10, 10])] 
        
        #top row layout
        search = [[sg.Text("Enter search term:")],
                [sg.Input(size=(25,1), focus=True, key="-TERM-", enable_events=True)],
                [sg.Button('Search Sounds', size=(15,1), bind_return_key=True, key="-SEARCH-")],
                [sg.Sizer(100, 10)]]
        
        status = [sg.Text('', size=(1, 1), key='-STATUS-', expand_x=True, justification='right')]
        
        # tab groups
        self.treeData = sg.TreeData()
        tree = [sg.Tree(data=self.treeData,
                   auto_size_columns=True,
                   select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                   num_rows=50,
                   col0_width=20,
                   key='-TREE-',
                   show_expanded=False,
                   enable_events=True,
                   expand_x=True,
                   expand_y=True,)]

        #column layout
        col1 =  [[sg.Input(visible=False, enable_events=True, key='-ADD-'),
                 sg.FolderBrowse('Add Directory', key='-BROWSE-', enable_events=True),
                 sg.Button('Delete Selected', key='-DELETE-', button_color=('white', 'red'))], tree]
        
        col2 = [[sg.Text('Results:'), sg.Sizer(200,10),
                 sg.Button('Open in original location', visible=False, key='-OPEN-', enable_events=True)], table]
        
        #music player
        musicplayer = [[sg.Button('Play', key='-PLAY-', button_color=('white', 'green')),
                       sg.Button('Stop', key='-STOP-', button_color=('white', 'red')),
                       sg.Text('Volume:'),
                       sg.Slider(range=(0, 100), orientation='h', default_value=75,
                                 size=(12, 7), key='-VOLUME-', enable_events=True)]]
        
      
        self.layout = [[search, status, sg.Sizer(100, 10)],
                       [sg.Column(col1), sg.Column(col2)],
                       [sg.Column(musicplayer, justification='center')],
                       [sg.Text('Output:')],
                       [sg.Output(size=(100, 10)), sg.Sizegrip()]]
        self.window = sg.Window('Sound File Explorer', self.layout, finalize=True)
        self.window['-TREE-'].expand(True, True)

class File:
    def __init__(self, path, queue=None):
        self.path = path
        self.queue = queue
        self.index = None
        #file name does not include the extension
        self.name = os.path.splitext(os.path.basename(path))[0]
        self.file_type = os.path.splitext(path)[-1]
        self.length = '...'
        

    def play(self):
        # Play the file
        pass

    def delete(self):
        # Delete the file
        pass
    
    def getLength(self):
        threading.Thread(target=self.calculateLength).start()
    
    def calculateLength(self):
        try:
            with contextlib.closing(wave.open(self.path,'r')) as f:
                if self.file_type == '.wav':
                    # use wave to get the length of the wav file
                    frames = f.getnframes()
                    rate = f.getframerate()
                    length = frames / float(rate)
                elif self.file_type == '.mp3':
                    # use mutagen to get the length of the mp3 file
                    audio = MP3(self.path)
                    length = audio.info.length
                elif self.file_type == '.aiff':
                    # use mutagen to get the length of the aiff file
                    audio = AIFF(self.path)
                    length = audio.info.length
                # display the length in minutes and seconds
                minutes = math.floor(length / 60)
                seconds = round(length % 60)
                self.length = f"{minutes}:{seconds:02}"
                if self.queue:
                    self.queue.put((self.path, self.length))
        except Exception as e:
            print(f"Failed to get length of {self.path}: {e}")
            
        

class Directory:
    
    FILE_TYPES = ('.mp3', '.wav', '.aiff')
    
    def __init__(self, path):
        self.path = path
        self.subdirectories = {}
        self.name = os.path.basename(path)
        self.audio_files = self.getFiles()
        self.parent = ''

    def getFiles(self):
        self.audio_files = {}
        # Get a list of audio files in the directory       
        notAdded = 0
        for root, dirs, files in os.walk(self.path):
            contains_audio = False

            for file in files:
                file_type = os.path.splitext(file)[-1]

                
                if file_type in Directory.FILE_TYPES:
                    # Create a new File object and add it to self.audio_files
                    self.audio_files[os.path.join(root, file)] = File(os.path.join(root, file))
                    contains_audio = True

            if contains_audio and root != self.path:
                # Create a new Directory object for the current directory
                self.subdirectories[root] = Directory(root)
            if not contains_audio:
                notAdded += 1
        
        if notAdded > 0:
            print(f"{notAdded} directories were not added because they do not contain audio.")
        return self.audio_files            


        
    
    def toTreeData(self, gui):
        # Use the full path as the key
        key = self.path
        
        # Create a list of subdirectory names
        subdirectory_names = []
        for subdirectory in self.subdirectories.values():
            subdirectory_names.append(subdirectory.name)
        
        # Insert the current directory into the tree
        gui.treeData.Insert(self.parent, key, self.name, tuple(subdirectory_names))
        if self.subdirectories:
            # Recursively generate the tree data for subdirectories
            for subdirectory in self.subdirectories.values():
                subdirectory.toTreeData(gui)

    def rename(self, new_name):
        # Rename the directory
        pass

    def delete(self):
        # Delete the directory
        pass


#Creates the functionality for the SoundFileExplorer
class SoundFileExplorer:
    def __init__(self, file_queue):
        self.loadState()
        self.file_queue = file_queue
        self.fileCache = {}

    def addDirectory(self, directory, parent=''):
        # add the directory and its subdirectories to the directory_map
        d1 = directory
        queue = [(directory, parent)]
        while queue:
            current, parent = queue.pop(0)                
            self.directory_map[current.path] = current
            current.parent = parent
            for subdirectory in current.subdirectories.values():
                queue.append((subdirectory, current.path))

    def removeDirectory(self, values):
        # Remove the Directory object for path from self.directories
        try:
            self.directory_map.pop(values['-TREE-'][0], None)
            #if drive is removed, remove all subdirectories
            for key in list(self.directory_map.keys()):
                if key.startswith(values['-TREE-'][0]):
                    self.directory_map.pop(key, None)
            #if directory is a subdirectory, remove it from the parent directory
            parent = os.path.dirname(values['-TREE-'][0])
            if parent in self.directory_map:
                self.directory_map[parent].subdirectories.pop(values['-TREE-'][0], None)
                
        #raise KeyError if the key is not found
        except KeyError:
            sg.popup_error(f"KeyError: {values['-TREE-'][0]}")
        except Exception as e:
            sg.popup_error(f"Failed to remove directory: {e}")
            

    def search(self, values):
        term = values['-TERM-']
        print(f"Searching for {term}")
        
        self.matches = 0
        self.results = []
        self.records = 0
        # Search for audio files by keyword
        try:
            for directory in self.directory_map.values():
                for file_path in directory.audio_files.keys():
                    self.records += 1
                    if term in os.path.basename(file_path):
                        self.results.append(File(file_path, self.file_queue))
                        self.matches += 1
        except Exception as e:
            sg.popup_error(f"Failed to search for {term}: {e}")
            self.results = []
            self.matches = 0
            self.records = 0
    
    # Handles the event when a tree item is selected
    def handleTreeEvent(self, values, sfe):
        start_time = time.time()
        try:
            if '-TREE-' in values and values['-TREE-']:
                # Get the key of the selected item
                key = values['-TREE-'][0]
                # Get the Directory object for the selected item
                directory = self.directory_map[key]         
                tableData = []
                if len(directory.audio_files) == 0:
                    return tableData
                index = 0
                for file_path in directory.audio_files.keys():
                    #check if already in fileCache
                    if file_path in sfe.fileCache:
                        for file in sfe.fileCache[file_path]:
                            file.index = index
                            tableData.append([file.name, file.file_type, file.length, file.path])
                            index += 1
                    else:
                        file = File(file_path, self.file_queue)
                        file.index = index
                        file.getLength()
                        sfe.fileCache[file.path] = [file]
                        tableData.append([file.name, file.file_type, file.length, file.path])
                        index += 1
                end_time = time.time()
                print(f"Time to update table: {end_time - start_time}")
                return tableData
        except Exception as e:
            sg.popup_error(f"Failed to update table: {e}")
            
    def saveState(self):
        # Use pickle to save the state of the explorer
        with open('explorer.pkl', 'wb') as f:
            pickle.dump(self.directory_map, f)

    def loadState(self):
        # Use pickle to load the state of the explorer
        try:
            with open('explorer.pkl', 'rb') as f:
                self.directory_map = pickle.load(f)
        except:
            #initialize directories if not found
            self.directory_map = {}
    
    def clearState(self):
        # Clear the state of the explorer
        self.directory_map = {}


def updateAudioTable(sfe, g, values):
    #update the table
    try:
        index = 0
        for file in sfe.results:
            #check if already in fileCache
            if file.length == '...':
                file.getLength()
            file.index = index
            g.tableData.append([file.name, file.file_type, file.length])
            g.window['-TABLE-'].Update(values=g.tableData)
            sfe.fileCache[file.path] = [file]
            index += 1
        print(f"{sfe.matches } Matches for {values["-TERM-"]} out of {sfe.records} records.")
    except Exception as e:
        sg.popup_error(f"Failed to update table: {e} : {file}")

def main():
    sg.set_options(suppress_raise_key_errors=False, suppress_error_popups=False, suppress_key_guessing=False)
    
    #create queue for file objects
    file_queue = Queue()
    #create explorer object
    sfe = SoundFileExplorer(file_queue) 
    sfe.loadState()

    #Create object for music player
    pg.mixer.init()
    is_playing = False
    
    table_update = False
   
    g = Gui()      
    #Update tree with directories 
    for directory in sfe.directory_map.values():
        #if directory is at the root, add it to the tree
        if directory.parent == '':
            directory.toTreeData(g)
    g.window['-TREE-'].Update(g.treeData)     
    
    #Flag to ignore repeated events
    ignore = False
    #main event loop    
    while True:
        event, values = g.window.Read()
        print("<<", event)
        print("<<", values)
        #debugging
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        
        if event == '-ADD-' and not ignore:
            ignore = True
            file_queue.queue.clear()
            g.window['-STATUS-'].Update(f"Adding {values['-ADD-']} to the library...")
            try:
                newDirectory = Directory(values["-ADD-"])            
                sfe.addDirectory(newDirectory)
            except Exception as e:
                g.window['-STATUS-'].Update(f"Failed to add {values['-ADD-']} to the library.")            
            try:
                newDirectory.toTreeData(g)
                g.window['-TREE-'].Update(g.treeData)
                g.window['-STATUS-'].Update(f"Added {values['-ADD-']} to the library.")
            except:
                error_type, error_value, traceback = sys.exc_info()
                #create txt file with error message:
                g.window['-STATUS-'].Update(f"Failed to add {values['-ADD-']} to the library.")
            finally:
                ignore = False
            
        if event == '-DELETE-' and not ignore:
            ignore = True
            sfe.removeDirectory(values)
            #clear tree and table
            g.treeData = sg.TreeData()
            g.window['-TREE-'].Update(g.treeData)
            g.tableData = []
            g.window['-TABLE-'].Update(values=g.tableData)
            #update tree to display remaining directories
            for directory in sfe.directory_map.values():
                directory.toTreeData(g)
                g.window['-TREE-'].Update(g.treeData)
            ignore = False
            
        if event == "-SEARCH-" and values["-TERM-"] != "" and not ignore:
            ignore = True
            g.window['-STATUS-'].Update(f"Searching for {values['-TERM-']}...")
            file_queue.queue.clear()
            sfe.search(values)
            g.window['-TERM-'].Update('')
            updateAudioTable(sfe, g, values)
            table_update = True
            g.window['-STATUS-'].Update(f"Showing {sfe.matches} matches for {values['-TERM-']} out of {sfe.records} records.")
            ignore = False
                
        if event == "-TREE-" and values["-TREE-"] and not ignore:
            ignore = True
            file_queue.queue.clear()
            try:
                print("Selected: ", values["-TREE-"][0])
                if len(sfe.directory_map[values['-TREE-'][0]].audio_files) > 2000:
                    g.window['-STATUS-'].Update(f"{values['-TREE-'][0]} has to many items to display at once.")
                else:
                    g.window['-STATUS-'].Update(f"Loading {values['-TREE-'][0]}...")
                    g.tableData = sfe.handleTreeEvent(values, sfe)    
                    g.window['-TABLE-'].Update(values=g.tableData)
                    table_update = True
                    g.window['-STATUS-'].Update(f"Showing results from {values['-TREE-'][0]}.")
                ignore = False    
            #get specific error message
            except KeyError:
                #print the specific value that caused the error
                print(f"KeyError: {values['-TREE-'][0]}")
            except IndexError:
                sg.popup_error(f"IndexError: {values['-TREE-'][0]}")
            except Exception as e:
                sg.popup_error(f"Failed to update table: {e}")
        
        if '-TABLE-' in event and not ignore:
            try:
                # Check if the index exists in g.tableData
                if values["-TABLE-"][0] < len(g.tableData):
                    lyst = g.tableData[values["-TABLE-"][0]]
                    file = sfe.fileCache.get(''.join(map(str, lyst[3:])), None)
                    if not file:
                        print(f"File not found in cache: {lyst[3:]}")
                    else:
                        path = file[0].path
                        g.window['-OPEN-'].Update(visible=True)
                        g.window['-OPEN-'].Update()
                        g.window['-STATUS-'].Update(f"Selected: {os.path.basename(path)}")
                        audio = pg.mixer.Sound(path)
                        channel = pg.mixer.Channel(1)
                        
                        if event == '-OPEN-':

                        # Open the directory containing the selected file
                            if sys.platform == "win32":
                                os.startfile(os.path.dirname(path))
                            else:
                                opener = "open" if sys.platform == "darwin" else "xdg-open"
                                subprocess.call([opener, os.path.dirname(path)])
                else:
                    print(f"Index {values['-TABLE-'][0]} does not exist in g.tableData.")
            except Exception as e:
                sg.window['-STATUS-'].Update(f"Failed to find {os.path.basename(path)}: {e}")

        if event == "-PLAY-" and audio and not ignore:
            try:
                if is_playing:
                    channel.stop()
                    g.window['-STATUS-'].Update(f"Paused {os.path.basename(path)}")
                    is_playing = False
                    ignore = False
                    continue
                else:
                    if not path:
                        print("No file selected.")
                        continue
                    g.window['-STATUS-'].Update(f"Playing {os.path.basename(path)}")  
                    is_playing = True
                    channel.play(audio) 
                    ignore = False
            except Exception as e:
                sg.popup_error(f"Failed to play {os.path.basename(path)}: {e}")
                print(f"Exception type: {type(e)}")
                print(f"Exception args: {e.args}")
                print(f"Path: {path}")
                print(f"Audio: {audio}")
        
        if event == "-STOP-":
            g.window['-STATUS-'].Update(f"Stopped {os.path.basename(path)}")  
            is_playing = False
            channel.stop()
            ignore = False
            
        if event == '-VOLUME-':
            volume = values['-VOLUME-'] / 100
            channel.set_volume(volume)
            ignore = False
            
        #Update file lengths in table
        while table_update and not file_queue.empty():
            ignore = True
            g.window['-STATUS-'].Update(f"Updating table... please wait. (You won't have to wait next time you load this directory.)")
            try:
                path, length = file_queue.get_nowait()
                for file in sfe.fileCache[path]:
                    file.length = length
                    g.tableData[file.index][2] = file.length
                    g.window['-TABLE-'].Update(values=g.tableData)
                    g.window.Read(timeout=0)  # Force the window to refresh
            except Exception as e:
                sg.popup_error(f"Failed to update table: {e}")

        
        if table_update:
            g.window['-STATUS-'].Update(f"Table updated.")
            table_update = False
            ignore = False
                
    print(os.path.basename(__file__))
                

    g.window.close()
    sfe.saveState()


if __name__ == '__main__':
    main()
