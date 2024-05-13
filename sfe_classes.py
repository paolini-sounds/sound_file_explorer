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
                   col0_width=30,
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
            self.length = "unknown"
            
        

class Directory:
    
    FILE_TYPES = ('.mp3', '.wav', '.aiff')
    
    def __init__(self, path):
        self.path = path
        self.subdirectories = {}
        self.name = os.path.basename(path)
        #contains a set of audio file paths (not objects)
        self.audio_files = self.getFiles()
        self.parent = ''

    def getFiles(self):
        self.audio_files = set()
        # Get a list of audio files in the directory       
        notAdded = 0
        for root, dirs, files in os.walk(self.path):

            for file in files:
                file_type = os.path.splitext(file)[-1]

                
                if file_type in Directory.FILE_TYPES:
                    # Create a new File object and add it to self.audio_files
                    self.audio_files.add(os.path.join(root, file))
                    contains_audio = True

            if root != self.path:
                # Create a new Directory object for the current directory
                self.subdirectories[root] = Directory(root)
        
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
        self.table_update = False

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
        try:
            removed = self.directory_map.pop(values['-TREE-'][0], None)
            removed.subdirectories.clear()

            if removed is None:
                sg.popup_error(f"Directory not found: {values['-TREE-'][0]}")
                return

            if removed.parent:
                parent = self.directory_map.get(removed.parent)
                if parent is not None and removed.path in parent.subdirectories:
                    parent.subdirectories.pop(removed.path, None)

            keys_to_remove = [key for key in self.directory_map.keys() if key.startswith(values['-TREE-'][0])]
            for key in keys_to_remove:
                self.directory_map.pop(key, None)  
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
                for file_path in directory.audio_files:
                    self.records += 1
                    if term in os.path.basename(file_path):
                        self.results.append(file_path)
                        self.matches += 1
            print(f"{self.matches} Matches for {term} out of {self.records} records.")
        except Exception as e:
            sg.popup_error(f"Failed to search for {term}: {e}")
            self.results = []
            self.matches = 0
            self.records = 0
    
    # Handles the event when a tree item is selected
    def handleTreeEvent(self, values):
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
                index = 0 #index to keep track of the file
                # Add the audio files to the table
                for file_path in directory.audio_files:
                    #check if already in fileCache
                    if file_path in self.fileCache:
                        for file in self.fileCache[file_path]:
                            file.index = index
                            tableData.append([file.name, file.file_type, file.length, file.path])
                            index += 1
                    else:
                        #load the file into the table
                        file = File(file_path, self.file_queue)
                        file.index = index
                        file.getLength()
                        self.fileCache[file.path] = [file]
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


    def updateAudioTable(self, values):
        try:
            tableData = []
            index = 0
            for file_path in self.results:
                    #check if already in fileCache
                if file_path in self.fileCache:
                    for file in self.fileCache[file.path]:
                        file.index = index
                        tableData.append([file.name, file.file_type, file.length, file.path])
                        index += 1
                else:
                    #load the file into the table
                    file = File(file_path, self.file_queue)
                    file.getLength()
                    file.index = index
                    self.fileCache[file.path] = [file]
                    tableData.append([file.name, file.file_type, file.length, file.path])
                    index += 1
            return tableData
            print(f"{sfe.matches } Matches for {values['-TERM-']} out of {sfe.records} records.")
        except Exception as e:
            sg.popup_error(f"Failed to update table: {e} : {file}")
