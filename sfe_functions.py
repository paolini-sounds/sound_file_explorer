import PySimpleGUI as sg
import os
from sfe_classes import Directory


def addDir(directory_path, sfe, g):
    try:
        newDirectory = Directory(directory_path)            
        sfe.addDirectory(newDirectory)
        newDirectory.toTreeData(g)
        g.window['-TREE-'].Update(g.treeData)
        return f"Added {directory_path} to the library."
    except Exception as e:
        # Log the exception details for debugging
        print(f"Exception type: {type(e)}")
        print(f"Exception args: {e.args}")
        return f"Failed to add {directory_path} to the library."

#Update tree with directories 
def updateTree(sfe, g):
    for directory in sfe.directory_map.values():
        #if directory is at the root, add it to the tree
        if directory.parent == '':
            directory.toTreeData(g)
    g.window['-TREE-'].Update(g.treeData) 

    
def deleteTreeItem(sfe, g, values):
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


def search(sfe, g, file_queue, values):
    sfe.table_update = True
    file_queue.queue.clear()
    g.window['-STATUS-'].Update(f"Searching for {values['-TERM-']}...")
    sfe.search(values)
    g.window['-TERM-'].Update('')
    g.tableData = sfe.updateAudioTable(values)
    g.window['-TABLE-'].Update(values=g.tableData)
    sfe.table_update = True
    g.window['-STATUS-'].Update(f"Showing {sfe.matches} matches for {values['-TERM-']} out of {sfe.records} records.")

def treeEvent(sfe, g, values, ignore):
    try:
        print("Selected: ", values["-TREE-"][0])
        if len(sfe.directory_map[values['-TREE-'][0]].audio_files) > 2000:
            g.window['-STATUS-'].Update(f"{values['-TREE-'][0]} has to many items to display at once.")
        else:
            g.window['-STATUS-'].Update(f"Loading {values['-TREE-'][0]}...")
            g.tableData = sfe.handleTreeEvent(values)    
            g.window['-TABLE-'].Update(values=g.tableData)
            g.window['-STATUS-'].Update(f"Showing results from {values['-TREE-'][0]}.")
            return True
        
    except KeyError:
        #print the specific value that caused the error
        print(f"KeyError: {values['-TREE-'][0]}")
    except IndexError:
        sg.popup_error(f"IndexError: {values['-TREE-'][0]}")
    except Exception as e:
        sg.popup_error(f"Failed to update table: {e}")
    finally:
        return True
    
def play(sfe, g, values, channel, audio, path):
    print("path: ", path, "channel: ", channel, "audio: ", audio)
    if channel and not channel.get_busy():
        g.window['-STATUS-'].Update(f"Stopped {os.path.basename(path)}")
    if not path or not os.path.exists(path):
        print("No file selected or file does not exist.")
        return
    g.window['-STATUS-'].Update(f"Playing {os.path.basename(path)}")  
    channel.play(audio) 