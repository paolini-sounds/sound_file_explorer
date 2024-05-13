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

from sfe_classes import *


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
            try:    
                if not values['-TREE-']:
                    g.window['-STATUS-'].Update(f"Please select a directory to delete.")         
                else:
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
            except Exception as e:
                sg.popup_error(f"Failed to delete directory: {e}")
                ignore = False
            
        if event == "-SEARCH-" and values["-TERM-"] != "" and not ignore:
            sfe.table_update = True
            ignore = True
            file_queue.queue.clear()
            g.window['-STATUS-'].Update(f"Searching for {values['-TERM-']}...")
            sfe.search(values)
            g.window['-TERM-'].Update('')
            g.tableData = sfe.updateAudioTable(values)
            g.window['-TABLE-'].Update(values=g.tableData)
            sfe.table_update = True
            g.window['-STATUS-'].Update(f"Showing {sfe.matches} matches for {values['-TERM-']} out of {sfe.records} records.")
            ignore = False
                        
        if event == "-TREE-" and values["-TREE-"] and not ignore:
            ignore = True
            sfe.table_update = True
            file_queue.queue.clear()
            try:
                print("Selected: ", values["-TREE-"][0])
                if len(sfe.directory_map[values['-TREE-'][0]].audio_files) > 2000:
                    g.window['-STATUS-'].Update(f"{values['-TREE-'][0]} has to many items to display at once.")
                else:
                    g.window['-STATUS-'].Update(f"Loading {values['-TREE-'][0]}...")
                    g.tableData = sfe.handleTreeEvent(values)    
                    g.window['-TABLE-'].Update(values=g.tableData)
                    g.window['-STATUS-'].Update(f"Showing results from {values['-TREE-'][0]}.")
 
            #get specific error message
            except KeyError:
                #print the specific value that caused the error
                print(f"KeyError: {values['-TREE-'][0]}")
            except IndexError:
                sg.popup_error(f"IndexError: {values['-TREE-'][0]}")
            except Exception as e:
                sg.popup_error(f"Failed to update table: {e}")
            finally:
                ignore = False
        
        if '-TABLE-' in event and not ignore:
            try:
                # Check if the index exists in g.tableData
                if values["-TABLE-"][0] < len(g.tableData):
                    lyst = g.tableData[values["-TABLE-"][0]]
                    file = sfe.fileCache.get(''.join(map(str, lyst[3:])), None)
                    if not file:
                        g.window['-STATUS-'].Update(f"File not found in cache: {lyst[3:]}")
                        print(f"File not found in cache: {lyst[3:]}")
                    else:
                        path = file[0].path
                        g.window['-STATUS-'].Update(f"Selected: {os.path.basename(path)}")
                        audio = pg.mixer.Sound(path)
                        channel = pg.mixer.Channel(1)
                        
                else:
                    print(f"Index {values['-TABLE-'][0]} does not exist in g.tableData.")
            except Exception as e:
                g.window['-STATUS-'].Update(f"Failed to find {os.path.basename(path)}: {e}")

        if event == "-PLAY-" and audio and not ignore:
            try:
                        # check if the audio file finished playing
                if channel and not channel.get_busy():
                    is_playing = False
                    g.window['-STATUS-'].Update(f"Stopped {os.path.basename(path)}")
                if not path:
                    print("No file selected.")
                    continue
                g.window['-STATUS-'].Update(f"Playing {os.path.basename(path)}")  
                is_playing = True
                channel.play(audio) 
            except Exception as e:
                sg.popup_error(f"Failed to play {os.path.basename(path)}: {e}")
                print(f"Exception type: {type(e)}")
                print(f"Exception args: {e.args}")
                print(f"Path: {path}")
                print(f"Audio: {audio}")
         
                
        # Update the lengths of the audio files in the table
        while sfe.table_update and not sfe.file_queue.empty():
            ignore = True
            g.window['-STATUS-'].Update(f"Updating table... please wait. (You won't have to wait next time you load this directory.)")
            try:
                path, length = sfe.file_queue.get_nowait()
                for file in sfe.fileCache[path]:
                    file.length = length
                    g.tableData[file.index][2] = file.length
                    g.window['-TABLE-'].Update(values=g.tableData)
                    g.window.read(timeout=0)
            except Exception as e:
                sg.popup_error(f"Failed to update table: {e}")
                
        
        
        # Periodically update the table GUI with the updated file lengths
        if sfe.table_update:
            g.window['-TABLE-'].Update(values=g.tableData)
            g.window['-STATUS-'].Update(f"Table updated.")
            sfe.table_update = False
            ignore = False 
                
        if event == "-STOP-":
            g.window['-STATUS-'].Update(f"Stopped {os.path.basename(path)}")  
            is_playing = False
            channel.stop()
            
        if event == '-VOLUME-':
            volume = values['-VOLUME-'] / 100
            channel.set_volume(volume)
            

    g.window.close()
    sfe.saveState()


if __name__ == '__main__':
    main()
